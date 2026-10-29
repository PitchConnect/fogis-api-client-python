"""`fogis`: read-only command line access to your FOGIS matches.

Prints JSON by default (--table for people). Never writes to FOGIS; use the library for that.
Credentials come from the macOS Keychain or the environment (see credentials.py); the cookie jar and the
cache of approved reports live in ~/.config/fogis and ~/.cache/fogis (see store.py).
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import date, timedelta
from typing import IO, Any

from .. import __version__
from ..checks import check_report
from ..client import FogisClient
from ..errors import FogisError, FogisInvalidCredentialsError
from ..models import LineupEntry, Match, TeamOfficial
from ..timeline import TimelineEntry, build_timeline, pair_substitutions
from .credentials import CredentialsError, find_credentials
from .output import Column, clock, write_json, write_table
from .store import MatchCache, MatchData, cache_dir, config_dir, ensure_dir, find_match

BUNDLE_VERSION = 1


class Context:
    """What a command needs, created on first use so that `fogis --help` touches nothing."""

    def __init__(
        self, args: argparse.Namespace, env: Mapping[str, str], out: IO[str], client: FogisClient | None
    ) -> None:
        self.args = args
        self.env = env
        self.out = out
        self.cache = MatchCache(cache_dir(env))
        self._client = client
        self.username = ""
        self.credentials_source = ""

    @property
    def client(self) -> FogisClient:
        if self._client is None:
            creds = find_credentials(self.env)
            self.username, self.credentials_source = creds.username, creds.source
            cookie_file = ensure_dir(config_dir(self.env)) / "cookies.json"
            self._client = FogisClient(creds.username, creds.password, cookie_file=cookie_file)
        return self._client

    def match_data(self) -> MatchData:
        args = self.args
        raw = find_match(self.client, self.cache, args.match_id, on=args.date, refresh=args.refresh)
        return MatchData(self.client, self.cache, raw, refresh=args.refresh)

    def emit(self, value: Any, rows: Sequence[Any] | None = None, columns: Sequence[Column] = ()) -> None:
        if self.args.table and columns:
            write_table(value if rows is None else rows, columns, self.out)
        else:
            write_json(value, self.out, raw=getattr(self.args, "raw", False))


# ---------------------------------------------------------------------------- columns


def _team_names(match: Match) -> dict[int | None, str]:
    return {match.home.match_team_id: match.home.name, match.away.match_team_id: match.away.name}


MATCH_COLUMNS: list[Column] = [
    ("date", lambda m: m.date),
    ("time", lambda m: m.kickoff and m.kickoff.strftime("%H:%M")),
    ("id", lambda m: m.match_id),
    ("match", lambda m: f"{m.home.name} - {m.away.name}"),
    ("score", lambda m: f"{m.home_goals}-{m.away_goals}" if m.result_is_final else ""),
    ("report", lambda m: "approved" if m.report_approved else ""),
    ("competition", lambda m: m.competition_name),
]


def _timeline_columns(match: Match) -> list[Column]:
    names = _team_names(match)

    def who(e: TimelineEntry) -> str:
        if e.official is not None:
            return f"{e.official.first_name} {e.official.last_name} ({e.official.role_name})"
        if e.event is None or e.event.player_name is None:
            return ""
        number = f"#{e.event.shirt_number} " if e.event.shirt_number is not None else ""
        return number + e.event.player_name

    def what(e: TimelineEntry) -> str:
        if e.kind == "official_caution":
            return "Varning (ledare)"
        if e.kind == "official_sending_off":
            return "Utvisning (ledare)"
        return e.event.type_name if e.event is not None else ""

    def notes(e: TimelineEntry) -> str:
        flags = [("score?", e.score_mismatch), ("automatic", e.automatic), ("orphan", e.orphan)]
        flags += [("period inferred", e.period_inferred)]
        return ", ".join(name for name, on in flags if on)

    return [
        ("period", lambda e: e.period),
        ("min", clock),
        ("team", lambda e: names.get(e.match_team_id, "")),
        ("event", what),
        ("who", who),
        ("score", lambda e: e.score and f"{e.score.home}-{e.score.away}"),
        ("notes", notes),
    ]


def _lineup_columns(match: Match) -> list[Column]:
    names = _team_names(match)

    def role(p: LineupEntry) -> str:
        flags = [("C", p.captain), ("sub", p.substitute), ("official", p.playing_official)]
        return " ".join(name for name, on in flags if on)

    return [
        ("team", lambda p: names.get(p.match_team_id, "")),
        ("#", lambda p: p.shirt_number),
        ("name", lambda p: f"{p.first_name} {p.last_name}"),
        ("role", role),
        ("sent off", lambda p: p.sending_off),
    ]


def _officials_columns(match: Match) -> list[Column]:
    names = _team_names(match)

    def discipline(o: TeamOfficial) -> str:
        parts = []
        if o.cautioned:
            parts.append(f"caution {o.caution_minute or ''}".strip())
        if o.sent_off:
            parts.append(f"sent off {o.sending_off_minute or ''}".strip())
        return ", ".join(parts)

    return [
        ("team", lambda o: names.get(o.match_team_id, "")),
        ("name", lambda o: f"{o.first_name} {o.last_name}"),
        ("role", lambda o: o.role_name),
        ("discipline", discipline),
    ]


RESULT_COLUMNS: list[Column] = [
    ("result", lambda r: r.type_name),
    ("score", lambda r: f"{r.home_goals}-{r.away_goals}"),
    ("walkover", lambda r: "yes" if r.walkover else ""),
]

PROBLEM_COLUMNS: list[Column] = [
    ("severity", lambda p: p.severity),
    ("code", lambda p: p.code),
    ("message", lambda p: p.message),
]


# ---------------------------------------------------------------------------- commands


def cmd_login(ctx: Context) -> None:
    client = ctx.client
    renewed = not client.session.is_valid()
    if renewed:
        client.session.renew()
    ctx.emit({"username": ctx.username, "credentials": ctx.credentials_source, "session_renewed": renewed})


def cmd_matches(ctx: Context) -> None:
    a = ctx.args
    if a.season is not None:
        start, end = date(a.season, 1, 1), date(a.season, 12, 31)
    else:
        start = a.start or date.today() - timedelta(days=30)
        end = a.end or date.today() + timedelta(days=30)
    matches = ctx.client.matches(start, end, exclude_statuses=a.exclude or ())
    ctx.cache.remember(matches)
    ctx.emit(matches, columns=MATCH_COLUMNS)


def cmd_match(ctx: Context) -> None:
    data = ctx.match_data()
    ctx.emit(data.match, rows=[data.match], columns=MATCH_COLUMNS)


def cmd_events(ctx: Context) -> None:
    ctx.emit(ctx.match_data().events())  # the raw events; `timeline` is the readable view


def cmd_results(ctx: Context) -> None:
    ctx.emit(ctx.match_data().results(), columns=RESULT_COLUMNS)


def cmd_timeline(ctx: Context) -> None:
    data = ctx.match_data()
    officials = [o for t in data.teams.values() for o in data.officials(t)]
    ctx.emit(build_timeline(data.match, data.events(), officials), columns=_timeline_columns(data.match))


def _per_team(
    ctx: Context, get: Callable[[MatchData, int], list[Any]], columns: Callable[[Match], list[Column]]
) -> None:
    data = ctx.match_data()
    teams = {side: t for side, t in data.teams.items() if ctx.args.team in (None, side)}
    by_side = {side: get(data, t) for side, t in teams.items()}
    rows = [row for side_rows in by_side.values() for row in side_rows]
    ctx.emit(by_side if ctx.args.team is None else rows, rows=rows, columns=columns(data.match))


def cmd_lineup(ctx: Context) -> None:
    _per_team(ctx, MatchData.lineup, _lineup_columns)


def cmd_officials(ctx: Context) -> None:
    _per_team(ctx, MatchData.officials, _officials_columns)


def cmd_check(ctx: Context) -> None:
    ctx.emit(_problems(ctx.match_data()), columns=PROBLEM_COLUMNS)


def _problems(data: MatchData) -> list[Any]:
    officials = [o for t in data.teams.values() for o in data.officials(t)]
    lineup = [p for t in data.teams.values() for p in data.lineup(t)]
    return check_report(data.match, data.events(), data.results(), officials, lineup)


def cmd_bundle(ctx: Context) -> None:
    data = ctx.match_data()
    events = data.events()
    officials = {side: data.officials(t) for side, t in data.teams.items()}
    all_officials = [o for side in officials.values() for o in side]
    ctx.emit(
        {
            "bundle_version": BUNDLE_VERSION,
            "cached_at": data.cached_at,
            "match": data.match,
            "results": data.results(),
            "timeline": build_timeline(data.match, events, all_officials),
            "substitutions": pair_substitutions(events),
            "events": events,
            "lineups": {side: data.lineup(t) for side, t in data.teams.items()},
            "officials": officials,
            "lineup_changes": data.lineup_changes(),
            "problems": _problems(data),
        }
    )


def cmd_cache(ctx: Context) -> None:
    if ctx.args.action == "clear":
        ctx.cache.clear()
        ctx.emit({"cleared": str(ctx.cache.root)})
        return
    entries = [{"match": Match.from_api(e["match"]), "cached_at": e["cached_at"]} for e in ctx.cache.list()]
    columns: list[Column] = [("cached", lambda e: e["cached_at"])]
    columns += [(header, _of_match(get)) for header, get in MATCH_COLUMNS]
    ctx.emit(entries, columns=columns)


def _of_match(get: Callable[[Any], object]) -> Callable[[Any], object]:
    return lambda entry: get(entry["match"])


# ---------------------------------------------------------------------------- parser


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fogis",
        description="Read your matches from FOGIS. Prints JSON; never changes anything in FOGIS.",
        epilog='Credentials: a Keychain item (security add-generic-password -s fogis -a "USERNAME" -w), '
        "or FOGIS_USERNAME and FOGIS_PASSWORD.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True, metavar="COMMAND")

    out = argparse.ArgumentParser(add_help=False)
    out.add_argument("--table", action="store_true", help="a readable table instead of JSON")
    raw = argparse.ArgumentParser(add_help=False)
    raw.add_argument("--raw", action="store_true", help="the records exactly as FOGIS returns them")
    one = argparse.ArgumentParser(add_help=False)
    one.add_argument("match_id", type=int, help="FOGIS match id (matchid)")
    one.add_argument("--date", type=date.fromisoformat, help="the match's date, YYYY-MM-DD; saves a search")
    one.add_argument("--refresh", action="store_true", help="ignore the cache and fetch from FOGIS")
    team = argparse.ArgumentParser(add_help=False)
    team.add_argument("--team", choices=("home", "away"), help="only one team")

    def command(name: str, func: Callable[[Context], None], help: str, *parents: Any) -> Any:
        c = sub.add_parser(name, help=help, description=help, parents=[out, *parents])
        c.set_defaults(func=func)
        return c

    command("login", cmd_login, "check the saved session, logging in if it has expired")
    m = command("matches", cmd_matches, "your matches (default: 30 days back to 30 days ahead)", raw)
    m.add_argument("--from", dest="start", type=date.fromisoformat, metavar="DATE", help="first date")
    m.add_argument("--to", dest="end", type=date.fromisoformat, metavar="DATE", help="last date")
    m.add_argument("--season", type=int, metavar="YEAR", help="the whole calendar year")
    m.add_argument(
        "--exclude", nargs="+", choices=("avbruten", "uppskjuten", "installd"), help="leave these out"
    )
    command("match", cmd_match, "one match", one, raw)
    command("events", cmd_events, "a match's stored events, as FOGIS keeps them", one, raw)
    command("results", cmd_results, "a match's results", one, raw)
    command("timeline", cmd_timeline, "what happened, in order, with official sanctions", one)
    command("lineup", cmd_lineup, "the teams' line-ups", one, team, raw)
    command("officials", cmd_officials, "the teams' officials and their discipline", one, team, raw)
    command("check", cmd_check, "what looks wrong in the report", one)
    command("bundle", cmd_bundle, "everything about a match in one JSON document", one)
    c = command("cache", cmd_cache, "list or clear the cache of approved reports")
    c.add_argument("action", choices=("list", "clear"), nargs="?", default="list")
    return p


def main(
    argv: Sequence[str] | None = None,
    env: Mapping[str, str] | None = None,
    *,
    client: FogisClient | None = None,
    out: IO[str] | None = None,
) -> int:
    """Run one command. `env`, `client` and `out` replace os.environ, the logged-in client and stdout."""
    args = parser().parse_args(argv)
    ctx = Context(args, os.environ if env is None else env, out or sys.stdout, client)
    try:
        args.func(ctx)
    except FogisInvalidCredentialsError as e:
        print(f"fogis: {e} (credentials from {ctx.credentials_source})", file=sys.stderr)
        return 3
    except (CredentialsError, FogisError) as e:
        print(f"fogis: {e}", file=sys.stderr)
        return 2
    except BrokenPipeError:  # e.g. piped into `head`
        sys.stderr.close()
        return 0
    finally:
        if ctx._client is not None:
            ctx._client.close()
    return 0
