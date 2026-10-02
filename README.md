# fogis-api-client

A Python client for [FOGIS](https://fogis.svenskfotboll.se/mdk/), the Swedish Football Association's system for
match reporting, as used by referees through the mobile referee client.

It logs in like the app does, keeps the session alive, reads your matches, events, line-ups, team officials and
results as typed objects, helps interpret what FOGIS stores (periods, substitutions, scores, server-made events), and
writes events and results with exactly the payloads the app sends.

> **Verified against live FOGIS.** Reading, and writing events, substitutions, results, attendance, line-up entries,
> team-official discipline and submitting were checked on real reports in September 2026, with payloads identical to
> the referee app's. Still untested: event types 3 and 33 (opt-in) and most of the rules FOGIS applies at submission.
> Coming from 0.x? See [docs/MIGRATION.md](docs/MIGRATION.md), or pin `fogis-api-client-timmyBird<1.0`.

```bash
pip install fogis-api-client-timmyBird
```

Requires Python 3.12 or newer. The only dependency is `requests`.

## Reading

```python
from datetime import date
from fogis_api_client import FogisClient

client = FogisClient("username", "password", cookie_file="~/.fogis-cookies.json")

for match in client.matches(date(2026, 1, 1), date(2026, 12, 31)):
    print(match.kickoff, match.home.name, "-", match.away.name, match.home_goals, match.away_goals)

match = ...  # one of the matches above
events = client.events(match.match_id)
home_lineup = client.lineup(match.home.match_team_id)
away_officials = client.officials(match.away.match_team_id)
results = client.results(match.match_id)
```

- **Login is lazy** and the session renews itself. With `cookie_file`, the session survives restarts and
  password logins become rare (FOGIS keeps a "remember me" cookie for 14 days).
- **Any date range works.** FOGIS returns at most 100 matches per request and silently drops the rest; the client
  splits the range until nothing is cut off.
- **Models keep everything.** Each object has typed fields and the original FOGIS record in `.raw`. FOGIS's
  placeholder values (0 ids, −1 numbers) become `None`, and `/Date(…)/` becomes a Swedish-time `datetime`.
- Also available: `lineup_changes()`, `earlier_matches()` (a team's earlier matches in a competition),
  `player_cautions()` and `official_cautions()` (accumulated cautions, for players and officials in your own matches).

## Making sense of events

FOGIS stores events as they were typed, not as they happened. `fogis_api_client.timeline` interprets them:

```python
from fogis_api_client.timeline import build_timeline

officials = client.officials(match.home.match_team_id) + client.officials(match.away.match_team_id)
for entry in build_timeline(match, events, officials):
    print(
        entry.period,
        entry.minute,
        entry.added_minutes,
        entry.kind,
        entry.event or entry.official,
        "ORPHAN" if entry.orphan else "",
        "SCORE?" if entry.score_mismatch else "",
    )
```

- **Period 0** (unknown) is inferred from the minute, and such events sort into place instead of first.
- **Substitutions** are paired off/on, including pre-2024 data where FOGIS didn't link them.
- **The running score** is computed from the goals and compared with the score the reporter typed, which FOGIS
  never checks.
- **Special events** are recognised: the sending-off FOGIS adds on a second caution (and the orphan it leaves when
  the caution is deleted), and the "penalty awarded" that live reporters enter before a penalty's outcome.
- **Team-official cautions and sending-offs**, which FOGIS keeps outside the event list, appear on the timeline.

## Writing

```python
from fogis_api_client import EventType, FogisClient, ResultType, next_score

client = FogisClient("username", "password", dry_run=True)  # nothing is sent; payloads are returned

player = home_lineup[0]
client.save_match_event(match, EventType.VARNING, "34", team_id=match.home.match_team_id, player=player)
client.save_match_event(
    match,
    EventType.SPELMAL,
    "45+2",
    team_id=match.home.match_team_id,
    player=player,
    score=next_score(events, match, match.home.match_team_id),
)
client.substitute(match, "60", team_id=match.home.match_team_id, player_in=home_lineup[12], player_out=player)
client.report_match_result(
    match.match_id, {ResultType.SLUTRESULTAT: (2, 1), ResultType.HALVTIDSRESULTAT: (1, 0)}
)
```

- **Times are typed as in the app** ("23", "45+2", "12:30") and converted exactly as the app converts them.
- **Fix mistakes in place:** `save_match_event(..., event_id=…)` edits an event, `edit_substitution(match, sub,
  time=…, player_in=…, player_out=…)` corrects a substitution (from `timeline.pair_substitutions()`), and
  `save_match_participant(player, shirt_number=…, substitute=…)` fixes a line-up entry. Only what you pass changes.
- **Don't save the sending-off for a second caution yourself**: FOGIS adds it. Deleting a second caution does not
  remove it; delete that one too.
- **Team-official discipline** is `save_official_discipline(official, minute=…, caution=…, sending_off="minor"|"major")`.
  Pass a freshly read official: FOGIS overwrites the whole record.
- Instead of `dry_run`, pass `confirm=` a callback `(method, payload) -> bool` to approve each write.
- **Before submitting, run `client.check_report(match)`.** FOGIS checks nothing; this finds a final or half-time
  result that doesn't match the goals, duplicate events, events without a minute or period, typed scores that don't
  add up, leftover automatic sending-offs, half substitutions and a missing responsible official.
- **To remove a team official's caution or sending-off use `clear_official_discipline(official)`.** FOGIS ignores
  every attempt to remove discipline from the record; this removes the official and adds them again, cleanly.

## ⚠️ Calls that cannot be undone

Two methods lock the match in FOGIS. There is no way back from either, through this library or the app:

| Method | FOGIS method | After the call |
|---|---|---|
| `mark_reporting_finished(match, confirm_match_id=...)` | `SparaMatchGodkannDomarrapport` | **The referee report is submitted.** You can no longer add, edit or delete events, results, line-ups or team-official discipline. |
| `end_live_reporting(match, confirm_match_id=...)` | `SparaMatchAvslutaLiveRapportering` | **No more events or results** can be added. |

Both require the match id to be repeated as `confirm_match_id`, refuse a match without a reported final result
(unless `allow_missing_result=True`), and respect `dry_run` and the `confirm` callback like every other write.
`mark_reporting_finished` also refuses while `check_report()` finds errors, unless `ignore_problems=True`.
Postponing a match (`SkjutUppMatch`) is not implemented at all.

## Coming from 0.x

1.0 is a rewrite. `FogisApiClient` still exists for existing code and keeps its constructor,
`fetch_matches_list_json(filter_params)`, `get_match_details()`, `login()`, `get_cookies()` and the three login
exceptions (`FogisLoginError`, `FogisInvalidCredentialsError`, `FogisAuthServiceUnavailableError`). It returns raw
dicts as before, but match lists longer than 100 now come back complete. `fetch_match_json()` still works but is
deprecated: it fetches the whole match list on every call.

Removed: the mock server, API gateway, swagger UI, CLI, OAuth-token login (FOGIS sessions are cookie-only),
`clear_match_events()` (FOGIS has no such method) and the convenience helpers. `mark_reporting_finished` now takes the
match and a `confirm_match_id`. **[docs/MIGRATION.md](docs/MIGRATION.md) lists every 0.x name and its 1.0 replacement**;
old-style calls fail with a message pointing there.

## How FOGIS behaves

[docs/FOGIS_API.md](docs/FOGIS_API.md) records what is known about the API: login and session lifetime, every method the
referee app calls, the enums, how events really behave, and what is still unverified. The library follows that document.

## Development

```bash
uv sync
uv run pytest                                  # unit tests
uv run --env-file .env pytest -m live          # read-only checks against FOGIS (FOGIS_USERNAME / FOGIS_PASSWORD)
uv run ruff check && uv run ruff format --check && uv run mypy
```

`tools/verify/` holds the write-verification runner and a comparison tool for browser recordings (HAR). Test fixtures
in `tests/fixtures/` are real FOGIS responses, anonymized.

## License

MIT — see [LICENSE.txt](LICENSE.txt).
