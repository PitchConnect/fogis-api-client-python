"""The verification runner against the fake FOGIS, seeded with a real (anonymized) match."""

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from conftest import FIXTURES, load
from fake_fogis import FakeFogis

from fogis_api_client.models import Match
from tools.verify.runner import STEPS, SafeClient, run
from tools.verify.state import MatchState, differences

SCENARIO = "01_modern_linked_subs"


def per_team(kind: str) -> dict[int, list[dict[str, Any]]]:
    out = {}
    for path in (FIXTURES / SCENARIO / kind).glob("*.json"):
        out[int(path.stem.split("_")[1])] = json.loads(path.read_text(encoding="utf-8"))
    return out


def fake(**match_overrides: Any) -> FakeFogis:
    match = dict(
        load(SCENARIO, "matches")[0], matchrapportgodkandavdomare=False, liverapporteringAvslutad=False
    )
    match.update(match_overrides)
    results = [
        {
            "matchresultatid": 1,
            "matchid": match["matchid"],
            "matchresultattypid": t,
            "matchresultattypnamn": "",
            "matchlag1mal": h,
            "matchlag2mal": a,
            "wo": False,
            "ow": False,
            "ww": False,
        }
        for t, h, a in ((1, match["matchlag1mal"], match["matchlag2mal"]), (2, 0, 0))
    ]
    return FakeFogis(match, load(SCENARIO, "events"), per_team("lineups"), per_team("officials"), results)


def go(f: FakeFogis, out: Path, **kwargs: Any) -> dict[str, Any]:
    m = Match.from_api(f.match)
    assert m.kickoff is not None and m.date is not None
    client = SafeClient(session=f)  # type: ignore[arg-type]
    return run(client, m.match_id, m.date, out, now=m.kickoff + timedelta(hours=3), **kwargs)


def test_full_run_leaves_the_match_as_it_was(tmp_path: Path) -> None:
    f = fake()
    original = [dict(e) for e in f.events]
    summary = go(f, tmp_path)

    assert summary["aborted"] is None
    assert all(s["ok"] for s in summary["steps"].values()), summary["steps"]
    assert all("left_behind" not in s for s in summary["steps"].values())
    assert summary["final_differences"] == []
    assert summary["rebuild"]["differences"] == []
    assert summary["rebuild"]["not_recreated"] == []
    assert len(f.events) == len(original)
    assert {"before.json", "after.json", "findings.json", "responses.jsonl", "report.md"} <= {
        p.name for p in tmp_path.iterdir()
    }
    assert "identical to the snapshot" in (tmp_path / "report.md").read_text()


def test_never_calls_irreversible_methods(tmp_path: Path) -> None:
    f = fake()
    go(f, tmp_path)
    called = {m for m, _ in f.calls}
    assert not called & {
        "SparaMatchGodkannDomarrapport",
        "SparaMatchAvslutaLiveRapportering",
        "SkjutUppMatch",
    }


def test_findings_answer_the_checklist_questions(tmp_path: Path) -> None:
    steps = go(fake(), tmp_path, rebuild_report=False)["steps"]
    second = steps["second_caution"]["findings"]
    assert [e["type"] for e in second["after_two_cautions"]] == [20, 20, 2]
    assert [e["type"] for e in second["after_deleting_second"]] == [20, 2]  # fake keeps the #2, like FOGIS
    assert set(steps["added_time"]["findings"]) == {"45+2", "47", "45", "90+3", "91"}
    assert steps["official_discipline"]["findings"]["cleared"]["varnad"] is False


def test_a_step_that_leaves_data_behind_is_restored(tmp_path: Path) -> None:
    def leaves_a_caution(ctx: Any) -> dict[str, Any]:
        from tools.verify.runner import quiet_players

        a, _, _ = quiet_players(ctx)
        ctx.client.save_match_event(ctx.match, 20, "10", team_id=ctx.match.home.match_team_id, player=a)
        raise RuntimeError("step blew up halfway")

    summary = go(fake(), tmp_path, steps=[leaves_a_caution], rebuild_report=False)
    step = summary["steps"]["leaves_a_caution"]
    assert step["ok"] is False and "blew up" in step["error"]
    assert step["left_behind"] and step["restored"] is True
    assert summary["final_differences"] == []


def test_failed_restore_aborts_everything(tmp_path: Path) -> None:
    f = fake()

    def break_deletes(ctx: Any) -> dict[str, Any]:
        from tools.verify.runner import quiet_players

        a, _, _ = quiet_players(ctx)
        ctx.client.save_match_event(ctx.match, 20, "10", team_id=ctx.match.home.match_team_id, player=a)
        f.fail_on = "RaderaMatchhandelse"
        return {}

    summary = go(f, tmp_path, steps=[break_deletes, *STEPS])
    assert summary["aborted"]
    assert list(summary["steps"]) == ["break_deletes"]  # nothing ran after the failure
    assert summary["final_differences"]  # reported, for the referee to fix in the app
    assert "DIFFERS" in (tmp_path / "report.md").read_text()


@pytest.mark.parametrize(
    "override", [{"matchrapportgodkandavdomare": True}, {"liverapporteringAvslutad": True}]
)
def test_refuses_a_closed_report(tmp_path: Path, override: dict[str, Any]) -> None:
    f = fake(**override)
    summary = go(f, tmp_path)
    assert "submitted" in summary["aborted"]
    assert not [m for m, _ in f.calls if not m.startswith("Get")]  # not a single write


def test_differences_ignore_ids_after_a_rebuild(tmp_path: Path) -> None:
    a = MatchState(
        match={}, events=[{"matchhandelseid": 1, "matchhandelsetypid": 20, "tidsangivelse": "5"}], results=[]
    )
    b = MatchState(
        match={}, events=[{"matchhandelseid": 9, "matchhandelsetypid": 20, "tidsangivelse": "5"}], results=[]
    )
    assert differences(a, b, compare_event_ids=False) == []
    assert differences(a, b)
