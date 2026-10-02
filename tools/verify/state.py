"""Snapshot of everything a referee can change in one match, and semantic comparison of two snapshots."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from fogis_api_client import FogisClient
from fogis_api_client.models import LineupEntry, Match, MatchEvent, TeamOfficial

# Fields of an official record that the discipline form writes.
OFFICIAL_FIELDS = (
    "lagrollid",
    "ansvarig",
    "varnad",
    "varnadmatchminut",
    "avvisadlindrig",
    "avvisadgrov",
    "avvisadmatchminut",
)
RESULT_FIELDS = ("matchresultattypid", "matchlag1mal", "matchlag2mal", "wo", "ow", "ww")
LINEUP_FIELDS = (
    "trojnummer",
    "lagdelid",
    "lagkapten",
    "ersattare",
    "positionsnummerhv",
    "arSpelandeLedare",
    "ansvarig",
)
MATCH_FIELDS = (
    "antalaskadare",
    "noteringfrandomare",
    "matchlag1mal",
    "matchlag2mal",
    "arslutresultat",
    "matchrapportgodkandavdomare",
    "liverapporteringAvslutad",
)


@dataclass
class MatchState:
    match: dict[str, Any]
    events: list[dict[str, Any]]
    results: list[dict[str, Any]]
    lineups: dict[int, list[dict[str, Any]]] = field(default_factory=dict)
    officials: dict[int, list[dict[str, Any]]] = field(default_factory=dict)

    @property
    def model(self) -> Match:
        return Match.from_api(self.match)

    def event_models(self) -> list[MatchEvent]:
        return [MatchEvent.from_api(e) for e in self.events]

    def players(self) -> list[LineupEntry]:
        return [LineupEntry.from_api(r) for rows in self.lineups.values() for r in rows]

    def official_models(self) -> list[TeamOfficial]:
        return [TeamOfficial.from_api(r) for rows in self.officials.values() for r in rows]

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=1), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> MatchState:
        d = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            match=d["match"],
            events=d["events"],
            results=d["results"],
            lineups={int(k): v for k, v in d["lineups"].items()},
            officials={int(k): v for k, v in d["officials"].items()},
        )


def take_snapshot(client: FogisClient, match_id: int, around: date) -> MatchState:
    match = client.match(match_id, around=around, days=3)
    if match is None:
        raise LookupError(f"match {match_id} not in the match list around {around}")
    teams = (match.home.match_team_id, match.away.match_team_id)
    s = client.session
    return MatchState(
        match=dict(match.raw),
        events=list(s.call("GetMatchhandelselista", {"matchid": match_id})),
        results=list(s.call("GetMatchresultatlista", {"matchid": match_id})),
        lineups={t: list(s.call("GetMatchdeltagareListaForMatchlag", {"matchlagid": t})) for t in teams},
        officials={t: list(s.call("GetMatchlagledareListaForMatchlag", {"matchlagid": t})) for t in teams},
    )


def event_signature(e: dict[str, Any]) -> tuple[Any, ...]:
    """What an event *is*, without its id (ids change when an event is recreated)."""
    return (
        e["matchhandelsetypid"],
        e.get("matchlagid"),
        e.get("spelareid"),
        e.get("matchdeltagareid"),
        e.get("tidsangivelse"),
        e.get("period"),
        e.get("matchminut"),
        e.get("hemmamal"),
        e.get("bortamal"),
        e.get("planpositionx"),
        e.get("planpositiony"),
    )


def differences(before: MatchState, after: MatchState, *, compare_event_ids: bool = True) -> list[str]:
    """Human-readable differences; empty = equivalent."""
    out: list[str] = []
    if compare_event_ids:
        b_ids = {e["matchhandelseid"]: e for e in before.events}
        a_ids = {e["matchhandelseid"]: e for e in after.events}
        out += [
            f"event {i} missing: {event_signature(b_ids[i])}" for i in sorted(b_ids.keys() - a_ids.keys())
        ]
        out += [f"event {i} extra: {event_signature(a_ids[i])}" for i in sorted(a_ids.keys() - b_ids.keys())]
        out += [
            f"event {i} changed: {event_signature(b_ids[i])} -> {event_signature(a_ids[i])}"
            for i in sorted(b_ids.keys() & a_ids.keys())
            if event_signature(b_ids[i]) != event_signature(a_ids[i])
        ]
    else:
        b_sig = sorted(map(event_signature, before.events), key=repr)
        a_sig = sorted(map(event_signature, after.events), key=repr)
        out += [f"event missing: {s}" for s in b_sig if b_sig.count(s) > a_sig.count(s)]
        out += [f"event extra: {s}" for s in a_sig if a_sig.count(s) > b_sig.count(s)]
        out = sorted(set(out))

    def rows(state: MatchState) -> dict[int, tuple[Any, ...]]:
        return {r["matchresultattypid"]: tuple(r.get(f) for f in RESULT_FIELDS) for r in state.results}

    br, ar = rows(before), rows(after)
    out += [
        f"result type {t}: {br.get(t)} -> {ar.get(t)}"
        for t in sorted(br.keys() | ar.keys())
        if br.get(t) != ar.get(t)
    ]

    def officials(state: MatchState) -> dict[tuple[int, int], tuple[Any, ...]]:
        # Keyed by person and role: clearing discipline re-creates the record with a new id.
        return {
            (r["personid"], r["lagrollid"]): tuple(r.get(f) for f in OFFICIAL_FIELDS)
            for rows in state.officials.values()
            for r in rows
        }

    bo, ao = officials(before), officials(after)
    out += [
        f"official {i}: {bo.get(i)} -> {ao.get(i)}"
        for i in sorted(bo.keys() | ao.keys())
        if bo.get(i) != ao.get(i)
    ]

    def lineup(state: MatchState) -> dict[int, tuple[Any, ...]]:
        return {
            r["matchdeltagareid"]: tuple(r.get(f) for f in LINEUP_FIELDS)
            for rows in state.lineups.values()
            for r in rows
        }

    bl, al = lineup(before), lineup(after)
    out += [
        f"player {k}: {bl.get(k)} -> {al.get(k)}"
        for k in sorted(bl.keys() | al.keys())
        if bl.get(k) != al.get(k)
    ]
    out += [
        f"match {f}: {before.match.get(f)!r} -> {after.match.get(f)!r}"
        for f in MATCH_FIELDS
        if before.match.get(f) != after.match.get(f)
    ]
    return out
