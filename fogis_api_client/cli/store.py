"""What the CLI keeps between runs: the FOGIS cookie jar, and a cache of match reports the referee has
approved (they hardly change after that, so repeat questions need no FOGIS calls)."""

from __future__ import annotations

import json
import os
import shutil
import sys
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, date, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any

from ..client import FogisClient
from ..errors import FogisError
from ..models import LineupChange, LineupEntry, Match, MatchEvent, MatchResult, TeamOfficial

CACHE_VERSION = 1
SCAN_DAYS = 400  # how far around today a match is looked for when its date is unknown

Raw = dict[str, Any]


def config_dir(env: Mapping[str, str]) -> Path:
    """FOGIS_CONFIG_DIR, else $XDG_CONFIG_HOME/fogis, else ~/.config/fogis. Holds the cookie jar."""
    return _dir(env, "FOGIS_CONFIG_DIR", "XDG_CONFIG_HOME", "~/.config")


def cache_dir(env: Mapping[str, str]) -> Path:
    """FOGIS_CACHE_DIR, else $XDG_CACHE_HOME/fogis, else ~/.cache/fogis."""
    return _dir(env, "FOGIS_CACHE_DIR", "XDG_CACHE_HOME", "~/.cache")


def _dir(env: Mapping[str, str], own: str, xdg: str, default: str) -> Path:
    if env.get(own):
        return Path(env[own]).expanduser()
    return Path(env.get(xdg) or default).expanduser() / "fogis"


def ensure_dir(path: Path) -> Path:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    return path


def _write_json(path: Path, value: Any) -> None:
    ensure_dir(path.parent)
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False)
    os.replace(tmp, path)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        return None  # a damaged cache file is as good as none


class MatchCache:
    """matches/<id>.json: the FOGIS records of an approved report. index.json: match id -> date, so a
    match can be found again without scanning months of the match list."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def get(self, match_id: int) -> Raw | None:
        d = _read_json(self._path(match_id))
        return d if isinstance(d, dict) and d.get("version") == CACHE_VERSION else None

    def put(self, match_id: int, match: Raw, records: Mapping[str, list[Raw]]) -> None:
        cached_at = datetime.now(UTC).isoformat(timespec="seconds")
        entry = {"version": CACHE_VERSION, "cached_at": cached_at, "match": match, "records": dict(records)}
        _write_json(self._path(match_id), entry)

    def known_date(self, match_id: int) -> date | None:
        value = self._index().get(str(match_id))
        try:
            return date.fromisoformat(value) if isinstance(value, str) else None
        except ValueError:
            return None

    def remember(self, matches: Iterable[Match]) -> None:
        index = self._index()
        new = {str(m.match_id): m.date.isoformat() for m in matches if m.date is not None}
        if any(index.get(k) != v for k, v in new.items()):
            _write_json(self.root / "index.json", {**index, **new})

    def list(self) -> list[Raw]:
        entries = (self.get(int(p.stem)) for p in sorted((self.root / "matches").glob("*.json")))
        return [e for e in entries if e is not None]

    def clear(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _index(self) -> dict[str, Any]:
        d = _read_json(self.root / "index.json")
        return d if isinstance(d, dict) else {}

    def _path(self, match_id: int) -> Path:
        return self.root / "matches" / f"{int(match_id)}.json"


def is_settled(match: Match) -> bool:
    """A report worth caching: approved by the referee, or a match that will not be played."""
    return match.report_approved or match.cancelled


def find_match(
    client: FogisClient, cache: MatchCache, match_id: int, *, on: date | None = None, refresh: bool = False
) -> Raw:
    """The FOGIS record of one of the referee's matches: from the cache, else from the match list of its
    date (given, or remembered), else by scanning SCAN_DAYS around today."""
    if not refresh and (cached := cache.get(match_id)) is not None:
        return dict(cached["match"])
    day = on or cache.known_date(match_id)
    if day is not None:
        start, end = day, day
    else:
        print(
            f"fogis: looking for match {match_id} within {SCAN_DAYS} days of today (--date is faster)",
            file=sys.stderr,
        )
        start, end = date.today() - timedelta(days=SCAN_DAYS), date.today() + timedelta(days=SCAN_DAYS)
    records = client.matches_raw(start, end)
    cache.remember(Match.from_api(r) for r in records)
    for r in records:
        if r["matchid"] == match_id:
            return r
    where = f"on {day}" if day is not None else f"within {SCAN_DAYS} days of today"
    raise FogisError(f"Match {match_id} is not among your matches {where}")


class MatchData:
    """One match's report, read once: from the cache if it is there, else from FOGIS. A settled report is
    fetched whole on first use and cached; any other is fetched piece by piece as asked for."""

    def __init__(self, client: FogisClient, cache: MatchCache, match: Raw, *, refresh: bool = False) -> None:
        self.match = Match.from_api(match)
        self._client = client
        self._cache = cache
        self._raw = match
        cached = None if refresh else cache.get(self.match.match_id)
        self._records: dict[str, list[Raw]] = dict(cached["records"]) if cached else {}
        self.cached_at: str | None = cached["cached_at"] if cached else None

    @property
    def teams(self) -> dict[str, int]:
        return {"home": self.match.home.match_team_id, "away": self.match.away.match_team_id}

    def events(self) -> list[MatchEvent]:
        return [MatchEvent.from_api(d) for d in self._get("events")]

    def results(self) -> list[MatchResult]:
        return [MatchResult.from_api(d) for d in self._get("results")]

    def lineup_changes(self) -> list[LineupChange]:
        return [LineupChange.from_api(d) for d in self._get("lineup_changes")]

    def lineup(self, match_team_id: int) -> list[LineupEntry]:
        return [LineupEntry.from_api(d) for d in self._get(f"lineup:{match_team_id}")]

    def officials(self, match_team_id: int) -> list[TeamOfficial]:
        return [TeamOfficial.from_api(d) for d in self._get(f"officials:{match_team_id}")]

    def _get(self, key: str) -> list[Raw]:
        if key not in self._records:
            if is_settled(self.match):
                self._fetch_all()
            else:
                self._records[key] = self._fetchers()[key]()
        return self._records[key]

    def _fetch_all(self) -> None:
        self._records = {key: fetch() for key, fetch in self._fetchers().items()}
        self._cache.put(self.match.match_id, self._raw, self._records)

    def _fetchers(self) -> dict[str, Callable[[], list[Raw]]]:
        c, match_id = self._client, self.match.match_id

        def raw(models: Callable[[], Iterable[Any]]) -> Callable[[], list[Raw]]:
            return lambda: [dict(m.raw) for m in models()]

        fetchers = {
            "events": raw(partial(c.events, match_id)),
            "results": raw(partial(c.results, match_id)),
            "lineup_changes": raw(partial(c.lineup_changes, match_id)),
        }
        for team in self.teams.values():
            fetchers[f"lineup:{team}"] = raw(partial(c.lineup, team))
            fetchers[f"officials:{team}"] = raw(partial(c.officials, team))
        return fetchers
