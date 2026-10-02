"""Checks to run before submitting a referee report. FOGIS itself checks none of this (FOGIS_API.md §6-8)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Literal

from .enums import ResultType
from .models import LineupEntry, Match, MatchEvent, MatchResult, TeamOfficial
from .timeline import (
    classify_second_caution_sending_offs,
    effective_period,
    last_period_played,
    pair_substitutions,
    running_score,
    shootout_score,
)

Severity = Literal["error", "warning"]


@dataclass(frozen=True, slots=True)
class Problem:
    severity: Severity
    code: str
    message: str
    event_ids: tuple[int, ...] = field(default=())


def check_report(
    match: Match,
    events: Sequence[MatchEvent],
    results: Iterable[MatchResult],
    officials: Iterable[TeamOfficial] = (),
    lineup: Iterable[LineupEntry] = (),
) -> list[Problem]:
    """Everything that looks wrong in a report, errors first. An empty list means nothing was found."""
    problems: list[Problem] = []
    rows = {r.type_id: r for r in results}
    scores = running_score(events, match)
    goals = (scores[-1].home, scores[-1].away) if scores else (0, 0)

    final = rows.get(ResultType.SLUTRESULTAT)
    if final is None or not match.result_is_final:
        problems.append(Problem("error", "no_final_result", "No final result is reported"))
    else:
        reported = (final.home_goals, final.away_goals)
        shootout = shootout_score(events, match)
        allowed = {goals} | ({(goals[0] + shootout[0], goals[1] + shootout[1])} if shootout else set())
        if reported not in allowed:
            problems.append(
                Problem(
                    "error",
                    "final_result_mismatch",
                    f"Final result {_s(reported)} but the goals in the events add up to {_s(goals)}",
                )
            )
        if (match.home_goals, match.away_goals) != reported:
            problems.append(
                Problem(
                    "error",
                    "match_score_mismatch",
                    f"The match shows {_s((match.home_goals, match.away_goals))}, "
                    f"the final result row {_s(reported)}",
                )
            )

    half = rows.get(ResultType.HALVTIDSRESULTAT)
    if half is not None:
        last = last_period_played(match, events)
        first_half = [s for s in scores if effective_period(s.event, match, last_period=last) == 1]
        at_half = (
            sum(s.event.match_team_id == match.home.match_team_id for s in first_half),
            sum(s.event.match_team_id == match.away.match_team_id for s in first_half),
        )
        if (half.home_goals, half.away_goals) != at_half:
            problems.append(
                Problem(
                    "error",
                    "half_time_mismatch",
                    f"Half-time result {_s((half.home_goals, half.away_goals))} but the goals in "
                    f"the first half add up to {_s(at_half)}",
                )
            )

    signature = Counter(_signature(e) for e in events)
    for sig, n in signature.items():
        if n > 1:
            ids = tuple(e.event_id for e in events if _signature(e) == sig)
            problems.append(
                Problem("error", "duplicate_event", f"{n} identical events: type {sig[0]} at '{sig[3]}'", ids)
            )

    for e in events:
        if (e.type is not None and e.type.is_control) or (e.type is not None and e.type.is_shootout):
            continue
        if e.minute == 0 and e.period == 0:
            problems.append(
                Problem("error", "no_minute", f"{e.type_name or e.type_id} has no minute", (e.event_id,))
            )
        elif e.period == 0:
            problems.append(
                Problem(
                    "warning",
                    "unknown_period",
                    f"{e.type_name or e.type_id} at '{e.time_text}' has no period; FOGIS lists it "
                    "first on the public web (type '90+1' instead of '91')",
                    (e.event_id,),
                )
            )

    for event_id, kind in classify_second_caution_sending_offs(events).items():
        if kind == "orphan":
            problems.append(
                Problem(
                    "error",
                    "orphan_second_caution",
                    "A sending-off for a second caution without two cautions (delete it?)",
                    (event_id,),
                )
            )

    for s in scores:
        if s.mismatch:
            problems.append(
                Problem(
                    "warning",
                    "typed_score_mismatch",
                    f"Goal at '{s.event.time_text}' is typed {_s((s.typed_home, s.typed_away))}, "
                    f"the goals so far make it {_s((s.home, s.away))}",
                    (s.event.event_id,),
                )
            )

    for sub in pair_substitutions(events):
        if sub.pairing == "unmatched":
            lone = sub.off or sub.on
            if lone is not None:
                missing = "on" if sub.on is None else "off"
                problems.append(
                    Problem(
                        "warning",
                        "half_substitution",
                        f"Substitution at '{lone.time_text}' has no {missing} player",
                        (lone.event_id,),
                    )
                )

    officials = list(officials)
    if officials and match.raw.get("tavlingDomareKravForekomstAvAnsvarigLagledareIGodkandDomarrapport"):
        for team in (match.home, match.away):
            if not any(o.responsible for o in officials if o.match_team_id == team.match_team_id):
                problems.append(
                    Problem(
                        "error",
                        "no_responsible_official",
                        f"{team.name or team.match_team_id} has no responsible team official",
                    )
                )

    players = list(lineup)
    for team in (match.home, match.away):
        squad = [p for p in players if p.match_team_id == team.match_team_id]
        if squad and not any(p.captain for p in squad):
            # FOGIS refuses the submission for this: "Bortalagets matchtrupp saknar lagkapten." [live]
            problems.append(
                Problem("error", "no_captain", f"{team.name or team.match_team_id} has no captain")
            )

    return sorted(problems, key=lambda p: p.severity != "error")


def _signature(e: MatchEvent) -> tuple[int, int | None, int | None, str]:
    return (e.type_id, e.match_team_id, e.player_id, e.time_text)


def _s(score: tuple[int, int]) -> str:
    return f"{score[0]}-{score[1]}"
