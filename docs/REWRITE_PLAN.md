# fogis-api-client 1.0.0 — rewrite plan

Decided 2026-09-25/26. Read together with [FOGIS_API.md](FOGIS_API.md) — that file is the source of truth for
how FOGIS behaves. The old code and the mock server are **not** (they mix verified facts with guesses).

## Status (2026-10-02): stages 1–5 done, ready for 1.0.0

Stages 1–4 (session, reads and models, timeline helpers, writes, 0.x compatibility) are on branch `rewrite/1.0`.
Stage 5, verification in real reporting windows, is done:
- **2026-09-27:** five browser recordings of normal reporting; the library's payloads matched the app's field for field
  (caution, own goal, substitution, event edit, results, attendance, discipline, captain); the library's first real
  writes corrected that report.
- **2026-09-30:** the §10 checklist run live with `tools/verify/runner.py` on an open report; the report ended identical to
  its snapshot after a full delete-and-rebuild; the report was then submitted through the library.

Found on the way and handled: team-official discipline can't be removed in place (`clear_official_discipline()`), caution
types 1/7 and type 33 are stored hidden (refused / opt-in), the server checks the captain at submission (`check_report()`).
Open, not release-blocking: types 3 and 33 (opt-in), and the full set of submission rules (FOGIS_API.md §10.16).

## Decisions

- **Rewrite in place**, same repo, same PyPI name (`fogis-api-client-timmyBird`), released as **1.0.0**.
  Users pinned to `<1.0` keep working. Git tag `v0.8.0` preserves the old code.
- **Start from an empty package** on a new branch off `main`; port *knowledge*, not code.
- **Drop:** `internal/` layer (dead), `core/` (dead), TypedDicts that don't match the API, convenience helpers,
  pure-OAuth token path, mock-server CLI inside the package. Gateway/swagger/mock server move out of the package
  (separate repo/folder, not in `install_requires`) or get deleted.
- **One packaging config** (pyproject.toml), minimal deps: requests only (the login form is parsed with the stdlib).
- **Python ≥ 3.12.**

## Compatibility surface (only known consumer: fogis_friend)

fogis_friend uses only:
- `FogisApiClient(username=..., password=...)`
- `fetch_matches_list_json()` (no args; also used as its login check)
- `fetch_match_json(match_id)` (deprecated alias — fetches the whole list per call; fogis_friend should look up from the list it already has)
- exceptions `FogisLoginError`, `FogisInvalidCredentialsError`, `FogisAuthServiceUnavailableError`

Keep these working (deprecated where appropriate). Keep write method names (`save_match_event`, `report_match_result`,
`mark_reporting_finished`, …) as the public face of the write side.

## Build order

1. **Transport + session** (all verified): OIDC login with RememberMe=true, persistable cookie jar, detect expiry by
   302 (never 401) with `allow_redirects=False`, silent re-auth via `.AspNetCore.Identity.Application`, password login
   only as last resort, timeouts on every request, typed exceptions chained with `from e` (no string sniffing).
2. **Reads + models** (verified): match list with per-year chunking (100 cap), events, line-ups, officials, results,
   change log, earlier matches, warnings search. Complete enums (40 event types, 5 result types, 3 football types).
   Timeline helpers: infer period from minute when period 0; pair unlinked substitutions (pre-2024); compute running
   score (don't trust `hemmamal`/`bortamal`); detect automatic #2/#3 and orphan #2.
3. **Writes**: payload shapes straight from the app's JS (FOGIS_API.md §4). Uncertain semantics isolated:
   - one `encode_match_time()` function for added time (hypothesis in FOGIS_API.md §10.5)
   - tolerant parsing of write responses (shape unknown) — log until known
   - `SparaMatchlagledare` always re-sends current `lagrollid`/`ansvarig`
   - every assumption marked in code with a reference to the FOGIS_API.md test checklist
   - **never** expose `SkjutUppMatch` or `SparaMatchGodkannDomarrapport` without an explicit, separate confirmation
4. **Compatibility layer** for fogis_friend (above).
5. **Verification** in the first open reporting window:
   - record browser traffic (HAR) while reporting normally → ground truth for write calls
   - run the FOGIS_API.md §10 checklist in the small hours with a **dry-run mode** (print payload, ask before sending),
     delete test events immediately, never submit
   - adjust, then release 1.0.0

## Tests

- Fixtures from real captured responses, anonymized (source: a sanitized personal archive, kept private,
  which still contains names; `tests/fixtures/` holds the anonymized result).
- No tests that encode mock-server guesses. Old tests that only exercise dead code get deleted.

## Out of scope for 1.0 (backlog)

Voice notebook ("Skriv:" grammar), comms recording, timeline UI, overlays, IMU. GDPR stance for history features in
Fogis Friend: "take-out, not store" / local-first tools; never aggregate across referees.
