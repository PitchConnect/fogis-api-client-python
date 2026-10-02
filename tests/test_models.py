from datetime import date, time

import pytest
from conftest import SCENARIOS, load

from fogis_api_client.enums import EventType, FootballType
from fogis_api_client.models import (
    STOCKHOLM,
    CautionRecord,
    LineupChange,
    LineupEntry,
    Match,
    MatchEvent,
    MatchResult,
    TeamOfficial,
    parse_ms_date,
)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_fixture_record_parses(scenario: str) -> None:
    for d in load(scenario, "matches"):
        assert Match.from_api(d).raw is d
    for d in load(scenario, "events"):
        MatchEvent.from_api(d)
    for d in load(scenario, "lineups"):
        LineupEntry.from_api(d)
    for d in load(scenario, "officials"):
        TeamOfficial.from_api(d)


def test_every_event_type_in_history_is_known() -> None:
    unknown = {d["matchhandelsetypid"] for s in SCENARIOS for d in load(s, "events")} - set(EventType)
    assert not unknown


def test_match_fields_and_sentinels() -> None:
    m = Match.from_api(load("12_match_list", "matches")[0])
    assert m.kickoff is not None and m.kickoff.tzinfo == STOCKHOLM
    assert m.date == m.kickoff.date()
    assert m.venue_latitude is None  # double.MinValue sentinel
    assert m.home.match_team_id == m.raw["matchlag1id"]
    assert m.away.name == m.raw["lag2namn"]
    assert m.crew


def test_futsal_shootout_period_matches_the_data() -> None:
    m = Match.from_api(load("06b_penalty_shootout_futsal", "matches")[0])
    assert m.football_type is FootballType.FUTSAL
    assert m.shootout_period == 5
    shootout = [MatchEvent.from_api(d) for d in load("06b_penalty_shootout_futsal", "events")]
    assert {e.period for e in shootout if e.type and e.type.is_shootout} == {5}


def test_protected_identity_is_not_a_name() -> None:
    crew = Match.from_api(load("11_protected_person", "matches")[0]).crew
    protected = [a for a in crew if a.is_protected]
    assert len(protected) == 1
    assert protected[0].name is None


def test_added_time_is_only_in_the_text() -> None:
    events = [MatchEvent.from_api(d) for d in load("07_added_time", "events")]
    added = [e for e in events if e.added_minutes is not None]
    assert [(e.minute, e.period, e.added_minutes) for e in added] == [(90, 2, 6)]


def test_event_sentinels_become_none() -> None:
    control = next(
        MatchEvent.from_api(d) for s in SCENARIOS for d in load(s, "events") if d["matchhandelsetypid"] == 23
    )
    assert control.match_team_id is None
    assert control.player_id is None
    assert control.shirt_number is None
    assert control.related_event_id is None
    assert control.position_x is None


def test_linked_substitution() -> None:
    events = [MatchEvent.from_api(d) for d in load("01_modern_linked_subs", "events")]
    by_id = {e.event_id: e for e in events}
    on = [e for e in events if e.type is EventType.BYTE_IN]
    assert on and all(e.related_event_id is not None for e in on)
    assert all(by_id[e.related_event_id].type is EventType.BYTE_UT for e in on if e.related_event_id)


def test_official_discipline() -> None:
    officials = [TeamOfficial.from_api(d) for d in load("10_official_discipline", "officials")]
    disciplined = {(o.cautioned, o.caution_minute, o.sent_off_major, o.sending_off_minute) for o in officials}
    assert (True, 90, False, None) in disciplined
    assert (False, None, True, 90) in disciplined
    assert (False, None, True, None) in disciplined  # sending-off saved without a minute


def test_unknown_event_type_keeps_raw_id() -> None:
    d = dict(load("01_modern_linked_subs", "events")[0], matchhandelsetypid=999)
    e = MatchEvent.from_api(d)
    assert e.type is None and e.type_id == 999


def test_event_type_classification() -> None:
    assert EventType.NICKMAL.is_goal and EventType.SJALVMAL.is_goal
    assert not EventType.STRAFFAVGORANDE_MAL.is_goal  # shoot-out goals don't count
    assert EventType.LINDRIG_UTVISNING_AVVISNING.is_sending_off
    assert EventType.VARNING.is_caution
    assert EventType.MATCH_SLUT.is_control
    assert len(EventType) == 40


def test_result_and_change_log_rows() -> None:
    r = MatchResult.from_api(
        {
            "matchresultatid": 5,
            "matchid": 1,
            "matchresultattypid": 2,
            "matchresultattypnamn": "Halvtidsresultat",
            "wo": False,
            "ow": False,
            "ww": False,
            "matchlag1mal": 1,
            "matchlag2mal": 0,
        }
    )
    assert (r.type_id, r.home_goals, r.away_goals) == (2, 1, 0)
    c = LineupChange.from_api({"matchlagid": 3, "tidpunkt": "14:32", "beskrivning": "x", "andradav": "y"})
    assert c.at == time(14, 32)


def test_caution_record_label_is_parsed() -> None:
    r = CautionRecord.from_api(
        {"arannullerad": False, "label": "Varning i match 123456789, Lag A IF - Lag B, BK, 2026-05-01"}
    )
    assert (r.match_number, r.date, r.annulled) == ("123456789", date(2026, 5, 1), False)
    odd = CautionRecord.from_api({"arannullerad": True, "label": "något annat"})
    assert (odd.match_number, odd.date, odd.annulled) == (None, None, True)


def test_parse_ms_date() -> None:
    dt = parse_ms_date("/Date(1682069400000)/")
    assert dt is not None and dt.date() == date(2023, 4, 21) and (dt.hour, dt.minute) == (11, 30)
    assert parse_ms_date("") is None
    assert parse_ms_date("2023-04-21") is None
