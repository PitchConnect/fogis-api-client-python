"""Unattended verification of the write side on one open, unsubmitted match (FOGIS_API.md §10).

    uv run --env-file .env python -m tools.verify.runner --match ID --date YYYY-MM-DD \\
        [--rehearse] [--no-rebuild]

1. Snapshot the match (events, results, line-ups, officials). Refuse unless the report is open and
   unsubmitted.
2. Run each checklist step: test events on top of the real report, observations recorded, test data deleted.
   After every step the whole match is compared with the snapshot; any difference triggers a restore, and a
   failed restore aborts everything.
3. Finally (unless --no-rebuild) delete every event and rebuild the report from the snapshot.
4. Write report.md, findings.json, responses.jsonl and the snapshots to .verify/<match>-<time>/.

--rehearse reads the real match once and then runs everything against an in-memory fake FOGIS seeded with it:
no writes at all. The report is never submitted: the two irreversible calls raise in this client.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import traceback
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from fogis_api_client import FogisClient, FogisSession
from fogis_api_client.enums import EventType, ResultType
from fogis_api_client.models import LineupEntry, Match, MatchEvent, TeamOfficial
from fogis_api_client.timeline import (
    Substitution,
    classify_second_caution_sending_offs,
    pair_substitutions,
    penalty_awards,
)
from fogis_api_client.writes import SCORE_TYPES, next_score

from .state import LINEUP_FIELDS, MatchState, differences, take_snapshot

log = logging.getLogger("verify")

SERVER_COMMENT_UNKNOWN_PLAYER = "Okänd spelare"


class Abort(Exception):
    """Stop the run: the match could not be brought back to the snapshot."""


class SafeClient(FogisClient):
    """FogisClient that records every write response and can never lock the match."""

    responses: list[dict[str, Any]]

    def mark_reporting_finished(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("the verification runner never submits the report")

    def end_live_reporting(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("the verification runner never ends live reporting")

    def _send(self, method: str, payload: Mapping[str, Any]) -> Any:
        d = super()._send(method, payload)
        self.responses.append(
            {
                "t": datetime.now().isoformat(timespec="seconds"),
                "method": method,
                "payload": dict(payload),
                "d": d,
            }
        )
        return d


@dataclass
class Ctx:
    client: SafeClient
    before: MatchState
    around: date
    findings: dict[str, Any] = field(default_factory=dict)

    @property
    def match(self) -> Match:
        return self.before.model

    def now(self) -> MatchState:
        return take_snapshot(self.client, self.before.match["matchid"], self.around)

    def new_events(self) -> list[MatchEvent]:
        known = {e["matchhandelseid"] for e in self.before.events}
        events = self.client.events(self.before.match["matchid"])
        return sorted((e for e in events if e.event_id not in known), key=lambda e: e.event_id)

    def delete_new_events(self) -> None:
        for e in reversed(self.new_events()):
            self.client.delete_match_event(e.event_id)


def describe(e: MatchEvent) -> dict[str, Any]:
    return {
        "id": e.event_id,
        "type": e.type_id,
        "period": e.period,
        "minute": e.minute,
        "time_text": e.time_text,
        "related": e.related_event_id,
        "score": [e.home_goals, e.away_goals],
        "player": e.player_id,
    }


# ---------------------------------------------------------------------------- choosing test subjects


def quiet_players(ctx: Ctx) -> tuple[LineupEntry, LineupEntry, LineupEntry]:
    """Two starters and one unused substitute of the same team, none with any event in the real report.

    Home team preferred; the choice is kept in ctx.findings so every step uses the same players.
    """
    chosen = ctx.findings.get("_players")
    if chosen is not None:
        return chosen  # type: ignore[no-any-return]
    events = ctx.before.event_models()
    busy = {e.participant_id for e in events} | {e.player_id for e in events}
    for team in (ctx.match.home.match_team_id, ctx.match.away.match_team_id):
        free = [
            p
            for p in ctx.before.players()
            if p.match_team_id == team
            and p.participant_id not in busy
            and p.player_id not in busy
            and not p.substitution_minutes
        ]
        starters = [p for p in free if not p.substitute and p.raw.get("lagdelid") != 1]
        subs = [p for p in free if p.substitute and p.raw.get("lagdelid") != 1]  # no goalkeepers
        if len(starters) >= 2 and subs:
            ctx.findings["_players"] = (starters[0], starters[1], subs[0])
            return ctx.findings["_players"]  # type: ignore[no-any-return]
    raise Abort("no team has two starters and one substitute without events to test on")


def clean_official(ctx: Ctx) -> TeamOfficial:
    for o in ctx.before.official_models():
        if not (o.cautioned or o.sent_off):
            return o
    raise Abort("no team official without discipline to test on")


# ---------------------------------------------------------------------------- checklist steps


def step_basic_caution(ctx: Ctx) -> dict[str, Any]:
    """Save, edit and delete one caution; the library's encoding must be what FOGIS stores."""
    a, _, _ = quiet_players(ctx)
    c, m = ctx.client, ctx.match
    c.save_match_event(m, EventType.VARNING, "30", team_id=a.match_team_id, player=a)
    new = ctx.new_events()
    assert [(e.type_id, e.period, e.minute, e.time_text) for e in new] == [(20, 1, 30, "30")], new
    c.save_match_event(
        m, EventType.VARNING, "31", team_id=a.match_team_id, player=a, event_id=new[0].event_id
    )
    edited = ctx.new_events()
    assert [(e.event_id, e.time_text) for e in edited] == [(new[0].event_id, "31")], edited
    c.delete_match_event(new[0].event_id)
    assert ctx.new_events() == []
    return {"saved": describe(new[0]), "edited": describe(edited[0])}


def step_goal_subtypes(ctx: Ctx) -> dict[str, Any]:
    """§10.1: how a headed goal is stored (rendering on the public web: check by hand).

    Types 1 and 7 are no longer tested: on 2026-09-30 they became hidden yellow cards (FOGIS_API.md §6).
    """
    a, _, _ = quiet_players(ctx)
    c, m, team = ctx.client, ctx.match, quiet_players(ctx)[0].match_team_id
    score = next_score(ctx.client.events(m.match_id), m, team)
    c.save_match_event(m, EventType.NICKMAL, "33", team_id=team, player=a, score=score)
    stored = [describe(e) | {"name": e.type_name} for e in ctx.new_events()]
    ctx.delete_new_events()
    return {"stored": stored, "score_sent": list(score)}


def step_second_caution(ctx: Ctx) -> dict[str, Any]:
    """§10.2/10.3: two cautions -> automatic #2? Deleting the 2nd caution -> does the #2 stay?"""
    a, _, _ = quiet_players(ctx)
    c, m, team = ctx.client, ctx.match, quiet_players(ctx)[0].match_team_id
    c.save_match_event(m, EventType.VARNING, "34", team_id=team, player=a)
    c.save_match_event(m, EventType.VARNING, "36", team_id=team, player=a)
    after_two = ctx.new_events()
    second = max((e for e in after_two if e.type_id == 20), key=lambda e: e.event_id)
    c.delete_match_event(second.event_id)
    after_delete = ctx.new_events()
    ctx.delete_new_events()
    return {
        "after_two_cautions": [describe(e) for e in after_two],
        "after_deleting_second": [describe(e) for e in after_delete],
    }


def step_added_time(ctx: Ctx) -> dict[str, Any]:
    """§10.5: what FOGIS stores for each way of typing added time."""
    _, b, _ = quiet_players(ctx)
    c, m, team = ctx.client, ctx.match, quiet_players(ctx)[0].match_team_id
    out = {}
    for text in ("45+2", "47", "45", "90+3", "91"):
        sent = c.save_match_event(m, EventType.VARNING, text, team_id=team, player=b)
        out[text] = {"stored": [describe(e) for e in ctx.new_events()], "response": repr(sent)[:200]}
        ctx.delete_new_events()
    return out


def step_substitution(ctx: Ctx) -> dict[str, Any]:
    """§10.9: one-call substitution -> 16 + linked 17? Deleting the 17 -> does the 16 stay?"""
    a, _, sub = quiet_players(ctx)
    c, m = ctx.client, ctx.match
    c.substitute(m, "60", team_id=a.match_team_id, player_in=sub, player_out=a)
    created = ctx.new_events()
    types = sorted(e.type_id for e in created)
    assert types == [16, 17], created
    on = next(e for e in created if e.type_id == 17)
    c.delete_match_event(on.event_id)
    left = ctx.new_events()
    ctx.delete_new_events()
    return {"created": [describe(e) for e in created], "after_deleting_on": [describe(e) for e in left]}


def step_substitution_edit(ctx: Ctx) -> dict[str, Any]:
    """§10.15: edit a substitution in place (minute, then outgoing player) — ids and link kept?"""
    a, b, sub = quiet_players(ctx)
    c, m = ctx.client, ctx.match

    def pair() -> Substitution:
        return next(s for s in pair_substitutions(ctx.new_events()) if s.on is not None)

    c.substitute(m, "60", team_id=a.match_team_id, player_in=sub, player_out=a)
    first = pair()
    ids = (first.off.event_id if first.off else None, first.on.event_id if first.on else None)
    c.edit_substitution(m, first, time="62")
    moved = pair()
    c.edit_substitution(m, moved, player_out=b)
    swapped = pair()
    out = {
        "created": [describe(e) for e in ctx.new_events()],
        "after_time_edit": [describe(e) for e in (moved.off, moved.on) if e],
        "after_player_edit": [describe(e) for e in (swapped.off, swapped.on) if e],
        "ids_kept": ids
        == (swapped.off.event_id if swapped.off else None, swapped.on.event_id if swapped.on else None),
        "linked": swapped.pairing == "linked",
        "out_player_is_b": swapped.off is not None and swapped.off.player_id == b.player_id,
        "time_is_62": all(e.time_text == "62" for e in (swapped.off, swapped.on) if e),
    }
    ctx.delete_new_events()
    return out


def step_penalty(ctx: Ctx) -> dict[str, Any]:
    """§10.10: penalty goal -> automatic #3? Deleting the goal -> does the #3 stay?"""
    a, _, _ = quiet_players(ctx)
    c, m, team = ctx.client, ctx.match, quiet_players(ctx)[0].match_team_id
    score = next_score(ctx.client.events(m.match_id), m, team)
    c.save_match_event(m, EventType.STRAFFMAL, "70", team_id=team, player=a, score=score)
    created = ctx.new_events()
    goal = next((e for e in created if e.type_id == 14), None)
    left = []
    if goal is not None:
        c.delete_match_event(goal.event_id)
        left = ctx.new_events()
    ctx.delete_new_events()
    return {"created": [describe(e) for e in created], "after_deleting_goal": [describe(e) for e in left]}


def step_official_discipline(ctx: Ctx) -> dict[str, Any]:
    """§10.6: caution at 30; then only a minor sending-off at 80 (is the caution kept?); then clear it all."""
    o = clean_official(ctx)
    c = ctx.client

    def read(official_id: int) -> dict[str, Any]:
        rows = c.session.call("GetMatchlagledareListaForMatchlag", {"matchlagid": o.match_team_id})
        return next(r for r in rows if r["matchlagledareid"] == official_id)

    keys = (
        "varnad",
        "varnadmatchminut",
        "avvisadlindrig",
        "avvisadgrov",
        "avvisadmatchminut",
        "lagrollid",
        "ansvarig",
    )
    out: dict[str, Any] = {}
    c.save_official_discipline(o, minute=30, caution=True)
    out["caution_30"] = {k: read(o.official_id).get(k) for k in keys}
    c.save_official_discipline(o, minute=80, sending_off="minor")  # like the app: one option per save
    current = read(o.official_id)
    out["caution_and_minor_80"] = {k: current.get(k) for k in keys}
    new = c.clear_official_discipline(TeamOfficial.from_api(current))
    out["cleared"] = {k: read(new.official_id).get(k) for k in keys} | {
        "new_record": new.official_id != o.official_id
    }
    return out


def step_lineup_changes(ctx: Ctx) -> dict[str, Any]:
    """§10.13: new shirt number (torn shirt); bench -> starting eleven (warm-up injury); both restored."""
    a, _, sub = quiet_players(ctx)
    c = ctx.client

    def read(p: LineupEntry) -> LineupEntry:
        rows = c.session.call("GetMatchdeltagareListaForMatchlag", {"matchlagid": p.match_team_id})
        return LineupEntry.from_api(next(r for r in rows if r["matchdeltagareid"] == p.participant_id))

    taken = {p.shirt_number for p in ctx.before.players() if p.match_team_id == a.match_team_id}
    free = next(n for n in range(99, 0, -1) if n not in taken)
    out: dict[str, Any] = {"free_number": free}
    c.save_match_participant(a, shirt_number=free)
    changed = read(a)
    out["shirt_changed"] = {"shirt": changed.shirt_number, "substitute": changed.substitute}
    restore_exactly(ctx, a)
    out["shirt_restored"] = read(a).raw == a.raw

    c.save_match_participant(sub, substitute=False)
    started = read(sub)
    out["bench_to_start"] = {
        "substitute": started.substitute,
        "position": started.raw.get("positionsnummerhv"),
    }
    c.save_match_participant(started, substitute=True)
    back = read(sub)
    out["back_on_bench_by_app_rules"] = {
        "substitute": back.substitute,
        "position": back.raw.get("positionsnummerhv"),
        "position_before": sub.raw.get("positionsnummerhv"),
    }
    restore_exactly(ctx, sub)  # the app's rules give a bench player position -1; old data may hold 0
    out["start_restored"] = read(sub).raw == sub.raw
    return out


def restore_exactly(ctx: Ctx, p: LineupEntry) -> None:
    """Re-send a line-up entry with exactly the snapshot's values (not the app's form rules)."""
    ctx.client._write("SparaMatchdeltagare", {k: p.raw.get(k) for k in ("matchdeltagareid", *LINEUP_FIELDS)})


def step_result_minus_one(ctx: Ctx) -> dict[str, Any]:
    """§10.7: a result row with (-1, -1) — does it clear the row? Restored afterwards."""
    rows = {r["matchresultattypid"]: r for r in ctx.before.results}
    half = rows.get(ResultType.HALVTIDSRESULTAT)
    if half is None:
        return {"skipped": "no half-time row to test on"}
    c, match_id = ctx.client, ctx.match.match_id
    c.report_match_result(match_id, {ResultType.HALVTIDSRESULTAT: (-1, -1)})
    after = [r for r in c.session.call("GetMatchresultatlista", {"matchid": match_id})]
    c.report_match_result(
        match_id, {ResultType.HALVTIDSRESULTAT: (half["matchlag1mal"], half["matchlag2mal"])}
    )
    return {"after_minus_one": after}


def step_idempotent_match_fields(ctx: Ctx) -> dict[str, Any]:
    """Re-send attendance and referee note unchanged; record the response shapes."""
    c, m = ctx.client, ctx.before.match
    r1 = c.save_attendance(m["matchid"], m.get("antalaskadare", 0))
    r2 = c.save_referee_note(m["matchid"], m.get("noteringfrandomare", ""))
    return {"attendance_response": repr(r1)[:300], "note_response": repr(r2)[:300]}


STEPS: list[Callable[[Ctx], dict[str, Any]]] = [
    step_basic_caution,
    step_goal_subtypes,
    step_second_caution,
    step_added_time,
    step_substitution,
    step_substitution_edit,
    step_penalty,
    step_official_discipline,
    step_lineup_changes,
    step_result_minus_one,
    step_idempotent_match_fields,
]


# ---------------------------------------------------------------------------- restore and rebuild


def restore(ctx: Ctx) -> list[str]:
    """Bring the match back to the snapshot; returns the remaining differences (empty = restored)."""
    ctx.delete_new_events()
    now = ctx.now()
    before_ids = {e["matchhandelseid"] for e in ctx.before.events}
    if before_ids - {e["matchhandelseid"] for e in now.events}:
        return differences(ctx.before, now)  # real events gone: only a rebuild can help; report instead
    current = {r["matchresultattypid"]: r for r in now.results}
    changed = {
        r["matchresultattypid"]: (r["matchlag1mal"], r["matchlag2mal"])
        for r in ctx.before.results
        if (current.get(r["matchresultattypid"]) or {}).get("matchlag1mal") != r["matchlag1mal"]
        or (current.get(r["matchresultattypid"]) or {}).get("matchlag2mal") != r["matchlag2mal"]
    }
    if changed:
        ctx.client.report_match_result(ctx.match.match_id, changed)
    now_officials = {(o.person_id, o.role_id): o for o in now.official_models()}
    for o in ctx.before.official_models():
        cur = now_officials.get((o.person_id, o.role_id))
        if cur is None or (cur.cautioned, cur.sent_off) == (o.cautioned, o.sent_off):
            continue
        if not (o.cautioned or o.sent_off):  # test discipline on an official who had none: remove it
            ctx.client.clear_official_discipline(cur)
        # real discipline that got lost cannot be restored safely here; the final report shows it
    now_players = {p.participant_id: p for p in now.players()}
    for p in ctx.before.players():
        cur = now_players.get(p.participant_id)
        if cur is not None and cur.raw != p.raw:
            restore_exactly(ctx, p)
    m = ctx.before.match
    if now.match.get("antalaskadare") != m.get("antalaskadare"):
        ctx.client.save_attendance(m["matchid"], m.get("antalaskadare", 0))
    if now.match.get("noteringfrandomare") != m.get("noteringfrandomare"):
        ctx.client.save_referee_note(m["matchid"], m.get("noteringfrandomare", ""))
    return differences(ctx.before, ctx.now())


def rebuild(ctx: Ctx) -> dict[str, Any]:
    """Delete every event and recreate the report from the snapshot, oldest first."""
    events = ctx.before.event_models()
    # FOGIS writes "Okänd spelare" itself on a goal saved without a player; only other comments are a problem.
    if any(e.comment and e.comment != SERVER_COMMENT_UNKNOWN_PLAYER for e in events):
        return {"skipped": "events carry comments, which the app's payload cannot re-create"}
    c, m = ctx.client, ctx.match
    by_participant = {p.participant_id: p for p in ctx.before.players()}
    second = classify_second_caution_sending_offs(events)
    awards = {a.award.event_id for a in penalty_awards(events) if a.outcome is not None}
    subs = {s.on.event_id: s for s in pair_substitutions(events) if s.on is not None and s.off is not None}
    paired_offs = {s.off.event_id for s in subs.values() if s.off is not None}
    not_recreated = [describe(e) for e in events if e.type_id == 2 and second.get(e.event_id) == "orphan"]

    for e in sorted(c.events(m.match_id), key=lambda e: e.event_id, reverse=True):
        c.delete_match_event(e.event_id)
    if c.events(m.match_id):
        raise Abort("events left after deleting all")

    for e in sorted(events, key=lambda e: e.event_id):
        if e.type_id == 2 or e.event_id in awards or e.event_id in paired_offs:
            continue  # created by the server (#2, #3) or by the substitution call (16)
        player = by_participant.get(e.participant_id) if e.participant_id else None
        if e.type_id == EventType.BYTE_IN:
            s = subs.get(e.event_id)
            if s is None or s.off is None or player is None or s.off.participant_id not in by_participant:
                not_recreated.append(describe(e))
                continue
            c.substitute(
                m,
                e.time_text,
                team_id=e.match_team_id or 0,
                player_in=player,
                player_out=by_participant[s.off.participant_id],
            )
            continue
        if e.type_id == EventType.BYTE_UT:
            not_recreated.append(describe(e))
            continue
        c.save_match_event(
            m,
            e.type_id,
            e.time_text,
            team_id=e.match_team_id or 0,
            player=player,
            score=(e.home_goals, e.away_goals) if e.type_id in SCORE_TYPES else None,
            position=(e.position_x, e.position_y)
            if e.position_x is not None and e.position_y is not None
            else None,
        )
    return {"not_recreated": not_recreated}


# ---------------------------------------------------------------------------- the run


def check_open(state: MatchState, now: datetime) -> None:
    m = state.model
    if m.report_approved or state.match.get("liverapporteringAvslutad"):
        raise Abort("the report is already submitted or live reporting has ended")
    if m.kickoff is None:
        raise Abort("match has no kick-off time")
    closes = m.kickoff + timedelta(
        days=state.match.get("tavlingAntalDagarEfterMatchForAdministrationAvDomarrapport", 0)
    )
    if not (m.kickoff <= now <= closes - timedelta(hours=2)):
        raise Abort(f"not inside the reporting window with a 2 h margin (closes {closes:%Y-%m-%d %H:%M})")


def run(
    client: SafeClient,
    match_id: int,
    around: date,
    out: Path,
    *,
    rebuild_report: bool = True,
    steps: list[Callable[[Ctx], dict[str, Any]]] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    client.responses = []
    before = take_snapshot(client, match_id, around)
    before.save(out / "before.json")
    ctx = Ctx(client, before, around)
    summary: dict[str, Any] = {"match_id": match_id, "steps": {}, "aborted": None}
    try:
        check_open(before, now or datetime.now().astimezone())
        for step in steps if steps is not None else STEPS:
            name = step.__name__.removeprefix("step_")
            entry: dict[str, Any] = {}
            try:
                entry["findings"] = step(ctx)
                entry["ok"] = True
            except Abort:
                raise
            except Exception as e:
                entry["ok"] = False
                entry["error"] = "".join(traceback.format_exception_only(e)).strip()
            left = differences(before, ctx.now())
            if left:
                entry["left_behind"] = left
                try:
                    remaining = restore(ctx)
                except Exception as e:
                    summary["steps"][name] = entry
                    raise Abort(f"restore after {name} failed: {e}") from e
                entry["restored"] = not remaining
                if remaining:
                    summary["steps"][name] = entry
                    raise Abort(f"could not restore after {name}: {remaining}")
            summary["steps"][name] = entry
            log.info("step %s: %s", name, "ok" if entry["ok"] else entry["error"])
        if rebuild_report:
            summary["rebuild"] = {"started": True}
            summary["rebuild"] = rebuild(ctx)
            if "skipped" not in summary["rebuild"]:
                summary["rebuild"]["differences"] = differences(before, ctx.now(), compare_event_ids=False)
    except Abort as e:
        summary["aborted"] = str(e)
    except Exception as e:
        summary["aborted"] = "".join(traceback.format_exception_only(e)).strip()
    finally:
        rebuilt = "rebuild" in summary and "skipped" not in summary["rebuild"]
        try:
            after = ctx.now()
            after.save(out / "after.json")
            summary["final_differences"] = differences(before, after, compare_event_ids=not rebuilt)
        except Exception as e:
            summary["final_differences"] = [f"could not read the final state: {e}"]
        (out / "responses.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False, default=repr) + "\n" for r in client.responses),
            encoding="utf-8",
        )
        (out / "findings.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=1, default=repr), encoding="utf-8"
        )
        (out / "report.md").write_text(render_report(summary), encoding="utf-8")
    return summary


def render_report(summary: dict[str, Any]) -> str:
    lines = [f"# Write verification, match {summary['match_id']}", ""]
    final = summary.get("final_differences") or []
    lines.append("**Final state: identical to the snapshot.**" if not final else "**Final state DIFFERS:**")
    lines += [f"- {d}" for d in final]
    if summary.get("aborted"):
        lines += ["", f"**Aborted:** {summary['aborted']}"]
    lines += ["", "| Step | Result | Left behind | Restored |", "|---|---|---|---|"]
    for name, e in summary["steps"].items():
        result = "ok" if e["ok"] else f"error: {e.get('error', '')[:120]}"
        lines.append(f"| {name} | {result} | {len(e.get('left_behind', []))} | {e.get('restored', '-')} |")
    if "rebuild" in summary:
        lines += [
            "",
            "## Rebuild",
            "```",
            json.dumps(summary["rebuild"], ensure_ascii=False, indent=1),
            "```",
        ]
    lines += [
        "",
        "Observations per step are in findings.json; every write and its response in responses.jsonl.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--match", type=int, required=True)
    p.add_argument("--date", type=date.fromisoformat, required=True, help="the match date")
    p.add_argument("--rehearse", action="store_true", help="read once, then run against a fake FOGIS")
    p.add_argument("--no-rebuild", action="store_true")
    p.add_argument("--out", type=Path, default=Path(".verify"))
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    session = FogisSession(
        os.environ["FOGIS_USERNAME"],
        os.environ["FOGIS_PASSWORD"],
        cookie_file=a.out / "cookies.json",
        min_interval=1.0,
    )
    a.out.mkdir(parents=True, exist_ok=True)
    now = None
    if a.rehearse:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
        from fake_fogis import FakeFogis

        real = take_snapshot(FogisClient(session=session), a.match, a.date)
        fake = FakeFogis(real.match, real.events, real.lineups, real.officials, real.results)
        fake.match.update(matchrapportgodkandavdomare=False, liverapporteringAvslutad=False)
        client = SafeClient(session=fake)  # type: ignore[arg-type]
        m = real.model
        now = m.kickoff + timedelta(hours=10) if m.kickoff else None
    else:
        client = SafeClient(session=session)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = a.out / f"{a.match}-{stamp}{'-rehearsal' if a.rehearse else ''}"
    summary = run(client, a.match, a.date, out, rebuild_report=not a.no_rebuild, now=now)
    print((out / "report.md").read_text(encoding="utf-8"))
    return 0 if not summary["aborted"] and not summary["final_differences"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
