import math
from dataclasses import replace

import pytest
from conftest import SCENARIOS, load

from fogis_api_client.enums import EventType
from fogis_api_client.models import Match, MatchEvent, TeamOfficial
from fogis_api_client.timeline import (
    build_timeline,
    classify_second_caution_sending_offs,
    effective_period,
    last_period_played,
    pair_substitutions,
    penalty_awards,
    period_for_minute,
    running_score,
    shootout_score,
)

WITH_EVENTS = [s for s in SCENARIOS if load(s, "events")]


def scenario(name: str) -> tuple[Match, list[MatchEvent], list[TeamOfficial]]:
    (match,) = (Match.from_api(d) for d in load(name, "matches"))
    events = [MatchEvent.from_api(d) for d in load(name, "events")]
    officials = [TeamOfficial.from_api(d) for d in load(name, "officials")]
    return match, events, officials


def by_id(events: list[MatchEvent]) -> dict[int, MatchEvent]:
    return {e.event_id: e for e in events}


def of_type(events: list[MatchEvent], t: EventType) -> list[MatchEvent]:
    return sorted((e for e in events if e.type is t), key=lambda e: e.event_id)


# ---------------------------------------------------------------------------- periods


@pytest.mark.parametrize("name", WITH_EVENTS)
def test_inferred_period_agrees_with_every_stored_period(name: str) -> None:
    match, events, _ = scenario(name)
    last = last_period_played(match, events)
    for e in events:
        if e.period == 0 or (e.type is not None and e.type.is_control):
            continue
        assert effective_period(replace(e, period=0), match, last_period=last) == e.period, e.event_id


def test_stored_period_wins() -> None:
    match, events, _ = scenario("01_modern_linked_subs")
    assert all(effective_period(e, match) == e.period for e in events)


def test_old_match_without_periods() -> None:
    match, events, _ = scenario("08a_period0_old")
    assert last_period_played(match, events) is None
    assert {e.minute: effective_period(e, match) for e in events} == {
        3: 1, 30: 1, 39: 1, 46: 2, 51: 2, 75: 2, 76: 2, 78: 2
    }  # fmt: skip


def test_futsal_period0_uses_20_minute_halves() -> None:
    match, events, _ = scenario("09b_futsal_save_order_score")
    periods = {e.minute: effective_period(e, match) for e in events}
    assert (periods[3], periods[20], periods[21], periods[35]) == (1, 1, 2, 2)


def test_overflow_minute_belongs_to_the_last_period() -> None:
    match, events, _ = scenario("08c_period0_overflow_minute")
    overflow = [e for e in events if e.minute == 91]
    assert overflow and all(e.period == 0 and effective_period(e, match) == 2 for e in overflow)
    assert period_for_minute(200, match) == 2


def test_empty_minute_is_unknown() -> None:
    match, events, _ = scenario("08b_period0_empty_minute")
    empty = [e for e in events if e.minute == 0]
    assert len(empty) == 2 and all(effective_period(e, match) is None for e in empty)


def test_no_half_length_means_no_guess() -> None:
    match, events, _ = scenario("08a_period0_old")
    for broken in (replace(match, half_length=0), replace(match, halves=0)):
        assert all(effective_period(e, broken) is None for e in events)


@pytest.mark.parametrize(
    ("name", "period"), [("06a_penalty_shootout_football", 3), ("06b_penalty_shootout_futsal", 5)]
)
def test_shootout_without_period_gets_the_shootout_period(name: str, period: int) -> None:
    match, events, _ = scenario(name)
    kicks = [e for e in events if e.type is not None and e.type.is_shootout]
    assert kicks and all(effective_period(replace(e, period=0), match) == period for e in kicks)


def test_futsal_extra_time() -> None:
    match, events, _ = scenario("06b_penalty_shootout_futsal")
    assert last_period_played(match, events) == 4  # the period-5 control event is ignored
    assert [period_for_minute(m, match) for m in (20, 21, 40, 41, 45, 46, 50, 51)] == [1, 2, 2, 3, 3, 4, 4, 4]


def test_extra_time_allowed_but_not_played() -> None:
    cup = next(m for m in (Match.from_api(d) for d in load("12_match_list", "matches")) if m.extra_periods)
    assert (cup.halves, cup.half_length, cup.extra_periods, cup.extra_period_length) == (2, 45, 2, 15)
    assert period_for_minute(91, cup) == 3  # no evidence: every configured period counts
    assert period_for_minute(91, cup, last_period=2) == 2  # "91" typed for 90+1
    assert [period_for_minute(m, cup, last_period=4) for m in (100, 105, 106, 120, 125)] == [3, 3, 4, 4, 4]
    assert period_for_minute(100, replace(cup, extra_period_length=0), last_period=3) is None
    assert period_for_minute(0, cup) is None and period_for_minute(None, cup) is None


# ---------------------------------------------------------------------------- substitutions


@pytest.mark.parametrize("name", WITH_EVENTS)
def test_every_substitution_event_is_paired_once_within_its_team(name: str) -> None:
    _, events, _ = scenario(name)
    subs = pair_substitutions(events)
    used = [e.event_id for s in subs for e in (s.off, s.on) if e is not None]
    assert sorted(used) == sorted(e.event_id for e in events if e.type is not None and e.type.is_substitution)
    for s in subs:
        assert s.off is not None and s.on is not None, "fixtures have no unmatched substitutions"
        assert s.off.type is EventType.BYTE_UT and s.on.type is EventType.BYTE_IN
        assert s.off.match_team_id == s.on.match_team_id == s.match_team_id


def test_linked_substitutions() -> None:
    _, events, _ = scenario("01_modern_linked_subs")
    subs = pair_substitutions(events)
    assert len(subs) == 5 and {s.pairing for s in subs} == {"linked"}
    assert all(
        s.on is not None and s.off is not None and s.on.related_event_id == s.off.event_id for s in subs
    )


@pytest.mark.parametrize("name", ["02_unlinked_subs_pre2024", "05_penalty_pair", "11_protected_person"])
def test_unlinked_substitutions_are_inferred(name: str) -> None:
    _, events, _ = scenario(name)
    subs = pair_substitutions(events)
    assert subs and {s.pairing for s in subs} == {"inferred"}
    # In these fixtures the app saved "on" then "off" back to back.
    assert all(s.on is not None and s.off is not None and s.off.event_id == s.on.event_id + 1 for s in subs)


def test_same_minute_pairs_follow_event_id_order() -> None:
    _, events, _ = scenario("02_unlinked_subs_pre2024")
    at_62 = [s for s in pair_substitutions(events) if s.on is not None and s.on.minute == 62]
    assert len(at_62) == 2
    assert [(s.on.event_id < s.off.event_id) for s in at_62 if s.on and s.off] == [True, True]


def test_never_pairs_across_teams() -> None:
    match, events, _ = scenario("02_unlinked_subs_pre2024")
    off = of_type(events, EventType.BYTE_UT)[0]
    other = (
        match.away.match_team_id
        if off.match_team_id == match.home.match_team_id
        else match.home.match_team_id
    )
    moved = [replace(e, match_team_id=other) if e is off else e for e in events]
    unmatched = [s for s in pair_substitutions(moved) if s.pairing == "unmatched"]
    assert len(unmatched) == 2
    assert {(s.off is None, s.on is None) for s in unmatched} == {(True, False), (False, True)}


def test_link_to_other_team_is_not_trusted() -> None:
    match, events, _ = scenario("01_modern_linked_subs")
    on = of_type(events, EventType.BYTE_IN)[0]
    moved = [replace(e, match_team_id=match.away.match_team_id + 1) if e is on else e for e in events]
    assert sum(s.pairing == "unmatched" for s in pair_substitutions(moved)) == 2


def test_missing_partner_is_unmatched() -> None:
    _, events, _ = scenario("01_modern_linked_subs")
    first_on = of_type(events, EventType.BYTE_IN)[0]
    subs = pair_substitutions([e for e in events if e is not first_on])
    lonely = [s for s in subs if s.pairing == "unmatched"]
    assert len(lonely) == 1 and lonely[0].on is None and lonely[0].off is not None
    assert lonely[0].off.event_id == first_on.related_event_id


# ---------------------------------------------------------------------------- score


@pytest.mark.parametrize("name", WITH_EVENTS)
def test_final_computed_score_matches_the_approved_result(name: str) -> None:
    match, events, _ = scenario(name)
    assert match.report_approved
    scores = running_score(events, match)
    final = (scores[-1].home, scores[-1].away) if scores else (0, 0)
    shootout = shootout_score(events, match)
    if shootout is None:
        assert final == (match.home_goals, match.away_goals)
    else:
        # The listed result sometimes includes shoot-out goals (06b, 2014) and sometimes not (06a, 2022).
        with_shootout = (final[0] + shootout[0], final[1] + shootout[1])
        assert (match.home_goals, match.away_goals) in (final, with_shootout)


def test_shootout_goals_do_not_count() -> None:
    match, events, _ = scenario("06a_penalty_shootout_football")
    scores = running_score(events, match)
    assert (scores[-1].home, scores[-1].away) == (1, 1) == (match.home_goals, match.away_goals)
    assert shootout_score(events, match) == (6, 5)


def test_futsal_listed_result_includes_the_shootout() -> None:
    match, events, _ = scenario("06b_penalty_shootout_futsal")
    scores = running_score(events, match)
    assert (scores[-1].home, scores[-1].away) == (4, 4)
    assert shootout_score(events, match) == (5, 4)
    assert (match.home_goals, match.away_goals) == (9, 8)


@pytest.mark.parametrize("name", WITH_EVENTS)
def test_only_the_mismatch_fixture_has_typed_score_mismatches(name: str) -> None:
    match, events, _ = scenario(name)
    mismatches = [s for s in running_score(events, match) if s.mismatch]
    assert bool(mismatches) == (name == "09a_typed_score_mismatch")


def test_typed_score_mismatch_is_flagged() -> None:
    match, events, _ = scenario("09a_typed_score_mismatch")
    scores = running_score(events, match)
    assert [(s.home, s.away) for s in scores] == [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 4), (2, 5)]
    (bad,) = [s for s in scores if s.mismatch]
    assert (bad.event.minute, bad.home, bad.away, bad.typed_home, bad.typed_away) == (60, 2, 4, 2, 0)


def test_futsal_save_order_differs_from_timeline_order() -> None:
    match, events, _ = scenario("09b_futsal_save_order_score")
    goals = sorted((e for e in events if e.type is not None and e.type.is_goal), key=lambda e: e.event_id)
    first_saved = goals[0]
    assert first_saved.match_team_id == match.away.match_team_id
    assert (first_saved.home_goals, first_saved.away_goals) == (1, 1)  # typed in match order, not save order
    scores = running_score(events, match)
    assert scores[0].event.minute == 3 and not any(s.mismatch for s in scores)
    assert (scores[-1].home, scores[-1].away) == (8, 1)


def test_own_goal_counts_for_its_match_team() -> None:
    match, events, _ = scenario("01_modern_linked_subs")
    goal = next(e for e in events if e.type is EventType.SPELMAL)
    own = [replace(e, type=EventType.SJALVMAL, type_id=15) if e is goal else e for e in events]
    assert [(s.home, s.away) for s in running_score(own, match)] == [
        (s.home, s.away) for s in running_score(events, match)
    ]


def test_running_score_is_in_timeline_order() -> None:
    match, events, _ = scenario("01_modern_linked_subs")
    assert [s.event.minute for s in running_score(events, match)] == [30, 39, 51]


# ---------------------------------------------------------------------------- server-generated events


def test_automatic_second_caution_sending_offs() -> None:
    _, events, _ = scenario("03_auto_second_caution")
    kinds = classify_second_caution_sending_offs(events)
    assert len(kinds) == 2 and set(kinds.values()) == {"automatic"}
    for event_id in kinds:
        assert by_id(events)[event_id - 1].type is EventType.VARNING  # created right after the 2nd caution


def test_second_caution_across_halves() -> None:
    _, events, _ = scenario("06a_penalty_shootout_football")
    assert list(classify_second_caution_sending_offs(events).values()) == ["automatic"]


def test_orphan_second_caution_sending_off() -> None:
    _, events, _ = scenario("04_orphan_second_caution")
    assert list(classify_second_caution_sending_offs(events).values()) == ["orphan"]


@pytest.mark.parametrize("name", WITH_EVENTS)
def test_only_the_orphan_fixture_has_an_orphan(name: str) -> None:
    _, events, _ = scenario(name)
    orphans = [k for k in classify_second_caution_sending_offs(events).values() if k == "orphan"]
    assert bool(orphans) == (name == "04_orphan_second_caution")


def test_second_caution_falls_back_to_participant_id() -> None:
    _, events, _ = scenario("03_auto_second_caution")
    anonymous = [replace(e, player_id=None) for e in events]
    assert set(classify_second_caution_sending_offs(anonymous).values()) == {"automatic"}
    nobody = [replace(e, player_id=None, participant_id=None) for e in events]
    assert set(classify_second_caution_sending_offs(nobody).values()) == {"orphan"}


def test_caution_entered_after_the_sending_off_does_not_rescue_it() -> None:
    _, events, _ = scenario("04_orphan_second_caution")
    (sending_off,) = of_type(events, EventType.LINDRIG_UTVISNING_AVVISNING)
    caution = next(e for e in events if e.type is EventType.VARNING and e.player_id == sending_off.player_id)
    late = replace(caution, event_id=sending_off.event_id + 100)
    assert list(classify_second_caution_sending_offs([*events, late]).values()) == ["orphan"]


def test_penalty_awards_are_linked() -> None:
    _, events, _ = scenario("05_penalty_pair")
    awards = penalty_awards(events)
    assert [a.pairing for a in awards] == ["linked", "linked"]
    assert {a.outcome.type for a in awards if a.outcome} == {
        EventType.STRAFFMAL,
        EventType.STRAFFMISS_I_MALSTALLNING,
    }
    assert all(a.outcome and a.outcome.event_id == a.award.event_id + 1 for a in awards)


def test_unlinked_penalty_award_is_inferred() -> None:
    _, events, _ = scenario("05_penalty_pair")
    unlinked = [replace(e, related_event_id=None) for e in events]
    linked = {a.award.event_id: a.outcome for a in penalty_awards(events)}
    inferred = penalty_awards(unlinked)
    assert [a.pairing for a in inferred] == ["inferred", "inferred"]
    assert all(a.outcome and linked[a.award.event_id] == replace(a.outcome, related_event_id=a.award.event_id)
               for a in inferred)  # fmt: skip


def test_penalty_award_without_outcome() -> None:
    match, events, _ = scenario("05_penalty_pair")
    outcomes = {a.outcome.event_id for a in penalty_awards(events) if a.outcome}
    remaining = [e for e in events if e.event_id not in outcomes]
    assert [a.pairing for a in penalty_awards(remaining)] == ["unmatched", "unmatched"]
    flagged = [
        t for t in build_timeline(match, remaining) if t.event and t.event.type is EventType.STRAFFSPARK
    ]
    assert flagged and all(t.orphan and not t.automatic for t in flagged)


# ---------------------------------------------------------------------------- timeline


def _position(entry_period: int | None, minute: int | None, added: int | None) -> tuple[float, float]:
    return (
        math.inf if entry_period is None else entry_period,
        math.inf if minute is None else minute + (added or 0),
    )


@pytest.mark.parametrize("name", WITH_EVENTS)
def test_timeline_contains_everything_in_order(name: str) -> None:
    match, events, officials = scenario(name)
    timeline = build_timeline(match, events, officials)
    sanctions = sum(o.cautioned for o in officials) + sum(o.sent_off for o in officials)
    assert len(timeline) == len(events) + sanctions
    assert sorted(t.event.event_id for t in timeline if t.event) == sorted(e.event_id for e in events)
    positions = [_position(t.period, t.minute, t.added_minutes) for t in timeline]
    assert positions == sorted(positions)


def test_unknown_period_goes_last_not_first() -> None:
    match, events, _ = scenario("08b_period0_empty_minute")
    timeline = build_timeline(match, events)
    assert [t.period for t in timeline[-2:]] == [None, None]
    assert all(t.minute == 0 and not t.period_inferred for t in timeline[-2:])
    assert timeline[0].period == 1


def test_overflow_minute_sorts_inside_the_second_half() -> None:
    match, events, _ = scenario("08c_period0_overflow_minute")
    timeline = build_timeline(match, events)
    overflow = [t for t in timeline if t.minute == 91]
    assert all(t.period == 2 and t.period_inferred for t in overflow)
    assert [t.minute for t in timeline[-3:]] == [90, 91, 91]


def test_added_time_sorts_after_later_base_minutes() -> None:
    match, events, officials = scenario("07_added_time")
    timeline = build_timeline(match, events, officials)
    assert (timeline[-2].kind, timeline[-2].minute, timeline[-2].period) == ("official_caution", 94, 2)
    assert timeline[-2].period_inferred and timeline[-2].official is not None
    assert (timeline[-1].minute, timeline[-1].added_minutes) == (90, 6)


def test_official_sanctions() -> None:
    match, events, officials = scenario("10_official_discipline")
    timeline = build_timeline(match, events, officials)
    official = [t for t in timeline if t.official is not None]
    assert [(t.kind, t.minute) for t in official] == [
        ("official_caution", 90), ("official_sending_off", 90), ("official_sending_off", None)
    ]  # fmt: skip
    assert (timeline[-1].kind, timeline[-1].minute, timeline[-1].period) == (
        "official_sending_off",
        None,
        None,
    )
    assert all(t.match_team_id == t.official.match_team_id for t in official if t.official)
    # 90 (control event), then the two official sanctions at 90, then the caution at 90+4.
    assert [(t.kind, t.minute, t.added_minutes) for t in timeline[-5:-1]] == [
        ("event", 90, None),
        ("official_caution", 90, None),
        ("official_sending_off", 90, None),
        ("event", 90, 4),
    ]


def test_official_with_caution_and_sending_off_gets_two_entries() -> None:
    match, _, officials = scenario("10_official_discipline")
    cautioned = next(o for o in officials if o.cautioned)
    both = replace(cautioned, sent_off_minor=True, sending_off_minute=93)
    assert [(t.kind, t.minute) for t in build_timeline(match, [], [both])] == [
        ("official_caution", 90), ("official_sending_off", 93)
    ]  # fmt: skip


def test_timeline_flags() -> None:
    match, events, _ = scenario("03_auto_second_caution")
    automatic = [t for t in build_timeline(match, events) if t.automatic]
    assert [t.event.type for t in automatic if t.event] == [EventType.LINDRIG_UTVISNING_AVVISNING] * 2
    assert not any(t.orphan for t in automatic)

    match, events, _ = scenario("04_orphan_second_caution")
    timeline = build_timeline(match, events)
    assert [t.event.type for t in timeline if t.orphan and t.event] == [EventType.LINDRIG_UTVISNING_AVVISNING]
    assert all(t.period_inferred and t.period in (1, 2) for t in timeline)

    match, events, _ = scenario("05_penalty_pair")
    timeline = build_timeline(match, events)
    assert [t.event.type for t in timeline if t.automatic and t.event] == [EventType.STRAFFSPARK] * 2
    control = [t for t in timeline if t.is_control]
    assert [t.event.type for t in control if t.event] == [EventType.MATCH_SLUT]

    match, events, _ = scenario("09a_typed_score_mismatch")
    timeline = build_timeline(match, events)
    assert [t.minute for t in timeline if t.score_mismatch] == [60]
    assert sum(t.score is not None for t in timeline) == 7


def test_shootout_comes_after_regular_time() -> None:
    match, events, _ = scenario("06a_penalty_shootout_football")
    timeline = build_timeline(match, events)
    kicks = [i for i, t in enumerate(timeline) if t.event and t.event.type and t.event.type.is_shootout]
    assert kicks == list(range(len(timeline) - len(kicks), len(timeline)))
    assert all(timeline[i].period == 3 and timeline[i].score is None for i in kicks)
