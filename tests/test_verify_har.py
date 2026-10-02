import json
from pathlib import Path
from typing import Any

from conftest import load

from fogis_api_client import FogisClient
from fogis_api_client.models import LineupEntry, Match, MatchEvent
from tools.verify.har import compare, library_payload, main, read_har

SCENARIO = "01_modern_linked_subs"


def entry(method: str, request: dict[str, Any], d: Any) -> dict[str, Any]:
    return {
        "request": {
            "url": f"https://fogis.svenskfotboll.se/mdk/MatchWebMetoder.aspx/{method}",
            "postData": {"text": json.dumps(request)},
        },
        "response": {"status": 200, "content": {"text": json.dumps({"d": d})}},
    }


def recording(tmp_path: Path, tweak: dict[str, Any] | None = None) -> Path:
    match_raw = load(SCENARIO, "matches")[0]
    lineups = load(SCENARIO, "lineups")
    events = load(SCENARIO, "events")
    match = Match.from_api(match_raw)
    caution = next(MatchEvent.from_api(e) for e in events if e["matchhandelsetypid"] == 20)
    player = next(LineupEntry.from_api(r) for r in lineups if r["matchdeltagareid"] == caution.participant_id)
    sent = FogisClient(session=None, dry_run=True).save_match_event(  # type: ignore[arg-type]
        match, 20, caution.time_text, team_id=caution.match_team_id or 0, player=player
    )
    request = dict(sent.payload) | (tweak or {})
    har = {
        "log": {
            "entries": [
                entry("GetMatcherAttRapportera", {"filter": {}}, {"matchlista": [match_raw]}),
                entry("GetMatchdeltagareListaForMatchlag", {"matchlagid": 1}, lineups),
                entry("SparaMatchhandelse", request, None),
                entry("GetMatchhandelselista", {"matchid": match.match_id}, events),
                {
                    "request": {"url": "https://fogis.svenskfotboll.se/mdk/js/app.min.js"},
                    "response": {"status": 200},
                },
            ]
        }
    }
    path = tmp_path / "rec.har"
    path.write_text(json.dumps(har))
    return path


def test_reads_only_api_calls(tmp_path: Path) -> None:
    calls = read_har(recording(tmp_path))
    assert [c.method for c in calls] == [
        "GetMatcherAttRapportera",
        "GetMatchdeltagareListaForMatchlag",
        "SparaMatchhandelse",
        "GetMatchhandelselista",
    ]


def test_identical_payload_is_recognised(tmp_path: Path) -> None:
    calls = read_har(recording(tmp_path))
    save = calls[2]
    lib = library_payload(save, calls)
    assert isinstance(lib, dict)
    assert compare(save.request, lib) == []


def test_type_difference_is_reported(tmp_path: Path) -> None:
    calls = read_har(recording(tmp_path, {"planpositionx": -1}))
    lib = library_payload(calls[2], calls)
    assert isinstance(lib, dict)
    assert compare(calls[2].request, lib) == ["planpositionx: same value, app sends int, library str"]


def test_cli_prints_summary(tmp_path: Path, capsys: Any) -> None:
    assert main([str(recording(tmp_path)), "--out", str(tmp_path / "out")]) == 0
    out = capsys.readouterr().out
    assert "SparaMatchhandelse" in out and "IDENTICAL" in out
    assert (tmp_path / "out" / "calls.jsonl").exists()
