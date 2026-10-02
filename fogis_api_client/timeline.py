"""Pure helpers that interpret stored events as a match timeline (FOGIS_API.md §6, §8).

FOGIS stores events as typed, not as they happened: periods may be 0, substitutions are two events that
are linked only since ~2024, typed scores are never validated, and the server creates the #2 on a second
caution itself. A #3 "penalty awarded" is entered by live reporters before the penalty's outcome.
These functions take models and return frozen dataclasses; no I/O.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal

from .enums import EventType
from .models import Match, MatchEvent, TeamOfficial

SubstitutionPairing = Literal["linked", "inferred", "unmatched"]
PenaltyPairing = Literal["linked", "inferred", "unmatched"]
SecondCautionKind = Literal["automatic", "orphan"]
EntryKind = Literal["event", "official_caution", "official_sending_off"]

PENALTY_OUTCOMES = frozenset(
    {
        EventType.STRAFFMAL,
        EventType.STRAFFMISS_UTANFOR,
        EventType.STRAFFMISS_RADDNING,
        EventType.STRAFFMISS_I_MALSTALLNING,
    }
)


# ---------------------------------------------------------------------------- periods


def last_period_played(match: Match, events: Iterable[MatchEvent]) -> int | None:
    """Highest regular or extra period with a stored event (at least `match.halves`); None without evidence.

    Tells a stoppage-time minute ("91" typed for "90+1") from extra time in matches that allow extra periods.
    Shoot-out and control events are ignored (control events are unreliable, §6).
    """
    final = match.halves + match.extra_periods
    stored = [
        e.period
        for e in events
        if 0 < e.period <= final and not (e.type is not None and (e.type.is_shootout or e.type.is_control))
    ]
    return max(match.halves, *stored) if stored else None


def period_for_minute(minute: int | None, match: Match, *, last_period: int | None = None) -> int | None:
    """Period a minute falls in: (0, L] -> 1, (L, 2L] -> 2, then extra periods (FOGIS_API.md §6).

    A minute beyond the last period (`last_period`, else every configured period) belongs to that period.
    Returns None for minute 0/None (unknown) and when the match has no period lengths to go by.
    """
    if not minute or minute < 0 or match.halves <= 0 or match.half_length <= 0:
        return None
    final = match.halves + match.extra_periods
    last = final if last_period is None else max(match.halves, min(last_period, final))
    end = 0
    for period in range(1, last + 1):
        length = match.half_length if period <= match.halves else match.extra_period_length
        if length <= 0:
            return None  # extra time was played but its length is unknown
        end += length
        if minute <= end:
            return period
    return last


def effective_period(event: MatchEvent, match: Match, *, last_period: int | None = None) -> int | None:
    """The stored period if known, the shoot-out period for shoot-out kicks, else inferred from the minute."""
    if event.period > 0:
        return event.period
    if event.type is not None and event.type.is_shootout:
        return match.shootout_period
    return period_for_minute(event.minute, match, last_period=last_period)


def _sort_key(
    period: int | None, minute: int | None, added: int | None, rank: int, tiebreak: int
) -> tuple[float, float, int, int]:
    # Unknown period and unknown minute go last, not first as on the public web (§6). Within a period,
    # minute + added time orders "91" (typed for 90+1) before "90+3".
    return (
        math.inf if period is None else period,
        math.inf if minute is None else minute + (added or 0),
        rank,
        tiebreak,
    )


def _ordered(match: Match, events: Sequence[MatchEvent]) -> list[tuple[MatchEvent, int | None]]:
    last = last_period_played(match, events)
    keyed = [(e, effective_period(e, match, last_period=last)) for e in events]
    return sorted(
        keyed, key=lambda ep: _sort_key(ep[1], ep[0].minute, ep[0].added_minutes, 0, ep[0].event_id)
    )


# ---------------------------------------------------------------------------- substitutions


@dataclass(frozen=True, slots=True)
class Substitution:
    """A player off (16) and a player on (17). Either is None when no partner was found."""

    off: MatchEvent | None
    on: MatchEvent | None
    pairing: SubstitutionPairing

    @property
    def match_team_id(self) -> int | None:
        either = self.off or self.on
        return either.match_team_id if either else None


def pair_substitutions(events: Iterable[MatchEvent]) -> list[Substitution]:
    """Pair 16 ByteUt with 17 ByteIn (FOGIS_API.md §6).

    "linked": the 17's related_event_id names a 16 of the same team (since ~2024).
    "inferred": remaining events of the same team with the same minute and time text, in event-id order.
    "unmatched": no partner. Never pairs across teams. Sorted by minute, then the lower event id.
    """
    events = list(events)
    offs = {e.event_id: e for e in events if e.type is EventType.BYTE_UT}
    ons = [e for e in events if e.type is EventType.BYTE_IN]
    result: list[Substitution] = []
    unlinked_on: list[MatchEvent] = []
    for on in ons:
        off = offs.get(on.related_event_id) if on.related_event_id else None
        if off is not None and off.match_team_id == on.match_team_id:
            result.append(Substitution(off, on, "linked"))
            del offs[off.event_id]
        else:
            unlinked_on.append(on)

    def group(e: MatchEvent) -> tuple[int | None, int, str]:
        return (e.match_team_id, e.minute, e.time_text)

    waiting: dict[tuple[int | None, int, str], list[MatchEvent]] = defaultdict(list)
    for off in sorted(offs.values(), key=lambda e: e.event_id):
        waiting[group(off)].append(off)
    for on in sorted(unlinked_on, key=lambda e: e.event_id):
        candidates = waiting.get(group(on)) if on.match_team_id is not None else None
        if candidates:
            result.append(Substitution(candidates.pop(0), on, "inferred"))
        else:
            result.append(Substitution(None, on, "unmatched"))
    result.extend(Substitution(off, None, "unmatched") for queue in waiting.values() for off in queue)

    def order(s: Substitution) -> tuple[int, int, int]:
        pair = [e for e in (s.off, s.on) if e is not None]
        first = min(pair, key=lambda e: e.event_id)
        return (first.minute, first.added_minutes or 0, first.event_id)

    return sorted(result, key=order)


# ---------------------------------------------------------------------------- score


@dataclass(frozen=True, slots=True)
class GoalScore:
    """The score after one goal: computed from the goals so far vs. typed by the reporter (§6)."""

    event: MatchEvent
    home: int
    away: int
    typed_home: int
    typed_away: int

    @property
    def mismatch(self) -> bool:
        return (self.home, self.away) != (self.typed_home, self.typed_away)


def running_score(events: Sequence[MatchEvent], match: Match) -> list[GoalScore]:
    """Every counting goal in timeline order with the score after it (FOGIS_API.md §6).

    A goal counts for its match_team_id; own goals (15) are stored on the benefiting team. Shoot-out kicks
    don't count. A goal on neither team's match_team_id changes nothing (and so shows as a mismatch).
    """
    home = away = 0
    scores: list[GoalScore] = []
    for e, _ in _ordered(match, events):
        if e.type is None or not e.type.is_goal:
            continue
        if e.match_team_id == match.home.match_team_id:
            home += 1
        elif e.match_team_id == match.away.match_team_id:
            away += 1
        scores.append(GoalScore(e, home, away, e.home_goals, e.away_goals))
    return scores


def shootout_score(events: Iterable[MatchEvent], match: Match) -> tuple[int, int] | None:
    """Goals scored in the penalty shoot-out (21) per team, or None if there was no shoot-out."""
    kicks = [e for e in events if e.type is not None and e.type.is_shootout]
    if not kicks:
        return None
    goals = [e.match_team_id for e in kicks if e.type is EventType.STRAFFAVGORANDE_MAL]
    return goals.count(match.home.match_team_id), goals.count(match.away.match_team_id)


# ---------------------------------------------------------------------------- server-generated events


def _player_key(e: MatchEvent) -> tuple[str, int] | None:
    if e.player_id is not None:
        return ("player", e.player_id)
    if e.participant_id is not None:
        return ("participant", e.participant_id)
    return None


def classify_second_caution_sending_offs(events: Iterable[MatchEvent]) -> dict[int, SecondCautionKind]:
    """Classify each #2 (LINDRIG_UTVISNING_AVVISNING) by event id (FOGIS_API.md §6).

    "automatic": the server created it; the same player has two cautions saved before it (lower event id).
    "orphan": fewer than two, typically because the 2nd caution was deleted and the #2 stayed behind.
    Event-id order is the server's creation order, so a caution re-entered later doesn't rescue an old #2.
    """
    events = sorted(events, key=lambda e: e.event_id)
    cautions: dict[tuple[str, int], int] = defaultdict(int)
    result: dict[int, SecondCautionKind] = {}
    for e in events:
        key = _player_key(e)
        if e.type is not None and e.type.is_caution and key is not None:
            cautions[key] += 1
        elif e.type is EventType.LINDRIG_UTVISNING_AVVISNING:
            result[e.event_id] = "automatic" if key is not None and cautions[key] >= 2 else "orphan"
    return result


@dataclass(frozen=True, slots=True)
class PenaltyAward:
    """A #3 (STRAFFSPARK, "penalty awarded", entered by live reporters) and the outcome it belongs to."""

    award: MatchEvent
    outcome: MatchEvent | None
    pairing: PenaltyPairing


def penalty_awards(events: Iterable[MatchEvent]) -> list[PenaltyAward]:
    """Pair each #3 with its outcome (14, 18, 19, 26) (FOGIS_API.md §6).

    "linked": an event's related_event_id names the #3. "inferred": the next penalty outcome by event id
    with the same player and time text. "unmatched": none found (maybe left behind like an orphan #2
    [unverified]).
    """
    events = sorted(events, key=lambda e: e.event_id)
    awards = [e for e in events if e.type is EventType.STRAFFSPARK]
    award_ids = {a.event_id for a in awards}
    linked = {e.related_event_id: e for e in events if e.related_event_id in award_ids}
    claimed = {e.event_id for e in linked.values()}
    result: list[PenaltyAward] = []
    for award in awards:
        if award.event_id in linked:
            result.append(PenaltyAward(award, linked[award.event_id], "linked"))
            continue
        outcome = next(
            (
                e
                for e in events
                if e.event_id > award.event_id
                and e.event_id not in claimed
                and e.type in PENALTY_OUTCOMES
                and _player_key(e) == _player_key(award)
                and e.time_text == award.time_text
            ),
            None,
        )
        if outcome is None:
            result.append(PenaltyAward(award, None, "unmatched"))
        else:
            claimed.add(outcome.event_id)
            result.append(PenaltyAward(award, outcome, "inferred"))
    return result


# ---------------------------------------------------------------------------- timeline


@dataclass(frozen=True, slots=True)
class TimelineEntry:
    """One line of a match timeline: a stored event or a team-official sanction (§8; not events in FOGIS)."""

    kind: EntryKind
    period: int | None  # effective period; None = unknown
    minute: int | None  # None for an official sanction saved without a minute
    added_minutes: int | None
    match_team_id: int | None
    event: MatchEvent | None
    official: TeamOfficial | None
    period_inferred: bool = False  # period not stored; derived from the minute (or the shoot-out)
    automatic: bool = False  # #2 created by the server after two cautions, or a #3 paired with its outcome
    orphan: bool = False  # cause is gone: #2 without two cautions, #3 without its penalty outcome
    score: GoalScore | None = None  # counting goals only

    @property
    def score_mismatch(self) -> bool:
        return self.score is not None and self.score.mismatch

    @property
    def is_control(self) -> bool:
        return self.event is not None and self.event.type is not None and self.event.type.is_control


_KIND_RANK: dict[EntryKind, int] = {"event": 0, "official_caution": 1, "official_sending_off": 2}


def build_timeline(
    match: Match, events: Sequence[MatchEvent], officials: Iterable[TeamOfficial] = ()
) -> list[TimelineEntry]:
    """All events plus team-official cautions and sending-offs, in match order.

    Sorted by effective period, minute + added minutes, events before official sanctions, then id. Entries
    with an unknown period or minute come last. Control events are kept (see `is_control`).
    """
    last = last_period_played(match, events)
    second_cautions = classify_second_caution_sending_offs(events)
    awards = {a.award.event_id: a for a in penalty_awards(events)}
    scores = {s.event.event_id: s for s in running_score(events, match)}

    entries: list[tuple[tuple[float, float, int, int], TimelineEntry]] = []
    for e in events:
        period = effective_period(e, match, last_period=last)
        award = awards.get(e.event_id)
        second_caution = second_cautions.get(e.event_id)
        automatic = second_caution == "automatic" or (award is not None and award.outcome is not None)
        orphan = second_caution == "orphan" or (award is not None and award.outcome is None)
        entry = TimelineEntry(
            kind="event",
            period=period,
            minute=e.minute,
            added_minutes=e.added_minutes,
            match_team_id=e.match_team_id,
            event=e,
            official=None,
            period_inferred=e.period <= 0 and period is not None,
            automatic=automatic,
            orphan=orphan,
            score=scores.get(e.event_id),
        )
        entries.append((_sort_key(period, e.minute, e.added_minutes, 0, e.event_id), entry))

    for o in officials:
        sanctions: list[tuple[EntryKind, int | None]] = []
        if o.cautioned:
            sanctions.append(("official_caution", o.caution_minute))
        if o.sent_off:
            sanctions.append(("official_sending_off", o.sending_off_minute))
        for kind, minute in sanctions:
            period = period_for_minute(minute, match, last_period=last)
            entry = TimelineEntry(
                kind=kind,
                period=period,
                minute=minute,
                added_minutes=None,
                match_team_id=o.match_team_id,
                event=None,
                official=o,
                period_inferred=period is not None,
            )
            entries.append((_sort_key(period, minute, None, _KIND_RANK[kind], o.official_id), entry))

    return [entry for _, entry in sorted(entries, key=lambda ke: ke[0])]
