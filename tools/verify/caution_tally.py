"""Do cautions count towards the tally in a competition? Read-only; prints shirt numbers, never names.

    uv run --env-file .env python -m tools.verify.caution_tally --match ID --date YYYY-MM-DD

1. Control group: every player cautioned in one of *your own* submitted reports in the same competition this
   season, with FOGIS's tally (spelareAntalAckumuleradeVarningar) and its caution search
   (SokVarningarForSpelareITavling).
2. The given match: every player on both teams, the same two numbers.

If the control group shows counts and the match shows zeros, FOGIS counts cautions and the match adds none.
If the control group is all zeros too, the competition doesn't count (or doesn't show) cautions to referees.
"""

from __future__ import annotations

import argparse
import os
from datetime import date

from fogis_api_client import FogisClient, FogisSession
from fogis_api_client.models import LineupEntry, Match

CAUTIONS = (1, 7, 20)


def tally(client: FogisClient, match: Match, player: LineupEntry) -> tuple[int, int]:
    """(FOGIS's accumulated count on the line-up row, rows in the caution search) for one player."""
    engagement = (
        match.home.engagement_id
        if player.match_team_id == match.home.match_team_id
        else match.away.engagement_id
    )
    return player.accumulated_cautions, len(client.player_cautions(player.player_id, engagement))


def side(match: Match, player: LineupEntry) -> str:
    return "home" if player.match_team_id == match.home.match_team_id else "away"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--match", type=int, required=True)
    ap.add_argument("--date", type=date.fromisoformat, required=True)
    a = ap.parse_args(argv)
    session = FogisSession(
        os.environ["FOGIS_USERNAME"],
        os.environ["FOGIS_PASSWORD"],
        cookie_file=".verify/cookies.json",
        min_interval=1.0,
    )
    client = FogisClient(session=session)
    target = client.match(a.match, around=a.date, days=2)
    if target is None:
        raise SystemExit(f"match {a.match} not found")
    season = client.matches(date(a.date.year, 1, 1), date(a.date.year, 12, 31))
    others = [
        m
        for m in season
        if m.competition_id == target.competition_id and m.report_approved and m.match_id != target.match_id
    ]
    print(f"Competition: {target.competition_name} | your other submitted matches in it: {len(others)}\n")

    print("1. Control group: players cautioned in your own submitted reports")
    counted = 0
    for m in others:
        cautioned = {e.player_id for e in client.events(m.match_id) if e.type_id in CAUTIONS and e.player_id}
        if not cautioned:
            print(f"   {m.date} {m.match_number}: no cautions")
            continue
        players = [
            p for t in (m.home, m.away) for p in client.lineup(t.match_team_id) if p.player_id in cautioned
        ]
        for p in players:
            acc, rows = tally(client, m, p)
            counted += acc > 0 or rows > 0
            where = f"{m.date} {m.match_number}: {side(m, p)} #{p.shirt_number}"
            print(f"   {where}: tally {acc}, caution search {rows}")

    print(f"\n2. {target.date} {target.match_number}: every player")
    nonzero = []
    for t in (target.home, target.away):
        for p in sorted(client.lineup(t.match_team_id), key=lambda p: p.shirt_number or 0):
            acc, rows = tally(client, target, p)
            if acc or rows:
                nonzero.append(f"{side(target, p)} #{p.shirt_number}: tally {acc}, caution search {rows}")
    print("   " + ("\n   ".join(nonzero) if nonzero else "all players: tally 0, caution search empty"))

    print(
        "\nReading:",
        "cautions ARE counted in this competition"
        if counted
        else "no control-group player shows a count: this competition doesn't count or show cautions",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
