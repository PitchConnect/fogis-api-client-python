# Migrating from 0.x to 1.0

1.0 is a rewrite. It keeps the package name (`fogis-api-client-timmyBird`) and the import name (`fogis_api_client`),
but most of the 0.x surface is gone or changed. If you are not ready to migrate, pin `fogis-api-client-timmyBird<1.0`.

**Why so much changed:** 0.x mixed verified behaviour with guesses (a mock server, payloads FOGIS doesn't accept, a
`ClearMatchEvents` method that doesn't exist, login that could never renew). 1.0 follows only what is established in
[FOGIS_API.md](FOGIS_API.md), and its write payloads are exactly what the referee app sends.

Old-style calls fail with a message that points here instead of a bare `TypeError` or `AttributeError`.

## Requirements

| 0.x | 1.0 |
|---|---|
| Python ≥ 3.7 | **Python ≥ 3.12** |
| requests, beautifulsoup4, flask, apispec, marshmallow, psutil, jsonschema, … | **requests only** (`tzdata` on Windows) |

## What still works

`FogisApiClient` keeps the calls existing code depends on. It returns raw FOGIS dicts, as before:

| Call | Note |
|---|---|
| `FogisApiClient(username=..., password=...)` or `FogisApiClient(cookies={...})` | `oauth_tokens=` is gone (FOGIS sessions are cookie-only) |
| `login()`, `get_cookies()` | |
| `fetch_matches_list_json(filter_params=None)` | same filter keys; **ranges with more than 100 matches now come back complete** |
| `get_match_details(match_id, filter_params=None)` | |
| `fetch_match_json(match_id)` | deprecated: fetches the whole match list per call |
| `FogisLoginError`, `FogisInvalidCredentialsError`, `FogisAuthServiceUnavailableError`, `FogisAPIRequestError`, `FogisDataError` | now share the base class `FogisError`; `.message` still works |

New code should use `FogisClient`, which returns typed models (each with the original record in `.raw`).

## Reading

| 0.x | 1.0 (`FogisClient`, also available on `FogisApiClient`) |
|---|---|
| `fetch_match_events_json(match_id)` | `events(match_id)` → `MatchEvent`s (`[e.raw for e in …]` for dicts) |
| `fetch_match_result_json(match_id)` | `results(match_id)` → `MatchResult`s |
| `fetch_team_players_json(matchlagid)` (returned `{"spelare": [...]}`) | `lineup(match_team_id)` → `LineupEntry`s |
| `fetch_team_officials_json(matchlagid)` | `officials(match_team_id)` → `TeamOfficial`s |
| `get_match_players(match_id)`, `fetch_match_players_json(match_id)` | `lineup(match.home.match_team_id)` and `lineup(match.away.match_team_id)` |
| `get_match_officials(match_id)`, `fetch_match_officials_json(match_id)` | `officials(...)` per team; the referees are `match.crew` |
| `fetch_complete_match(match_id)`, `get_match_summary(match_id)` | combine `match()`, `events()`, `lineup()`, `officials()`, `results()` |
| `get_recent_matches(days)`, `find_matches(...)`, `get_matches_requiring_action(...)` | `matches(start, end)` and filter the models |
| `get_match_events_by_type(...)`, `get_team_statistics(...)` | filter `events()` by `EventType`; see `fogis_api_client.timeline` |
| `MatchListFilter` | `matches(start, end, exclude_statuses=..., age_categories=..., genders=...)` |
| `EVENT_TYPES` dict (16 types; 17 called "Substitution") | `EventType` enum, all 40 types, with `is_goal`, `is_caution`, … |
| `enums.MatchStatus` | strings in `fogis_api_client.client.STATUSES`: `"avbruten"`, `"uppskjuten"`, `"installd"` (excluded via `exclude_statuses`) |
| `enums.AgeCategory`, `enums.Gender` | plain ints (`age_categories`, `genders`) |
| `enums.FootballType.FOOTBALL` / `.FUTSAL` | `FootballType.FOTBOLL` / `.FUTSAL` / `.BEACH_SOCCER` (members follow FOGIS's own names) |
| TypedDicts (`MatchDict`, `EventDict`, `PlayerDict`, …) | models: `Match`, `MatchEvent`, `LineupEntry`, `TeamOfficial`, `MatchResult`, … |

## Writing

All writes take models read from FOGIS and send exactly what the referee app sends. Try them with
`FogisClient(..., dry_run=True)` first.

| 0.x | 1.0 |
|---|---|
| `save_match_event(event_data: dict)` | `save_match_event(match, event_type, time, team_id=..., player=..., score=...)`; time as typed in the app ("45+2") |
| a substitution as one `save_match_event` | `substitute(match, time, team_id=..., player_in=..., player_out=...)` |
| (none) | `edit_substitution(...)`, `save_match_event(..., event_id=...)` to correct in place |
| `delete_match_event(event_id)` → `bool` | `delete_match_event(event_id)` → FOGIS's answer; raises on failure |
| `clear_match_events(match_id)` | removed: FOGIS has no such method; delete events one by one |
| `report_match_result(result_data: dict)` | `report_match_result(match_id, {ResultType.SLUTRESULTAT: (2, 1), ...})` |
| `save_match_participant(participant_data: dict)` | `save_match_participant(player, shirt_number=..., substitute=..., captain=...)` |
| `save_team_official(official_data: dict)` | `save_official_discipline(official, minute=..., caution=..., sending_off=...)`; to remove discipline `clear_official_discipline(official)` |
| `mark_reporting_finished(match_id)` | `mark_reporting_finished(match, confirm_match_id=match.match_id)` — **submits the report, cannot be undone**; refuses while `check_report()` finds errors |

Write methods no longer return `{"success": True, "data": ...}`: they return FOGIS's answer and raise
`FogisAPIRequestError` (or `FogisRejectedError` with FOGIS's own text in `.server_message`) when FOGIS says no.

## Session and authentication

| 0.x | 1.0 |
|---|---|
| `refresh_authentication()` | automatic; manually `client.session.renew()` |
| `is_authenticated()`, `validate_cookies()` | `client.session.is_valid()` (one small request, never logs in) |
| `get_authentication_info()` | removed |
| expired session → "Failed to parse API response" | renewed automatically, without the password when possible |
| (none) | `FogisClient(..., cookie_file="~/.fogis-cookies.json")` keeps the session between runs |

## Removed without replacement

The mock server, API gateway, swagger UI and CLI (`fogis_api_client.cli`), the logging helpers (`configure_logging`,
`get_logger`, `set_log_level`, `get_log_levels`, `add_sensitive_filter`, `SensitiveFilter`; use the standard `logging`
module, logger names start with `fogis_api_client`), the validation helpers (`ValidationConfig`, `validate_request`,
`validate_response`, `convert_flat_to_nested_match_result`), `hello_world()`, and the `internal`/`core` packages.
