from dataclasses import replace
from typing import Any

from conftest import load
from test_verify_runner import fake

from fogis_api_client import FogisClient, check_report
from fogis_api_client.models import LineupEntry, Match, MatchEvent, MatchResult, TeamOfficial


def scenario(name: str) -> tuple[Match, list[MatchEvent], list[TeamOfficial]]:
    match = Match.from_api(load(name, "matches")[0])
    return (
        match,
        [MatchEvent.from_api(e) for e in load(name, "events")],
        [TeamOfficial.from_api(o) for o in load(name, "officials")],
    )


def result(match: Match, kind: int, home: int, away: int) -> MatchResult:
    return MatchResult.from_api(
        {
            "matchresultatid": kind,
            "matchid": match.match_id,
            "matchresultattypid": kind,
            "matchlag1mal": home,
            "matchlag2mal": away,
            "wo": False,
            "ow": False,
            "ww": False,
        }
    )


def codes(problems: Any) -> set[str]:
    return {p.code for p in problems}


def correct_results(match: Match, events: list[MatchEvent]) -> list[MatchResult]:
    first = [e for e in events if e.type and e.type.is_goal and e.period == 1]
    half = (
        sum(e.match_team_id == match.home.match_team_id for e in first),
        sum(e.match_team_id == match.away.match_team_id for e in first),
    )
    return [result(match, 1, match.home_goals, match.away_goals), result(match, 2, *half)]


def test_a_correct_report_has_no_errors() -> None:
    match, events, officials = scenario("01_modern_linked_subs")
    problems = check_report(match, events, correct_results(match, events), officials)
    assert [p for p in problems if p.severity == "error"] == []


def test_wrong_final_and_half_time_results() -> None:
    match, events, officials = scenario("01_modern_linked_subs")
    wrong = [result(match, 1, match.home_goals + 1, match.away_goals), result(match, 2, 5, 5)]
    assert {"final_result_mismatch", "match_score_mismatch", "half_time_mismatch"} <= codes(
        check_report(match, events, wrong, officials)
    )


def test_missing_final_result() -> None:
    match, events, _ = scenario("01_modern_linked_subs")
    assert "no_final_result" in codes(check_report(match, events, []))


def test_duplicate_substitution_like_on_sunday() -> None:
    match, events, _ = scenario("01_modern_linked_subs")
    sub = [e for e in events if e.type_id in (16, 17)][:2]
    copies = [replace(e, event_id=e.event_id + 10_000) for e in sub]
    problems = check_report(match, events + copies, correct_results(match, events))
    assert "duplicate_event" in codes(problems)


def test_event_without_a_minute_like_on_sunday() -> None:
    match, events, _ = scenario("08b_period0_empty_minute")
    assert "no_minute" in codes(check_report(match, events, correct_results(match, events)))


def test_orphan_second_caution() -> None:
    match, events, _ = scenario("04_orphan_second_caution")
    assert "orphan_second_caution" in codes(check_report(match, events, []))


def test_typed_score_mismatch_is_a_warning() -> None:
    match, events, _ = scenario("09a_typed_score_mismatch")
    flagged = [p for p in check_report(match, events, []) if p.code == "typed_score_mismatch"]
    assert flagged and all(p.severity == "warning" for p in flagged)


def test_team_without_responsible_official() -> None:
    match, events, officials = scenario("01_modern_linked_subs")
    match = replace(
        match, raw={**match.raw, "tavlingDomareKravForekomstAvAnsvarigLagledareIGodkandDomarrapport": True}
    )
    nobody = [replace(o, responsible=False) for o in officials]
    assert "no_responsible_official" in codes(
        check_report(match, events, correct_results(match, events), nobody)
    )


def test_submission_is_refused_while_the_report_has_errors() -> None:
    f = fake()
    client = FogisClient(session=f, dry_run=True)  # type: ignore[arg-type]
    m = Match.from_api(f.match)
    f.results = [
        dict(r, matchlag1mal=r["matchlag1mal"] + 1) if r["matchresultattypid"] == 1 else r for r in f.results
    ]
    try:
        client.mark_reporting_finished(m, confirm_match_id=m.match_id)
    except ValueError as e:
        assert "problems" in str(e) and "Final result" in str(e)
    else:
        raise AssertionError("submission was not refused")
    assert client.mark_reporting_finished(m, confirm_match_id=m.match_id, ignore_problems=True).method == (
        "SparaMatchGodkannDomarrapport"
    )


def test_team_without_captain_like_on_sunday() -> None:
    match, events, _ = scenario("01_modern_linked_subs")
    lineup = [LineupEntry.from_api(r) for r in load("01_modern_linked_subs", "lineups")]
    assert "no_captain" not in codes(check_report(match, events, correct_results(match, events), (), lineup))
    no_away_captain = [
        replace(p, captain=False) if p.match_team_id == match.away.match_team_id else p for p in lineup
    ]
    flagged = [
        p
        for p in check_report(match, events, correct_results(match, events), (), no_away_captain)
        if p.code == "no_captain"
    ]
    assert len(flagged) == 1 and flagged[0].severity == "error"
