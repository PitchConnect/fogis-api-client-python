"""The `fogis` command against the fake FOGIS, and its credential lookup against a scripted `security`."""

import io
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from conftest import FIXTURES, load
from fake_fogis import FakeFogis

from fogis_api_client import FogisClient
from fogis_api_client.cli import main
from fogis_api_client.cli.credentials import CredentialsError, find_credentials

SCENARIO = "01_modern_linked_subs"
WRITES = ("Spara", "Radera", "LaggTill", "Klar", "Avsluta", "Skapa")


# ---------------------------------------------------------------- credentials


def security(stdout: str = "", stderr: str = "", code: int = 0) -> Any:
    calls: list[list[str]] = []

    def run(args: list[str]) -> subprocess.CompletedProcess[bytes]:
        calls.append(args)
        return subprocess.CompletedProcess(args, code, stdout.encode(), stderr.encode())

    run.calls = calls  # type: ignore[attr-defined]
    return run


# Output of `security find-generic-password` (attributes trimmed) as recorded on macOS 26.
ITEM_PLAIN = '    "acct"<blob>="Anna Domare"\n    "svce"<blob>="fogis"\n'
ITEM_NON_ASCII = (
    '    "acct"<blob>=0xC385736120C396626572672054657374  "\\303\\205sa \\303\\226berg Test"\n'
    '    "svce"<blob>="fogis"\n'
)


def test_keychain_account_with_a_space_is_the_username() -> None:
    run = security(ITEM_PLAIN)
    creds = find_credentials({}, run)
    assert creds.username == "Anna Domare"
    assert creds.source == "keychain (fogis)"
    assert run.calls == [["find-generic-password", "-s", "fogis"]]  # the secret is not read yet


def test_keychain_account_with_swedish_letters_is_decoded_from_hex() -> None:
    assert find_credentials({}, security(ITEM_NON_ASCII)).username == "Åsa Öberg Test"


@pytest.mark.parametrize(
    ("printed", "password"),
    [
        ('password: "hemligt"', "hemligt"),
        ('password: 0x6CC3B673656E206F7264225C  "l\\303\\266sen ord"\\134"', 'lösen ord"\\'),
    ],
)
def test_keychain_password_is_read_with_g_and_decoded(printed: str, password: str) -> None:
    run = security(ITEM_PLAIN, stderr=printed + "\n")
    creds = find_credentials({}, run)
    assert creds.password() == password
    assert run.calls[-1] == ["find-generic-password", "-s", "fogis", "-a", "Anna Domare", "-g"]


def test_fogis_username_picks_the_keychain_account_and_service_can_be_changed() -> None:
    run = security(ITEM_PLAIN)
    find_credentials({"FOGIS_USERNAME": "Anna Domare", "FOGIS_KEYCHAIN_SERVICE": "fogis-test"}, run)
    assert run.calls == [["find-generic-password", "-s", "fogis-test", "-a", "Anna Domare"]]


def test_environment_password_wins_over_the_keychain() -> None:
    run = security(ITEM_PLAIN)
    creds = find_credentials({"FOGIS_USERNAME": "Bo Ek", "FOGIS_PASSWORD": "pw"}, run)
    assert (creds.username, creds.password(), creds.source) == ("Bo Ek", "pw", "environment")
    assert run.calls == []


def test_environment_password_needs_a_username() -> None:
    with pytest.raises(CredentialsError, match="FOGIS_USERNAME"):
        find_credentials({"FOGIS_PASSWORD": "pw"}, security())


def test_missing_keychain_item_explains_how_to_add_one() -> None:
    with pytest.raises(CredentialsError, match="security add-generic-password -s fogis"):
        find_credentials({}, security(code=44))


def test_unexpected_password_output_is_not_echoed() -> None:
    creds = find_credentials({}, security(ITEM_PLAIN, stderr="password: secret-ish\n"))
    with pytest.raises(CredentialsError) as e:
        creds.password()
    assert "secret" not in str(e.value)


# ---------------------------------------------------------------- commands


def per_team(kind: str) -> dict[int, list[dict[str, Any]]]:
    return {
        int(p.stem.split("_")[1]): json.loads(p.read_text(encoding="utf-8"))
        for p in (FIXTURES / SCENARIO / kind).glob("*.json")
    }


def fake(**match_overrides: Any) -> FakeFogis:
    match = {**load(SCENARIO, "matches")[0], **match_overrides}
    return FakeFogis(match, load(SCENARIO, "events"), per_team("lineups"), per_team("officials"))


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    return {"FOGIS_CACHE_DIR": str(tmp_path / "cache"), "FOGIS_CONFIG_DIR": str(tmp_path / "config")}


def fogis(f: FakeFogis, env: dict[str, str], *argv: str) -> Any:
    out = io.StringIO()
    assert main(list(argv), env, client=FogisClient(session=f), out=out) == 0  # type: ignore[arg-type]
    text = out.getvalue()
    return text if "--table" in argv else json.loads(text)


def test_matches_lists_the_referees_matches_as_json(env: dict[str, str]) -> None:
    f = fake()
    got = fogis(f, env, "matches", "--from", "2026-07-01", "--to", "2026-07-31")
    assert [m["match_id"] for m in got] == [91000010]
    assert got[0]["date"] == "2026-07-06"
    assert {"home", "away", "kickoff", "crew", "shootout_period"} <= got[0].keys()
    assert "raw" not in got[0]


def test_raw_gives_the_fogis_records(env: dict[str, str]) -> None:
    got = fogis(fake(), env, "matches", "--season", "2026", "--raw")
    assert got[0]["matchid"] == 91000010


def test_table_is_readable(env: dict[str, str]) -> None:
    text = fogis(fake(), env, "matches", "--season", "2026", "--table")
    assert text.splitlines()[0].split() == ["date", "time", "id", "match", "score", "report", "competition"]
    assert "91000010" in text


def test_a_listed_match_is_found_again_by_its_date(env: dict[str, str]) -> None:
    f = fake(matchrapportgodkandavdomare=False)
    fogis(f, env, "matches", "--season", "2026")
    f.calls.clear()
    fogis(f, env, "match", "91000010")
    ranges = [(c[1]["filter"]["datumFran"], c[1]["filter"]["datumTill"]) for c in f.calls]
    assert ranges == [("2026-07-06", "2026-07-06")]


def test_bundle_has_everything_and_an_approved_report_is_cached(env: dict[str, str]) -> None:
    f = fake(matchrapportgodkandavdomare=True)
    bundle = fogis(f, env, "bundle", "91000010", "--date", "2026-07-06")
    assert bundle["bundle_version"] == 1
    assert bundle["match"]["match_id"] == 91000010
    assert set(bundle["lineups"]) == set(bundle["officials"]) == {"home", "away"}
    assert bundle["events"] and bundle["timeline"] and bundle["substitutions"]
    assert all(s["pairing"] == "linked" for s in bundle["substitutions"])
    assert isinstance(bundle["problems"], list)
    assert not any(c[0].startswith(WRITES) for c in f.calls)

    f.calls.clear()
    again = fogis(f, env, "bundle", "91000010")
    assert f.calls == []  # served from the cache
    assert again["cached_at"] is not None
    assert {k: v for k, v in again.items() if k != "cached_at"} == {
        k: v for k, v in bundle.items() if k != "cached_at"
    }

    fogis(f, env, "timeline", "91000010", "--refresh", "--date", "2026-07-06")
    assert f.calls  # --refresh goes back to FOGIS


def test_an_open_report_is_fetched_only_as_needed_and_not_cached(env: dict[str, str], tmp_path: Path) -> None:
    f = fake(matchrapportgodkandavdomare=False)
    fogis(f, env, "events", "91000010", "--date", "2026-07-06")
    assert [c[0] for c in f.calls] == ["GetMatcherAttRapportera", "GetMatchhandelselista"]
    assert not (tmp_path / "cache" / "matches").exists()


def test_timeline_puts_goals_with_their_running_score(env: dict[str, str]) -> None:
    timeline = fogis(fake(), env, "timeline", "91000010", "--date", "2026-07-06")
    goals = [e for e in timeline if e["score"] is not None]
    assert goals and all("event" not in e["score"] for e in goals)  # not repeated inside the score
    assert [e["kind"] for e in timeline].count("event") == len(load(SCENARIO, "events"))


def test_one_team_only(env: dict[str, str]) -> None:
    f = fake()
    lineup = fogis(f, env, "lineup", "91000010", "--date", "2026-07-06", "--team", "home")
    home = f.match["matchlag1id"]
    assert lineup and {p["match_team_id"] for p in lineup} == {home}


def test_unknown_match_is_an_error_not_a_crash(
    env: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["match", "1", "--date", "2026-07-06"], env, client=FogisClient(session=fake()))  # type: ignore[arg-type]
    assert code == 2
    assert "Match 1 is not among your matches on 2026-07-06" in capsys.readouterr().err


def test_cache_list_and_clear(env: dict[str, str]) -> None:
    f = fake(matchrapportgodkandavdomare=True)
    fogis(f, env, "check", "91000010", "--date", "2026-07-06")
    assert [e["match"]["match_id"] for e in fogis(f, env, "cache")] == [91000010]
    fogis(f, env, "cache", "clear")
    assert fogis(f, env, "cache") == []
