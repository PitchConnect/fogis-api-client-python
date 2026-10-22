from dataclasses import replace

import pytest
from conftest import SCENARIOS, load

from fogis_api_client.enums import EventType
from fogis_api_client.matchtime import MatchTime, encode_match_time
from fogis_api_client.models import Match, MatchEvent

BASE = Match.from_api(load("12_match_list", "matches")[0])
FOOTBALL = replace(
    BASE, halves=2, half_length=45, extra_periods=0, extra_period_length=0, high_resolution_time=False
)
CUP = replace(FOOTBALL, extra_periods=2, extra_period_length=15)
FUTSAL_HIGH_RES = replace(FOOTBALL, half_length=20, high_resolution_time=True)

GOAL = EventType.SPELMAL


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("23", (1, 23, 0)),
        ("45", (1, 45, 0)),
        ("46", (2, 46, 0)),
        ("45+2", (1, 47, 0)),
        ("90+5", (2, 95, 0)),  # FOGIS stores minute 90 + text "90+5"
        ("91", (0, 91, 0)),  # past the last period: this is how period-0 events arise
        ("", (0, 0, 0)),
        (" 7 ", (1, 7, 0)),
    ],
)
def test_regular_match(text: str, expected: tuple[int, int, int]) -> None:
    assert encode_match_time(text, FOOTBALL, GOAL) == MatchTime(*expected)


def test_extra_time_periods() -> None:
    assert encode_match_time("91", CUP, GOAL) == MatchTime(3, 91, 0)
    assert encode_match_time("106", CUP, GOAL) == MatchTime(4, 106, 0)
    assert encode_match_time("121", CUP, GOAL) == MatchTime(0, 121, 0)


@pytest.mark.parametrize("sub", [EventType.BYTE_IN, EventType.BYTE_UT])
@pytest.mark.parametrize(
    ("match", "text", "period"),
    [
        (FOOTBALL, "45", 1),
        (FOOTBALL, "46", 2),
        (FOOTBALL, "90", 2),
        (CUP, "90", 2),
        (CUP, "91", 3),
        (CUP, "105", 3),
        (CUP, "106", 4),
        (CUP, "120", 4),
    ],
)
def test_whole_minute_substitution_at_period_end_stays_in_its_period(
    match: Match, text: str, period: int, sub: EventType
) -> None:
    """A deliberate departure from the app, which would put "45" in period 2 (owner, 2026-10-22)."""
    assert encode_match_time(text, match, sub) == MatchTime(period, int(text), 0)


def test_other_events_at_period_end_unchanged() -> None:
    assert encode_match_time("45", FOOTBALL, GOAL).period == 1
    assert encode_match_time("45", FOOTBALL, EventType.VARNING).period == 1
    assert encode_match_time("45+2", FOOTBALL, EventType.BYTE_IN) == MatchTime(1, 47, 0)


def test_high_resolution_substitution_at_period_end_belongs_to_the_next_period() -> None:
    assert encode_match_time("20:00", FUTSAL_HIGH_RES, EventType.BYTE_IN) == MatchTime(2, 20, 0)
    assert encode_match_time("19:59", FUTSAL_HIGH_RES, EventType.BYTE_UT) == MatchTime(1, 19, 59)
    assert encode_match_time("21", FUTSAL_HIGH_RES, EventType.BYTE_IN) == MatchTime(2, 20, 0)
    assert encode_match_time("20", FUTSAL_HIGH_RES, EventType.BYTE_IN) == MatchTime(2, 19, 0)  # app quirk


def test_period_start_at_period_end_starts_the_next_period() -> None:
    assert encode_match_time("45", FOOTBALL, EventType.HALVLEK_PERIOD_START).period == 2


def test_shootout_kicks_go_to_the_shootout_period() -> None:
    for text in ("0", ""):
        assert encode_match_time(text, CUP, EventType.STRAFFAVGORANDE_MAL).period == 5
    assert encode_match_time("0", FOOTBALL, EventType.STRAFFAVGORANDE_MISS).period == 3


def test_high_resolution_whole_minute_means_its_start() -> None:
    assert encode_match_time("12", FUTSAL_HIGH_RES, GOAL) == MatchTime(1, 11, 0)
    assert encode_match_time("12:30", FUTSAL_HIGH_RES, GOAL) == MatchTime(1, 12, 30)
    assert encode_match_time("20+2", FUTSAL_HIGH_RES, GOAL) == MatchTime(1, 21, 0)
    assert encode_match_time("12", FUTSAL_HIGH_RES, None) == MatchTime(1, 12, 0)  # no type: no adjustment


def test_not_a_time() -> None:
    with pytest.raises(ValueError):
        encode_match_time("abc", FOOTBALL, GOAL)


def test_reproduces_stored_periods_of_modern_fixtures() -> None:
    """For events saved with today's app, re-encoding the displayed time gives back the stored period."""
    checked = 0
    for scenario in SCENARIOS:
        matches = {m["matchid"]: Match.from_api(m) for m in load(scenario, "matches")}
        for d in load(scenario, "events"):
            e = MatchEvent.from_api(d)
            m = matches.get(e.match_id)
            if m is None or m.kickoff is None or m.kickoff.year < 2024 or e.period == 0 or e.type is None:
                continue
            if e.type.is_control:
                continue
            assert encode_match_time(e.time_text, m, e.type_id).period == e.period, (scenario, e.time_text)
            checked += 1
    assert checked > 20
