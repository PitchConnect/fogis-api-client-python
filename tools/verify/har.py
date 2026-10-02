"""Compare a browser recording (HAR) of normal reporting with what the library would send.

    uv run python -m tools.verify.har path/to/recording.har [--out .verify/har]

For every MatchWebMetoder call in the recording: method, request payload, status and the shape of `d`.
For every event saved (SparaMatchhandelse) the library's payload is rebuilt from the same match, line-up and
the event as stored afterwards, and compared field by field. Output: calls.jsonl (full data, stays local) and
a printed summary. The summary shows field names, types and differences, not personal values.
"""

from __future__ import annotations

import argparse
import base64
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fogis_api_client import FogisClient
from fogis_api_client.models import LineupEntry, Match, MatchEvent
from fogis_api_client.writes import DryRun

API = "/MatchWebMetoder.aspx/"


@dataclass
class Call:
    method: str
    request: dict[str, Any]
    status: int
    d: Any


def read_har(path: Path) -> list[Call]:
    har = json.loads(path.read_text(encoding="utf-8"))
    calls = []
    for entry in har["log"]["entries"]:
        url = entry["request"]["url"]
        if API not in url:
            continue
        method = url.split(API, 1)[1].split("?")[0]
        text = (entry["request"].get("postData") or {}).get("text") or "{}"
        try:
            request = json.loads(text)
        except ValueError:
            request = {"_unparsed": text}  # SparaPubliksiffra is built by string concatenation in the app
        content = entry["response"].get("content") or {}
        body = content.get("text")
        if body and content.get("encoding") == "base64":
            body = base64.b64decode(body).decode("utf-8", "replace")
        try:
            d = json.loads(body)["d"] if body else None
        except (ValueError, KeyError, TypeError):
            d = {"_unparsed": (body or "")[:200]}
        calls.append(Call(method, request, entry["response"]["status"], d))
    return calls


def snapshot_calls(path: Path) -> list[Call]:
    """Pretend the snapshot's reads were part of the recording (for recordings that skip the match list)."""
    snap = json.loads(path.read_text(encoding="utf-8"))
    calls = [Call("GetMatcherAttRapportera", {}, 200, {"matchlista": [snap["match"]]})]
    calls += [
        Call("GetMatchdeltagareListaForMatchlag", {"matchlagid": int(k)}, 200, v)
        for k, v in snap["lineups"].items()
    ]
    return calls


def shape(v: Any, depth: int = 0) -> Any:
    if isinstance(v, dict):
        return {k: shape(x, depth + 1) for k, x in v.items()} if depth < 2 else "dict"
    if isinstance(v, list):
        return [shape(v[0], depth + 1)] if v else []
    return type(v).__name__


def library_payload(call: Call, calls: list[Call]) -> dict[str, Any] | str:
    """What FogisClient would send for the same event, or why it can't be rebuilt."""
    p = call.request
    matches = {
        m["matchid"]: m
        for c in calls
        if c.method == "GetMatcherAttRapportera" and isinstance(c.d, dict)
        for m in c.d.get("matchlista", [])
    }
    raw_match = matches.get(p.get("matchid"))
    if raw_match is None:
        return "match not in the recording (open the match list first)"
    match = Match.from_api(raw_match)
    players = {
        r["matchdeltagareid"]: LineupEntry.from_api(r)
        for c in calls
        if c.method == "GetMatchdeltagareListaForMatchlag" and isinstance(c.d, list)
        for r in c.d
    }
    stored = [
        MatchEvent.from_api(e)
        for c in calls
        if c.method in ("GetMatchhandelselista", "SparaMatchhandelse") and isinstance(c.d, list)
        for e in c.d
    ]
    event_type = p["matchhandelsetypid"]
    wanted_player = p.get("spelareid") or None
    candidates = [
        e
        for e in stored
        if (e.type_id == event_type or (event_type == 17 and e.type_id == 17))
        and e.match_team_id == (p.get("matchlagid") or None)
        and e.player_id == wanted_player
        and (e.period == p["period"] or e.period == 0)
    ]
    if not candidates:
        return "event not found in any later event list of the recording"
    e = candidates[-1]
    client = FogisClient(session=None, dry_run=True)  # type: ignore[arg-type]
    player = players.get(p.get("matchdeltagareid"))
    if event_type == 17 and p.get("spelareid2"):
        out = players.get(p.get("matchdeltagareid2"))
        if player is None or out is None:
            return "substitution players not in a recorded line-up"
        r = client.substitute(match, e.time_text, team_id=p["matchlagid"], player_in=player, player_out=out)
    else:
        score = (p["hemmamal"], p["bortamal"]) if p["hemmamal"] or p["bortamal"] else None
        pos = None
        if str(p.get("planpositionx")) not in ("-1", "", "None"):
            pos = (int(p["planpositionx"]), int(p["planpositiony"]))
        try:
            r = client.save_match_event(
                match,
                event_type,
                e.time_text,
                team_id=p.get("matchlagid") or 0,
                player=player,
                score=score,
                position=pos,
                event_id=p.get("matchhandelseid", 0),
            )
        except ValueError as err:
            return f"library refused: {err}"
    assert isinstance(r, DryRun)
    return dict(r.payload)


def compare(app: dict[str, Any], lib: dict[str, Any]) -> list[str]:
    out = []
    for k in sorted(app.keys() | lib.keys()):
        a, b = app.get(k, "<missing>"), lib.get(k, "<missing>")
        if a != b and str(a) != str(b):
            out.append(f"{k}: app {a!r} ({type(a).__name__}) vs library {b!r} ({type(b).__name__})")
        elif type(a) is not type(b):
            out.append(f"{k}: same value, app sends {type(a).__name__}, library {type(b).__name__}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("har", type=Path)
    ap.add_argument("--out", type=Path, default=Path(".verify/har"))
    ap.add_argument(
        "--snapshot", type=Path, help="a runner snapshot (before.json) for the match and line-ups"
    )
    a = ap.parse_args(argv)
    calls = read_har(a.har)
    if a.snapshot:
        calls = [*snapshot_calls(a.snapshot), *calls]
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "calls.jsonl").write_text(
        "".join(json.dumps(c.__dict__, ensure_ascii=False) + "\n" for c in calls), encoding="utf-8"
    )
    print(
        f"{len(calls)} API calls: "
        + ", ".join(f"{m} x{n}" for m, n in Counter(c.method for c in calls).items())
    )
    for c in calls:
        if c.method.startswith(("Get", "hamta", "Sok")):
            continue
        print(f"\n## {c.method} → HTTP {c.status}")
        print("   request fields:", {k: type(v).__name__ for k, v in c.request.items()})
        print("   response d:", json.dumps(shape(c.d)))
        if c.method == "SparaMatchhandelse":
            lib = library_payload(c, calls)
            if isinstance(lib, str):
                print("   library comparison skipped:", lib)
            else:
                diffs = compare(c.request, lib)
                print("   library payload:", "IDENTICAL" if not diffs else "DIFFERS")
                for d in diffs:
                    print("     -", d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
