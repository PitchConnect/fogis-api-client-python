"""Encode a typed match time ("23", "45+2", "12:30") the way the referee app does (FOGIS_API.md §6, §10.5).

A direct port of the app's getMatchtidpunktNy / parseMinutSekund / getPeriodFromMinSek (app.min.js v20260610),
quirks included, so that FOGIS stores exactly what it would store for the same input typed in the app:

- "90+5" is sent as minute 95 in the period of the regular minute (2); FOGIS renders it "90+5".
- A minute past the last period ("91" in a 90-minute match) gets period 0, which is how period-0 events arise.
- With high-resolution time, a whole minute "12" is sent as 11:00 (the 12th minute starts at 11:00).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .enums import EventType
from .models import Match

_INT = re.compile(r"^\s*([+-]?\d+)")


@dataclass(frozen=True, slots=True)
class MatchTime:
    period: int  # 0 = FOGIS could not place it
    minute: int
    second: int


def _period_ends_seconds(match: Match) -> list[int]:
    ends = [match.half_length * i * 60 for i in range(1, match.halves + 1)]
    regular = match.halves * match.half_length * 60
    ends += [regular + match.extra_period_length * i * 60 for i in range(1, match.extra_periods + 1)]
    return ends


def _period_ends_minutes(match: Match) -> list[int]:
    return [
        match.half_length * min(p, match.halves)
        + (match.extra_period_length * min(p - match.halves, match.extra_periods) if p > match.halves else 0)
        for p in range(1, match.halves + match.extra_periods + 1)
    ]


def _period_for(minute: int, second: int, event_type: int | None, match: Match) -> int:
    ends = _period_ends_seconds(match)
    t = minute * 60 + second
    if t in ends and event_type in (EventType.BYTE_IN, EventType.BYTE_UT):
        # A substitution exactly at a period's end belongs to the next period (half-time substitution).
        # The app's odd index arithmetic is kept as is.
        last = len(ends) - 1 - ends[::-1].index(t)
        return ends.index(t) + (1 if last == 1 else 2)
    if t in ends and event_type == EventType.HALVLEK_PERIOD_START:
        return ends.index(t) + 2
    if event_type in (EventType.STRAFFAVGORANDE_MAL, EventType.STRAFFAVGORANDE_MISS):
        if not (t != 0 and ends and t < ends[-1]):
            return match.halves + match.extra_periods + 1
        return 0
    for i, end in enumerate(ends):
        if t <= end:
            return i + 1
    return 0


def _parse(text: str, event_type: int | None, match: Match) -> MatchTime:
    minute_text, colon, second_text = text.partition(":")
    minute = _leading_int(minute_text)
    second = _leading_int(second_text) if colon else 0
    return MatchTime(_period_for(minute, second, event_type, match), minute, second)


def _leading_int(text: str) -> int:
    """JavaScript parseInt for the inputs we accept; anything else is an error rather than NaN."""
    m = _INT.match(text)
    if m is None:
        raise ValueError(f"not a match time: {text!r}")
    return int(m.group(1))


def encode_match_time(text: str, match: Match, event_type: int | None) -> MatchTime:
    """What the app sends as (period, matchminut, sekund) for `text` typed as the time of an event.

    Raises ValueError for text that is not a match time (the app would send NaN).
    """
    high_res = match.high_resolution_time
    typed = event_type is not None and event_type > 0
    text = text.strip()
    if not text:
        result = MatchTime(0, 0, 0)
    elif "+" in text:
        regular_text, _, added_text = text.partition("+")
        added = _parse(added_text, event_type, match)
        regular = _parse(regular_text, event_type, match)
        added_minutes = added.minute
        if high_res and added.second == 0 and ":" not in added_text and added_minutes > 0 and typed:
            added_minutes -= 1
        period = _period_for(regular.minute - 1, 0, event_type, match)
        result = MatchTime(period, regular.minute + added_minutes, regular.second + added.second)
    else:
        parsed = _parse(text, event_type, match)
        minute = parsed.minute
        if high_res and parsed.second == 0 and ":" not in text and minute > 0 and typed:
            minute -= 1
        result = MatchTime(parsed.period, minute, parsed.second)

    if event_type in (EventType.STRAFFAVGORANDE_MAL, EventType.STRAFFAVGORANDE_MISS):
        ends = _period_ends_minutes(match)
        if not (result.minute != 0 and ends and result.minute < ends[-1]):
            result = MatchTime(match.halves + match.extra_periods + 1, result.minute, result.second)
    return result
