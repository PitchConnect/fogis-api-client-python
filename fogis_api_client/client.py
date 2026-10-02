"""Read methods of the mobile referee client's API, returning models (FOGIS_API.md §3-4, §7b)."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable, Sequence
from datetime import date, timedelta
from typing import Any

from .checks import Problem, check_report
from .errors import FogisDataError
from .models import (
    CautionRecord,
    LineupChange,
    LineupEntry,
    Match,
    MatchEvent,
    MatchResult,
    TeamOfficial,
)
from .session import FogisSession
from .writes import Confirm, WriteMethods

log = logging.getLogger(__name__)

MATCH_LIST_CAP = 100  # GetMatcherAttRapportera silently truncates to the 100 oldest matches
STATUSES = ("avbruten", "uppskjuten", "installd")  # abandoned, postponed, cancelled
ALL_AGE_CATEGORIES = (1, 2, 3, 4, 5)
ALL_GENDERS = (2, 3, 4)


class FogisClient(WriteMethods):
    """Typed access to FOGIS for a logged-in referee.

    Pass credentials (and optionally a cookie file) or a ready FogisSession. Login happens lazily on the
    first call, and expired sessions are renewed automatically.

    Writes: with dry_run=True nothing is sent (payloads are logged and returned as DryRun); with a confirm
    callback, each write is sent only if confirm(method, payload) returns True.
    """

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        *,
        cookie_file: str | os.PathLike[str] | None = None,
        session: FogisSession | None = None,
        dry_run: bool = False,
        confirm: Confirm | None = None,
    ) -> None:
        self.session = session or FogisSession(username, password, cookie_file=cookie_file)
        self.dry_run = dry_run
        self.confirm = confirm

    # ------------------------------------------------------------------ match list

    def matches(
        self,
        start: date,
        end: date,
        *,
        exclude_statuses: Iterable[str] = (),
        age_categories: Iterable[int] = ALL_AGE_CATEGORIES,
        genders: Iterable[int] = ALL_GENDERS,
    ) -> list[Match]:
        """All of the referee's matches with kick-off date in [start, end], oldest first.

        FOGIS returns at most 100 matches per request, so the range is fetched per calendar year and split
        further wherever a request comes back full. `exclude_statuses` takes values from STATUSES.
        """
        return [
            Match.from_api(d)
            for d in self.matches_raw(
                start, end, exclude_statuses=exclude_statuses, age_categories=age_categories, genders=genders
            )
        ]

    def matches_raw(
        self,
        start: date,
        end: date,
        *,
        exclude_statuses: Iterable[str] = (),
        age_categories: Iterable[int] = ALL_AGE_CATEGORIES,
        genders: Iterable[int] = ALL_GENDERS,
    ) -> list[dict[str, Any]]:
        """As matches(), but the records as FOGIS returns them."""
        if end < start:
            raise ValueError(f"end {end} is before start {start}")
        base = {
            "datumTyp": 1,
            "typ": "alla",
            "status": list(exclude_statuses),
            "alderskategori": list(age_categories),
            "kon": list(genders),
            "sparadDatum": date.today().isoformat(),
        }
        seen: dict[int, dict[str, Any]] = {}
        for chunk_start, chunk_end in _years(start, end):
            for record in self._match_range(base, chunk_start, chunk_end):
                seen.setdefault(record["matchid"], record)
        return sorted(seen.values(), key=lambda d: (d.get("speldatum") or "", d.get("avsparkstid") or ""))

    def _match_range(self, base: dict[str, Any], start: date, end: date) -> list[dict[str, Any]]:
        d = self.session.call(
            "GetMatcherAttRapportera",
            {"filter": {**base, "datumFran": start.isoformat(), "datumTill": end.isoformat()}},
        )
        if not isinstance(d, dict) or not isinstance(d.get("matchlista"), list):
            raise FogisDataError("GetMatcherAttRapportera: no matchlista in response")
        records: list[dict[str, Any]] = d["matchlista"]
        if len(records) < MATCH_LIST_CAP:
            return records
        if start == end:
            log.warning(
                "More than %d matches on %s; FOGIS returns only %d", MATCH_LIST_CAP, start, MATCH_LIST_CAP
            )
            return records
        middle = start + (end - start) // 2
        return self._match_range(base, start, middle) + self._match_range(
            base, middle + timedelta(days=1), end
        )

    def match(self, match_id: int, around: date | None = None, days: int = 400) -> Match | None:
        """Find one match. FOGIS has no single-match method, so this scans the list around `around`
        (default today) +/- `days`. Prefer looking the match up in a list you already have."""
        centre = around or date.today()
        for m in self.matches(centre - timedelta(days=days), centre + timedelta(days=days)):
            if m.match_id == match_id:
                return m
        return None

    # ------------------------------------------------------------------ per match

    def events(self, match_id: int) -> list[MatchEvent]:
        return [MatchEvent.from_api(d) for d in self._list("GetMatchhandelselista", {"matchid": match_id})]

    def results(self, match_id: int) -> list[MatchResult]:
        return [MatchResult.from_api(d) for d in self._list("GetMatchresultatlista", {"matchid": match_id})]

    def lineup_changes(self, match_id: int) -> list[LineupChange]:
        rows = self._list("GetMatchdeltagareAndringForMatch", {"matchid": match_id})
        return [LineupChange.from_api(d) for d in rows]

    # ------------------------------------------------------------------ per team in a match

    def lineup(self, match_team_id: int) -> list[LineupEntry]:
        """Players of one team in one match (match_team_id = Match.home/away.match_team_id)."""
        rows = self._list("GetMatchdeltagareListaForMatchlag", {"matchlagid": match_team_id})
        return [LineupEntry.from_api(d) for d in rows]

    def officials(self, match_team_id: int) -> list[TeamOfficial]:
        """Team officials of one team in one match, including their discipline."""
        rows = self._list("GetMatchlagledareListaForMatchlag", {"matchlagid": match_team_id})
        return [TeamOfficial.from_api(d) for d in rows]

    # ------------------------------------------------------------------ per team in a competition

    def earlier_matches(self, competition_id: int, engagement_id: int) -> list[Match]:
        """A team's earlier matches in a competition (engagement_id = MatchTeam.engagement_id)."""
        rows = self._list(
            "hamtaTidigareMatcherForLag", {"tavlingsId": competition_id, "lagengagemangId": engagement_id}
        )
        return [Match.from_api(d) for d in rows]

    def player_cautions(self, player_id: int, engagement_id: int) -> list[CautionRecord]:
        """A player's cautions in the competition of `engagement_id`. Intended for your own matches."""
        rows = self._list(
            "SokVarningarForSpelareITavling", {"spelareId": player_id, "lagengagemangId": engagement_id}
        )
        return [CautionRecord.from_api(d) for d in rows]

    def official_cautions(self, person_id: int, engagement_id: int) -> list[CautionRecord]:
        """A team official's cautions in the competition of `engagement_id`. Intended for your own matches."""
        rows = self._list(
            "SokVarningarForLedareITavling", {"personId": person_id, "lagengagemangId": engagement_id}
        )
        return [CautionRecord.from_api(d) for d in rows]

    # ------------------------------------------------------------------ checks

    def check_report(self, match: Match) -> list[Problem]:
        """Read the report and list what looks wrong (see checks.check_report). Empty = nothing found."""
        teams = (match.home.match_team_id, match.away.match_team_id)
        officials = [o for t in teams for o in self.officials(t)]
        lineup = [p for t in teams for p in self.lineup(t)]
        return check_report(
            match, self.events(match.match_id), self.results(match.match_id), officials, lineup
        )

    # ------------------------------------------------------------------ other

    def application_config(self) -> dict[str, Any]:
        d = self.session.call("GetApplicationConfig")
        if not isinstance(d, dict):
            raise FogisDataError("GetApplicationConfig: expected an object")
        return d

    def _list(self, method: str, payload: dict[str, Any]) -> Sequence[dict[str, Any]]:
        d = self.session.call(method, payload)
        if not isinstance(d, list):
            raise FogisDataError(f"{method}: expected a list, got {type(d).__name__}")
        return d

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> FogisClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _years(start: date, end: date) -> list[tuple[date, date]]:
    chunks = []
    cur = start
    while cur <= end:
        year_end = min(date(cur.year, 12, 31), end)
        chunks.append((cur, year_end))
        cur = year_end + timedelta(days=1)
    return chunks
