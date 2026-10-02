from dataclasses import replace
from typing import Any

import pytest
from conftest import load
from test_client import FakeSession

from fogis_api_client import DryRun, FogisClient, FogisWriteCancelled, next_score
from fogis_api_client.enums import EventType, ResultType
from fogis_api_client.models import LineupEntry, Match, MatchEvent, TeamOfficial

MATCH = Match.from_api(load("01_modern_linked_subs", "matches")[0])
LINEUP = [LineupEntry.from_api(d) for d in load("01_modern_linked_subs", "lineups")]
HOME_PLAYER = next(p for p in LINEUP if p.match_team_id == MATCH.home.match_team_id and not p.substitute)
HOME_SUB = next(p for p in LINEUP if p.match_team_id == MATCH.home.match_team_id and p.substitute)


def dry() -> FogisClient:
    return FogisClient(session=FakeSession(), dry_run=True)  # type: ignore[arg-type]


def payload(result: Any) -> dict[str, Any]:
    assert isinstance(result, DryRun)
    return dict(result.payload)


def test_goal_payload_matches_the_app() -> None:
    p = payload(
        dry().save_match_event(
            MATCH,
            EventType.NICKMAL,
            "45+2",
            team_id=MATCH.home.match_team_id,
            player=HOME_PLAYER,
            score=(1, 0),
        )
    )
    assert p == {
        "matchhandelseid": 0,
        "matchid": MATCH.match_id,
        "period": 1,
        "matchminut": 47,
        "sekund": 0,
        "matchhandelsetypid": 39,
        "matchlagid": MATCH.home.match_team_id,
        "spelareid": HOME_PLAYER.player_id,
        "spelareid2": -1,
        "hemmamal": 1,
        "bortamal": 0,
        "planpositionx": "-1",
        "planpositiony": "-1",
        "matchdeltagareid": HOME_PLAYER.participant_id,
        "matchdeltagareid2": -1,
        "fotbollstypId": MATCH.raw["fotbollstypid"],
        "relateradTillMatchhandelseID": 0,
    }


def test_caution_has_no_score_and_no_second_player() -> None:
    p = payload(
        dry().save_match_event(
            MATCH, EventType.VARNING, "60", team_id=MATCH.home.match_team_id, player=HOME_PLAYER
        )
    )
    assert (p["hemmamal"], p["bortamal"], p["spelareid2"], p["matchdeltagareid2"]) == (0, 0, 0, None)


def test_match_event_without_team_or_player() -> None:
    p = payload(dry().save_match_event(MATCH, EventType.HALVLEK_PERIOD_START, "46"))
    assert (p["matchlagid"], p["spelareid"], p["matchdeltagareid"], p["period"]) == (0, 0, None, 2)


def test_goal_needs_a_score_and_substitutions_their_own_method() -> None:
    with pytest.raises(ValueError, match="score"):
        dry().save_match_event(MATCH, EventType.SPELMAL, "10", team_id=MATCH.home.match_team_id)
    with pytest.raises(ValueError, match="substitute"):
        dry().save_match_event(MATCH, EventType.BYTE_IN, "10", team_id=MATCH.home.match_team_id)


def test_substitution_is_one_call_with_the_outgoing_player_second() -> None:
    p = payload(
        dry().substitute(
            MATCH, "70", team_id=MATCH.home.match_team_id, player_in=HOME_SUB, player_out=HOME_PLAYER
        )
    )
    assert p["matchhandelsetypid"] == EventType.BYTE_IN
    assert (p["spelareid"], p["matchdeltagareid"]) == (HOME_SUB.player_id, HOME_SUB.participant_id)
    assert (p["spelareid2"], p["matchdeltagareid2"]) == (HOME_PLAYER.player_id, HOME_PLAYER.participant_id)


def test_other_write_payloads() -> None:
    c = dry()
    assert payload(c.delete_match_event(5)) == {"matchhandelseid": 5}
    assert payload(c.report_match_result(9, {ResultType.SLUTRESULTAT: (2, 1)})) == {
        "matchresultatListaJSON": [
            {
                "matchid": 9,
                "matchresultattypid": 1,
                "matchlag1mal": 2,
                "matchlag2mal": 1,
                "wo": False,
                "ow": False,
                "ww": False,
            }
        ]
    }
    assert payload(c.save_attendance(9, 312)) == {"matchid": 9, "antalaskadare": 312}
    assert payload(c.save_referee_note(9, "Inga noteringar")) == {
        "matchid": 9,
        "noterinfrandomare": "Inga noteringar",
    }


def test_official_discipline_resends_role_and_responsible() -> None:
    official = TeamOfficial.from_api(load("10_official_discipline", "officials")[0])
    clean = replace(official, cautioned=False, sent_off_minor=False, sent_off_major=False)
    p = payload(dry().save_official_discipline(clean, minute=80, caution=True, sending_off="minor"))
    assert p == {
        "matchlagledareid": official.official_id,
        "lagrollid": official.role_id,
        "avvisadmatchminut": 80,
        "avvisadlindrig": True,
        "avvisadgrov": False,
        "varnad": True,
        "ansvarig": official.responsible,
    }


def test_removing_discipline_with_save_is_refused() -> None:
    disciplined = next(
        TeamOfficial.from_api(d)
        for d in load("10_official_discipline", "officials")
        if d["varnad"] or d["avvisadgrov"]
    )
    with pytest.raises(ValueError, match="clear_official_discipline"):
        dry().save_official_discipline(disciplined)


def test_remove_and_add_official_payloads_match_the_app() -> None:
    """As recorded in the app on 2026-09-27."""
    c = dry()
    assert payload(c.remove_team_official(13, 9203412)) == {
        "matchlagid": 13,
        "matchdeltagareAttRaderaListaJSON": [],
        "matchDeltagareAndraErsattareListaJSON": [],
        "matchlagledareAttRaderaListaJSON": [{"matchlagledareid": 9203412}],
        "matchdeltagareAttAndraPositionListaJSON": [],
    }
    assert payload(c.add_team_official(6, 13, 1004869, 3)) == {
        "personid": 1004869,
        "lagrollid": 3,
        "matchid": 6,
        "matchlagid": 13,
    }
    assert c.remove_team_official(13, 1).method == "MatchLaguppställningKlar"


def test_clear_official_discipline_recreates_a_clean_record() -> None:
    from test_verify_runner import fake

    f = fake()
    client = FogisClient(session=f)  # type: ignore[arg-type]
    team = next(iter(f.officials))
    row = next((r for r in f.officials[team] if r["ansvarig"]), f.officials[team][0])
    o = TeamOfficial.from_api(row)

    reply = client.save_official_discipline(o, minute=33, caution=True)
    assert all("personnr" not in r for r in reply)  # stripped from write responses
    cautioned = TeamOfficial.from_api(
        next(r for r in f.officials[team] if r["matchlagledareid"] == o.official_id)
    )
    assert (cautioned.cautioned, cautioned.caution_minute) == (True, 33)

    calls_before = len(f.calls)
    new = client.clear_official_discipline(cautioned)
    assert new.official_id != o.official_id
    assert (new.person_id, new.role_id, new.responsible) == (o.person_id, o.role_id, o.responsible)
    assert not (new.cautioned or new.sent_off)
    expected = ["MatchLaguppställningKlar", "LaggTillMatchlagledare"] + (
        ["SparaMatchlagledare"] if o.responsible else []
    )
    assert [m for m, _ in f.calls[calls_before:]][: len(expected)] == expected


def test_clear_official_discipline_needs_real_answers() -> None:
    disciplined = next(
        TeamOfficial.from_api(d)
        for d in load("10_official_discipline", "officials")
        if d["varnad"] or d["avvisadgrov"]
    )
    with pytest.raises(ValueError, match="dry-run"):
        dry().clear_official_discipline(disciplined)


def test_confirm_callback_can_stop_a_write() -> None:
    session = FakeSession(answers={"RaderaMatchhandelse": None})
    seen = []

    def decline(method: str, p: Any) -> bool:
        seen.append(method)
        return False

    c = FogisClient(session=session, confirm=decline)  # type: ignore[arg-type]
    with pytest.raises(FogisWriteCancelled):
        c.delete_match_event(5)
    assert seen == ["RaderaMatchhandelse"] and session.calls == []

    c.confirm = lambda method, p: True
    c.delete_match_event(5)
    assert session.calls == [("RaderaMatchhandelse", {"matchhandelseid": 5})]


def test_final_methods_cannot_go_through_the_generic_path() -> None:
    with pytest.raises(AssertionError):
        dry()._write("SparaMatchGodkannDomarrapport", {"matchid": 1})


def test_next_score_follows_the_app() -> None:
    events = [MatchEvent.from_api(d) for d in load("01_modern_linked_subs", "events")]
    goals = [e for e in events if e.type and e.type.is_goal]
    home = max(e.home_goals for e in goals)
    away = max(e.away_goals for e in goals)
    assert next_score(events, MATCH, MATCH.away.match_team_id) == (home, away + 1)
    with pytest.raises(ValueError):
        next_score(events, MATCH, 12345)


# ---------------------------------------------------------------- irreversible calls

OPEN = replace(MATCH, report_approved=False, result_is_final=True)


@pytest.mark.parametrize("method", ["mark_reporting_finished", "end_live_reporting"])
def test_irreversible_calls_need_the_match_id_repeated(method: str) -> None:
    with pytest.raises(ValueError, match="cannot be undone"):
        getattr(dry(), method)(OPEN, confirm_match_id=OPEN.match_id + 1)
    with pytest.raises(TypeError):
        getattr(dry(), method)(OPEN)  # no confirm_match_id at all


@pytest.mark.parametrize(
    ("method", "fogis_method"),
    [
        ("mark_reporting_finished", "SparaMatchGodkannDomarrapport"),
        ("end_live_reporting", "SparaMatchAvslutaLiveRapportering"),
    ],
)
def test_irreversible_calls_refuse_a_missing_final_result(method: str, fogis_method: str) -> None:
    no_result = replace(OPEN, result_is_final=False)
    with pytest.raises(ValueError, match="no final result"):
        getattr(dry(), method)(no_result, confirm_match_id=no_result.match_id)
    extra = {"ignore_problems": True} if method == "mark_reporting_finished" else {}
    r = getattr(dry(), method)(
        no_result, confirm_match_id=no_result.match_id, allow_missing_result=True, **extra
    )
    assert r == DryRun(fogis_method, {"matchid": no_result.match_id})


def test_submitting_an_approved_report_is_refused() -> None:
    approved = replace(OPEN, report_approved=True)
    with pytest.raises(ValueError, match="already approved"):
        dry().mark_reporting_finished(approved, confirm_match_id=approved.match_id)


def test_irreversible_calls_still_go_through_confirm() -> None:
    session = FakeSession(answers={"SparaMatchGodkannDomarrapport": {}})
    c = FogisClient(session=session, confirm=lambda method, p: False)  # type: ignore[arg-type]
    with pytest.raises(FogisWriteCancelled):
        c.mark_reporting_finished(OPEN, confirm_match_id=OPEN.match_id, ignore_problems=True)
    assert session.calls == []


# ---------------------------------------------------------------- line-up entries


def test_new_shirt_number_resends_everything_else() -> None:
    p = payload(dry().save_match_participant(HOME_PLAYER, shirt_number=44))
    assert p == {
        "matchdeltagareid": HOME_PLAYER.participant_id,
        "trojnummer": 44,
        "lagdelid": HOME_PLAYER.raw["lagdelid"],
        "lagkapten": HOME_PLAYER.captain,
        "ersattare": HOME_PLAYER.substitute,
        "positionsnummerhv": HOME_PLAYER.raw["positionsnummerhv"],
        "arSpelandeLedare": HOME_PLAYER.playing_official,
        "ansvarig": HOME_PLAYER.responsible,
    }


def test_bench_and_goalkeeper_positions_follow_the_app() -> None:
    to_bench = payload(dry().save_match_participant(HOME_PLAYER, substitute=True))
    assert (to_bench["ersattare"], to_bench["positionsnummerhv"]) == (True, -1)
    keeper = payload(dry().save_match_participant(HOME_PLAYER, goalkeeper=True, substitute=False))
    assert (keeper["lagdelid"], keeper["positionsnummerhv"]) == (1, 1)
    no_number = payload(dry().save_match_participant(replace(HOME_PLAYER, shirt_number=None)))
    assert no_number["trojnummer"] == -1


# ---------------------------------------------------------------- editing a substitution


def test_edit_substitution_matches_the_apps_two_saves() -> None:
    from fogis_api_client.timeline import pair_substitutions

    events = [MatchEvent.from_api(d) for d in load("01_modern_linked_subs", "events")]
    sub = next(s for s in pair_substitutions(events) if s.pairing == "linked")
    assert sub.on is not None and sub.off is not None
    session = FakeSession(answers={"SparaMatchhandelse": []})
    FogisClient(session=session).edit_substitution(MATCH, sub, time="62")  # type: ignore[arg-type]
    (m1, on), (m2, off) = session.calls
    assert (m1, m2) == ("SparaMatchhandelse", "SparaMatchhandelse")
    assert (on["matchhandelseid"], on["matchhandelsetypid"], on["relateradTillMatchhandelseID"]) == (
        sub.on.event_id,
        17,
        sub.off.event_id,
    )
    assert (on["spelareid"], on["matchdeltagareid"], on["spelareid2"], on["matchdeltagareid2"]) == (
        sub.on.player_id,
        sub.on.participant_id,
        0,
        0,
    )
    assert (off["matchhandelseid"], off["matchhandelsetypid"], off["relateradTillMatchhandelseID"]) == (
        sub.off.event_id,
        16,
        0,
    )
    assert (off["spelareid"], off["matchdeltagareid"], off["spelareid2"], off["matchdeltagareid2"]) == (
        0,
        None,
        sub.off.player_id,
        sub.off.participant_id,
    )
    assert on["matchminut"] == off["matchminut"] == 62 and on["period"] == off["period"] == 2


def test_only_linked_substitutions_can_be_edited() -> None:
    from fogis_api_client.timeline import pair_substitutions

    events = [MatchEvent.from_api(d) for d in load("02_unlinked_subs_pre2024", "events")]
    unlinked = next(s for s in pair_substitutions(events) if s.pairing != "linked")
    with pytest.raises(ValueError, match="linked"):
        dry().edit_substitution(MATCH, unlinked, time="50")


@pytest.mark.parametrize("event_type", [1, 7, 2])
def test_dangerous_and_server_made_types_are_always_refused(event_type: int) -> None:
    with pytest.raises(ValueError):
        dry().save_match_event(
            MATCH, event_type, "30", team_id=MATCH.home.match_team_id, player=HOME_PLAYER, allow_untested=True
        )


@pytest.mark.parametrize("event_type", [3, 33])
def test_untested_types_need_an_explicit_opt_in(event_type: int) -> None:
    with pytest.raises(ValueError, match="allow_untested"):
        dry().save_match_event(MATCH, event_type, "30", team_id=MATCH.home.match_team_id, player=HOME_PLAYER)
    sent = dry().save_match_event(
        MATCH, event_type, "30", team_id=MATCH.home.match_team_id, player=HOME_PLAYER, allow_untested=True
    )
    assert sent.payload["matchhandelsetypid"] == event_type
