# FOGIS API — what is known

How the API behind FOGIS's mobile referee client (`/mdk`) actually behaves, as far as it has been established.
This library follows this document, not the 0.x code or its mock server. Each finding is marked by source:

- **[live]** observed against production FOGIS (read-only unless stated)
- **[js]** read from the referee app's own code (`/mdk/js/app.min.js?v=20260610`)
- **[history]** derived from one referee's match history (several hundred matches with reports, thousands of events)
- **[referee]** confirmed by a practising referee's first-hand experience
- **[unverified]** inferred, needs a test (see §10)

Writes come from the app's code; event saves, edits and deletes are also confirmed live (2026-09-27): the library's
payloads matched the app's field for field, and the library has saved and deleted events on a real report.

---

## 1. Authentication

- **Flow [live]:** `Login.aspx` → 302 `auth.fogis.se/connect/authorize` (IdentityServer; client `fogis.mobildomarklient`;
  `response_type=code`, PKCE S256, scope `openid fogis profile anvandare personid offline_access`)
  → 302 `/Account/LogIn` (form: `Username`, `Password`, `RememberMe`, `__RequestVerificationToken`)
  → POST `/Account/Login` → `/connect/authorize/callback` → `/mdk/signin-oidc?code=…` → `/mdk/Start/OnAuthenticated` → `/mdk/`.
- **The code exchange happens server-side [live]** (mdk is .NET 4.7.2 OWIN). A client only ever holds cookies; there are no
  tokens to obtain or refresh.
- **The legacy ASP.NET form login is gone [live]:** `Login.aspx` always redirects to OIDC.
- **Only `.MDK.AuthCookie` is needed for API calls [live].** `.MDK.SessionCookie` and `NSC_*` (Citrix NetScaler
  load-balancer stickiness) are not required.
- **Unauthenticated or expired → 302 to `/connect/authorize` [live]** (HTML "Access is denied"), **never 401**.
- **Validity check [live]:** any read POST with `allow_redirects=False` → 200 JSON = valid, 302 = expired.
- **Silent re-auth [live]:** with only `.AspNetCore.Identity.Application` (domain `auth.fogis.se`), `GET /mdk/` follows four
  redirects and yields a new `.MDK.AuthCookie`, no password needed. Still working 1 h, 3 h and 6 h after login.
- **RememberMe [live]:** `true` → `.AspNetCore.Identity.Application` is persistent and expires after **14 days**; `false` → a
  browser-session cookie. Whether the server honours the full 14 days: **[unverified]**.
- **Concurrent sessions are fine [live]:** a second silent re-auth or password login does not invalidate the first session.
- **Session lifetime [live]:**
  - An untouched `.MDK.AuthCookie` is still valid after **6 h** idle.
  - In use, the server **re-issues `.MDK.AuthCookie` roughly hourly** (a sliding session); clients must keep the re-issued cookie.
  - A session used every 10 min stayed valid through an **8 h** test; ~3,000 requests over 2 h needed no re-auth.
- **Wrong credentials [live]:** for a non-existent username the login form is rendered again (HTTP 200). A wrong password on
  a real account (possibly with a lockout message) is **[unverified]**.

**Client strategy:** RememberMe=true; persist the cookie jar; on a 302 renew silently via the identity cookie; only then log in
with the password. Password logins become rare, which lowers the lockout risk.

## 2. Transport

- Every call is `POST /mdk/MatchWebMetoder.aspx/<Method>` with a JSON body and the headers
  `Content-Type: application/json; charset=utf-8` and `X-Requested-With: XMLHttpRequest`.
- **The response is `{"d": …}` with `d` already parsed [live]** (object or list), never a JSON string.
- Errors from page methods come as JSON `{Message, ExceptionType, StackTrace}` (standard ASP.NET; the app shows `Message`).
- **Dates [live]:** `speldatum` "YYYY-MM-DD"; `tid` "/Date(ms)/" (milliseconds since the epoch, UTC); `avsparkstid` "HH:MM".
- **No nulls in read data; sentinels instead [history]:** missing id = `0` (control events have `matchlagid`, `spelareid`,
  `matchdeltagareid` 0), missing number or position = `-1` (`trojnummer`, `planpositionx/y`), missing venue coordinate
  = `-1.7976931348623157e308` (.NET `double.MinValue`).
- No rate limiting seen at one request per 1.5 s [live]; thresholds unknown.
- A plain `python-requests` User-Agent is accepted for login, re-auth and API calls [live].

## 3. Match list — `GetMatcherAttRapportera`

- `d` = `{__type, anvandartyp, anvandareforeningid, matchlista, anvandare (null), endastLiverapportor}`; each match has
  85 fields [live].
- **The server honours `datumFran`/`datumTill` [live].**
- **Hard cap of 100 matches, oldest first, silently truncated [live].** A range with more matches returns the first 100
  and nothing else. Fetch per year (and split further if a request comes back full).
- `datumTyp` (0 = sliding, 1 = fixed) and `sparadDatum` belong to the app's filter cookie; results are identical [live][js].
- The `status` list **excludes** (`"avbruten"`, `"uppskjuten"`, `"installd"`); `alderskategori` and `kon` **include**.
- App default filter [js]: today to +1 year, the three statuses excluded, `alderskategori` [1..5], `kon` [2, 3, 4].
- **There is no single-match method [js]** (no GetMatch/HamtaMatch). Finding one match means listing and scanning.
- **Reporting window [js]** (`truppFarRedigeras`, for referees): from kick-off minus
  `tavlingAntalTimmarInnanMatchForTruppAdministration` **minutes** (multiplied by 60,000 ms despite "Timmar" in the name)
  until kick-off plus `tavlingAntalDagarEfterMatchForAdministrationAvDomarrapport` days. **This check is in the app; whether
  the server enforces it is unknown.**
- Live-reporting flags per match: `liverapporteringTillaten`, `liverapporteringsAktorTypId`, `liverapporteringPaborjad`,
  `liverapporteringAvslutad` [live]. Actor types 1, 4 and 5 get extra input (assists, positions) [js]; 0 and 2 are the
  common values on a referee's own matches [history]. The meaning of 2 is **[unverified]**.

## 4. Methods — 33 in the app [js]

### Reads (16)

| Method | Payload | Returns |
|---|---|---|
| GetApplicationConfig | `{}` | `{ArvodesUrl}` |
| GetMatcherAttRapportera | `{filter:{…}}` | match list (≤ 100) |
| GetMatchhandelselista | `matchid` | events |
| GetMatchresultatlista | `matchid` | results, one row per result type |
| GetMatchdeltagareListaForMatchlag | `matchlagid` | one team's line-up in one match |
| GetMatchlagledareListaForMatchlag | `matchlagid` | one team's officials, including discipline |
| GetMatchdeltagareAndringForMatch | `matchid` | line-up change log |
| GetTruppdeltagareListaForLag | `lagid` | full club squad (**contains personnr**) |
| hamtaTidigareMatcherForLag | `tavlingsId, lagengagemangId` | a team's earlier matches in a competition |
| GetLagPersonLista | `lagId` | a team's people |
| GetForeningPersonLista | `foreningid, lagid` | a club's people |
| GetForeningSpelareLista | `foreningid, filter` | a club's players |
| GetExternaSpelareLista | `personnr, tavlingid` | a player from another club |
| GetExternPersonLista | `personnr, tavlingid` | a person from another club |
| SokVarningarForSpelareITavling | `spelareId, lagengagemangId` | a player's cautions in the competition |
| SokVarningarForLedareITavling | `personId, lagengagemangId` | an official's cautions in the competition |

The first nine and the two caution searches have been called live, for matches the account is assigned to.

### Writes (17)

| Method | Payload |
|---|---|
| SparaMatchhandelse | `matchhandelseid` (0 = new), `matchid, period, matchminut, sekund, matchhandelsetypid, matchlagid, spelareid, spelareid2, hemmamal, bortamal, planpositionx, planpositiony, matchdeltagareid, matchdeltagareid2, fotbollstypId, relateradTillMatchhandelseID` |
| RaderaMatchhandelse | `matchhandelseid` |
| SparaMatchresultatLista | `matchresultatListaJSON: [{matchid, matchresultattypid, matchlag1mal, matchlag2mal, wo, ow, ww}]` |
| SparaMatchdeltagare | `matchdeltagareid, trojnummer, lagdelid, lagkapten, ersattare, positionsnummerhv, arSpelandeLedare, ansvarig` |
| LaggTillMatchdeltagare | `spelareid, trojnummer, matchlagid, tavlingantalstartadespelareigodkanddomarrapport` |
| SparaMatchlagledare | `matchlagledareid, lagrollid, avvisadmatchminut, avvisadlindrig, avvisadgrov, varnad, ansvarig` |
| LaggTillMatchlagledare | `personid, lagrollid, matchid, matchlagid` |
| MatchLaguppställningKlar | `matchlagid, matchdeltagareAttRaderaListaJSON, matchDeltagareAndraErsattareListaJSON, matchlagledareAttRaderaListaJSON, matchdeltagareAttAndraPositionListaJSON` |
| SparaSpelsystem | `matchid, matchlagid, spelsystem` |
| OffentliggorMatchtrupp | `matchlagId, offentliggorDatum` |
| SparaPubliksiffra | `matchid, antalaskadare` (the app builds this JSON by string concatenation) |
| SparaMatchklimat | `matchklimat` |
| SparaNoteringFranDomare | `matchid, noterinfrandomare` (sic) |
| SparaNoteringFranLag | `matchid, matchlagid, noterinfranlag` (sic) |
| SkjutUppMatch | `matchid` — **postpones the match** |
| SparaMatchAvslutaLiveRapportering | `matchid` — **ends live reporting: no more events or results; cannot be undone** |
| SparaMatchGodkannDomarrapport | `matchid` — **submits the referee report; cannot be undone** |

How the app fills these [js] (ported in `fogis_api_client/writes.py`):

- **New event:** one `SparaMatchhandelse` with `matchhandelseid: 0` and `relateradTillMatchhandelseID: 0`. Without team or
  player: `matchlagid: 0`, `spelareid: 0`, `matchdeltagareid: null`. `planpositionx/y` are **strings**; `"-1"` means none.
- **Goals (6, 39) from the referee client** send `spelareid2`/`matchdeltagareid2` = −1 (the referee client has no assist
  input; assists are only sent for actor types 1 and 4). Other events send 0 / null.
- **Score fields** are sent only for result-affecting types (6, 14, 15, 21, 28, 29, 39, 40), otherwise 0. The app suggests
  the highest score typed so far plus one for the scoring team; the reporter can change it and the server never checks it.
- **A new substitution is one call [js][live]:** type 17 with the incoming player in `spelareid`/`matchdeltagareid` and the
  outgoing one in `spelareid2`/`matchdeltagareid2`. The server stores 16 (id n) and 17 (id n + 1, related to n).
- **Deleting a substitution is two calls [live]:** the app's single delete button sends `RaderaMatchhandelse` for the 17,
  then for the 16. The server does not cascade: after deleting the 17, the 16 is still there.
- **Editing an event [live]:** the same payload as a new event with `matchhandelseid` set; the id is kept.
- **An empty minute [live]** is sent as period 0, minute 0 and stored as `tidsangivelse` "0" (typing "0" gives period 1).
- **Responses [live]:** `SparaMatchhandelse` returns the match's **whole event list** in `d`; `RaderaMatchhandelse`,
  `SparaMatchresultatLista` and `MatchLaguppställningKlar` return `d: null`; `SparaPubliksiffra` and
  `SparaMatchAvslutaLiveRapportering` return the updated match; `LaggTillMatchlagledare` returns the new official;
  `SparaMatchlagledare` returns **every official of that team, including their `personnr`** (the library strips it).
  The app sometimes sends the id to delete as a string (both work).
- **Attendance [js][live]:** the app shows 0 as a blank field and sends a blank field as 0, so "no attendance" is 0.
  Its body is built by hand without quoted keys (`{ matchid : 1, antalaskadare : 50 }`); the server accepts that
  and proper JSON alike.
- **Time** is typed as text ("23", "45+2", "12:30") and converted by `getMatchtidpunktNy`; see §6 "Added time" and
  `fogis_api_client/matchtime.py`.
- `matchresultatListaJSON` is a JSON array, not a string. The app sends only changed rows.
- The team-official discipline form has **one** minute field (`avvisadmatchminut`) for L, G and V.
- **Ending live reporting ("Stäng rapportering") [js][live]** sets `liverapporteringAvslutad`; it locks out the club
  reporters (the "Resultatrapportör" roles), not the referee, who can still edit events and results and then sees
  "OBS! Matchen har liverapporterats av förening". The app has no call to reopen it.
- **Submitting (`SparaMatchGodkannDomarrapport`) [live, 2026-09-27]:** returns the updated match (all 85 fields,
  `matchrapportgodkandavdomare: true`, a `matchrapportgodkandavdomaredatum`). **The server validates at this point:** a team
  without a captain is refused with HTTP 500, `ExceptionType: System.ApplicationException`, `Message: "Bortalagets
  matchtrupp saknar lagkapten."` (the away team's squad has no captain). Other rules it enforces are unknown; the app shows
  the `Message`. Nothing else in a report is validated by the server while editing. **Not checked at submission
  [live, 2026-09-30]:** the number of starting players (a team with 9 starters was accepted).
- `SparaMatchdeltagare` returns the team's whole line-up, including `personnr` [live]; the library's payload for setting
  a captain was identical to the app's.
- **Not in the app:** ClearMatchEvents, RensaMatchhandelser, GetMatch, HamtaMatch, GetMatchdeltagareLista.
- **The server publishes no method list [live, 2026-09-30]:** `GET MatchWebMetoder.aspx` (and `/js`, `/jsdebug`, the usual
  ASP.NET AJAX proxy addresses) returns only an empty form with an opaque `__VIEWSTATE`. The app's code and recorded
  traffic remain the only sources; methods outside the app's 33 are unknown and must not be called.

## 5. Enums [js]

**MatchhandelsetypOption (40):** 1 VarningOjustSpel, 2 LindrigUtvisningAvvisning, 3 Straffspark, 4 Frispark, 5 Horna,
6 Spelmal, 7 VarningOlampligtUpptradande, 8 Malchansutvisning, 9 GrovUtvisningAvvisning, 10 SaknarSpelarlegitimation,
11 MalgivandePassning, 12 SkottUtanforMal, 13 SkottPaMal, 14 Straffmal, 15 Sjalvmal, 16 ByteUt, 17 ByteIn,
18 Straffmissutanfor, 19 StraffmissRaddning, 20 Varning, 21 StraffavgorandeMal, 22 StraffavgorandeMiss, 23 MatchSlut,
24 Offside, 25 SkottIMalstallning, 26 StraffmissIMalstallning, 27 MatchsekreterareAvslutarMatchrapportering, 28 Hornmal,
29 Frisparksmal, 30 FrisparkOrsakadAv, 31 HalvlekPeriodStart, 32 HalvlekPeriodSlut, 33 AnnonseradStopptid,
34 StraffOrsakadAv, 35 StraffSkjutsAv, 39 Nickmal, 40 TioMeterStraffMalFutsal, 41 TioMeterStraffMissFutsal, 42 TimeOut,
4545 JusteraMatchklocka.

**MatchresultattypOption:** 1 Slutresultat, 2 Halvtidsresultat, 3 FullTid, 4 EfterForlangning, 5 EfterStraffar.
**FotbollstypOption:** 1 Fotboll, 2 Futsal, 3 BeachSoccer.
**DomaruppdragstatusOption:** 1 Skapat, 2 Tillgangligt, 3 Preliminart, 4 Foreslaget, 5 Tilldelat,
6/7/8 Tilldelat innan uppskjuten/avbruten/WO.

## 6. Events — how they really behave

- **Caution types 1 and 7 are dangerous [live, 2026-09-30]:** saved through `SparaMatchhandelse` they are accepted but
  **never appear in the event list** (`GetMatchhandelselista`, the app, the public web), so they can't be seen or deleted.
  They still count as yellow cards: types 1 + 7 on one player produced an automatic #2, and a further caution was then
  refused with HTTP 500 "Spelaren kan inte få fler än 2 gula kort i en match." Never use them (the library refuses);
  everyone uses 20. After submitting that report, the player's `spelareAntalAckumuleradeVarningar` stayed 0 and
  `SokVarningarForSpelareITavling` stayed empty, while the same search finds every visible caution from earlier
  submitted reports in that competition: **hidden cautions are not counted towards suspensions [live]**, still true two
  days after submission.
- **Caution types in practice [history][referee]:** 1 and 7 are not used; everyone uses 20. They most likely stem from the
  paper-report era, when the form had two kinds of caution that the FA keyed in by hand [referee]. The server evidently
  still treats them as yellow cards in its card rules (automatic #2, "no more than 2 yellow cards") while the event list
  only returns types it is meant to show, which would also explain type 33 disappearing. Goals are 6
  (plain) or a subtype (39 header, 29 free kick, 28 corner, 15 own goal, 14 penalty), which the public web shows with a
  sub-heading [referee].
- **A substitution is stored as two events [live][history]:** 16 ByteUt, then 17 ByteIn whose `relateradTillMatchhandelseID`
  is the 16's id. **The link exists only since about 2024 [history];** older substitutions must be paired by team and minute.
- **Second caution → automatic #2, created by the server [history][js][referee]:**
  - A #2 follows two cautions on the same player, with the same `tidsangivelse` as the second caution, never linked
    (rel = 0), usually with id = second caution's id + 1. Two cautions always produced a #2; #2 is not used otherwise.
  - The app never posts type 2.
  - **Deleting the second caution leaves the #2 behind [referee].** A "#2 without two cautions on that player" is an orphan.
- **#3 "penalty awarded" [history][js][live]:** in history, 3 appears linked to 14 (or 26), with the id just before the
  outcome, same time and player. The referee app defines type 3 but **never sends it, for any role**, and a 14 saved by a
  referee gets **no** #3 (2026-09-30). So #3 comes from other reporting clients (live reporting: "penalty!" first, then the
  outcome linked to it), not from the server. Saving 3 through this API is untested (the library needs allow_untested).
- **Penalty shoot-out [js][history]:** period = `antalhalvlekar + antalforlangningsperioder + 1` (3 in a normal match, 5
  with two extra periods). `tidsangivelse` is usually "0" (shown blank); in futsal with high-resolution time it can be mm:ss.
  **IFAB:** the shoot-out is separate from the match, so a caution in the match plus one in the shoot-out must not send a
  player off [referee]. Whether the server's automatic #2 respects this: **[unverified]**.
- **Added time [js][history][live]:** the app turns "90+5" into minute 95 in the period of the regular minute (2). FOGIS
  stores `matchminut: 90`, `period: 2`, `tidsangivelse: "90+5"`; the "+5" exists in no numeric field. Confirmed live:
  "45+2" → period 1, minute 45, "45+2"; "47" → period 2; "45" → period 1; "90+3" → period 2, minute 90; "91" → **period 0**. Other rules of the app's converter, reproduced by `matchtime.py`:
  - a minute past the last period ("91" in a 90-minute match) gets **period 0**;
  - a substitution at exactly the end of a period belongs to the next period (half-time substitution);
  - with high-resolution time (`tavlinganvanderhogupplosttid`), "12" means 11:00 and "12:30" is taken literally.
  The port reproduces the stored period of more than 99% of events saved since 2019 [history]. The exceptions are
  explained: substitutions at exactly 90:00 were stored in period 3 until 2023 (the app changed in 2024); mm:ss times in
  competitions without high-resolution time are stored as the next whole minute ("64:31" → 65); and futsal periods were
  often lost in 2019–2023.
- **Period 0 means unknown [history][referee]:**
  - Before ~2018 the period was often not recorded at all.
  - Today it mostly comes from minutes typed as "91" instead of "90+1" [referee], or an event saved with an empty minute
    (allowed for referees) → minute 0, period 0.
  - **The public web sorts by period, then minute**, so period-0 events appear first [referee]. Clients should infer the
    period from the minute.
- **Score fields on events [js][history]:** `hemmamal`/`bortamal` are the score after a goal **as typed by the reporter**,
  never validated, and 0-0 on every other event. Goals saved out of match order carry the typed values, which may look wrong
  in save order and right in match order. → Compute the running score from the goals and flag mismatches.
- **Own goals (15) [referee]:** `matchlagid` is the team that **benefits**, so the running score counts goals per `matchlagid`.
- **Control events are unreliable [history]:** 23 MatchSlut exists in most but not all matches, 31/32 less often, and they
  can carry odd periods. Don't rely on them for half-time or full-time.
- **Listed result vs shoot-out [history]:** a match's listed result may exclude the shoot-out (1-1) or include it summed in
  (e.g. 4-4 after extra time + 5-4 on penalties listed as 9-8). Check result type 5 (EfterStraffar) before trusting either.
- `kommentar` is free text and appears on some events (goals, cautions, substitutions); it may contain names.
- **A goal saved without a player gets `kommentar: "Okänd spelare"` from the server [live]** (the app sends no comment).
  This is how unregistered players (e.g. trialists not in FOGIS) end up in a report.
- Incomplete reports exist (e.g. unmatched 16 events, matches without events).

## 7. Results and other read shapes

- **Result rows [live]:** `matchresultatid, matchid, matchresultattypid, matchresultattypnamn, wo, ow, ww, matchlag1mal,
  matchlag2mal`. The app sends rows without `matchresultatid`. **(-1, -1) deletes the row [live]**; sending the values
  again recreates it.
- **Line-up change log [live]:** `matchlagid, tidpunkt, beskrivning, andradav, andradavegenforening`; `tidpunkt` is
  **"HH:MM" only, without a date**.
- **Earlier matches of a team [live]:** the same 85 fields as a match-list entry; `domaruppdraglista` comes back empty.
- **Caution searches [live]:** one row per caution, `{arannullerad: bool, label: "Varning i match <matchnr>, <home> - <away>,
  <YYYY-MM-DD>"}`; the row count matches `spelare/ledareAntalAckumuleradeVarningar`. An empty list means no cautions.
- **`lagengagemangid` [history]:** one team's entry in one competition. No id is shared by two teams or two competitions;
  a team in several competitions has one per competition. Cup placeholders with the same `lagid` on both sides get one per side.
- **Line-up rows [history]:** `byte1`/`byte2` are substitution minutes (0 = none); `utvisning` is '' or a code ('L', 'M' seen);
  `lagdelid` 0–5 (meaning unknown); `positionsnummerhv` is 0.
- **Official rows [history]:** `varnadmatchminut` is filled when `varnad` is set; a sending-off can be saved with minute 0.

## 8. Team-official discipline

- **Not events:** fields on the official's match record, saved with `SparaMatchlagledare` [js].
- The form [js] has a checkbox and the exclusive options **Varning** (`varnad`), **Lindrig** (`avvisadlindrig`) and **Grov**
  (`avvisadgrov`), with one minute sent as `avvisadmatchminut`. The server stores the minute by card [live]: a caution
  (yellow) in **`varnadmatchminut`**, a sending-off (red) in **`avvisadmatchminut`**.
- **Discipline can be set but never removed with `SparaMatchlagledare` [live, 2026-09-27].** Unticking in the app sends
  all flags false and minute 0; the server answers 200 and keeps the caution. So do `avvisadmatchminut` 33 or −1,
  `varnad: "false"`, and an extra `varnadmatchminut` (0, −1, null, ""). The server method takes exactly the seven payload
  fields (`int`/`bool`; wrong types give HTTP 500 "Cannot convert null to a value type" / "is not a valid value for
  Int32"); unknown fields such as `varnadmatchminut` are ignored. The app offers no other way to remove it.
- **What works: remove the official and add them again [live]:** `MatchLaguppställningKlar` with
  `matchlagledareAttRaderaListaJSON: [{matchlagledareid}]` (other lists empty; `d: null`), then `LaggTillMatchlagledare
  {personid, lagrollid, matchid, matchlagid}`, which returns a new, clean record (new id, not responsible). If the team
  then has no responsible official, the app sets it automatically with `SparaMatchlagledare` (`ansvarig: true`).
  The library's `clear_official_discipline()` does exactly this.
- **A caution and a sending-off can co-exist on one official [referee][live]:** a caution at 30' and then only a minor
  sending-off at 80' leaves both (`varnadmatchminut` 30, `avvisadmatchminut` 80).
- **`SparaMatchlagledare` overwrites all seven fields**, so an edit must re-send the current `lagrollid` and `ansvarig` [js].
- The app's automatic "responsible official" path (`sattAutomatisktLedareSomAnsvarig`) sends all discipline as false and
  may wipe existing discipline [js].
- **Caution tallies count submitted reports only [live]:** a visible caution in an unsubmitted report changes neither
  `spelareAntalAckumuleradeVarningar` nor the caution search.
- **Use the caution search, not the line-up tally [live]:** in submitted reports of one competition, every cautioned player
  had exactly one row in `SokVarningarForSpelareITavling`, yet `spelareAntalAckumuleradeVarningar` on that match's line-up
  row was 0 for all of them (apparently the count before that match). `tools/verify/caution_tally.py` compares both.
- Accumulated cautions: `ledareAntalAckumuleradeVarningar`, `ledareAvstangningBeskrivning` (suspension text); players:
  `spelareAntalAckumuleradeVarningar`, `spelareAvstangningBeskrivning`, `utvisning` [live].
- The public web shows team-official sanctions [referee]; the referee client does not show them on the event timeline.

## 9. What was wrong in 0.x

Re-login could never work (it waited for a 401 that never comes); the `.MDK.*` cookies were not recognised; API requests
had no timeouts; `clear_match_events` called a method the app doesn't have; the event-type list was incomplete and treated
a substitution as one event; `fetch_match_json` fetched the whole match list per call; the OAuth-token path was dead; the
documented event example lacked `period` (creating period-0 events); and the 100-match cap was not handled.

## 10. Write test checklist

Run in an open, unsubmitted report of a low-profile match, at night; delete test data immediately; never submit.
`tools/verify/runner.py` automates this.

1. Goal subtypes: stored as sent [live]. **Types 1 and 7: hidden yellow cards — never use [live].**
2. Two cautions (20) on one player → automatic #2 (id, time, link)? (Blocked on 2026-09-30 by the hidden 1/7 cautions.)
3. Delete the second caution → does the #2 stay? (expected: yes [referee])
4. A caution in the match and one in the shoot-out period → does the server wrongly create a #2? (needs a cup match)
5. Added time: "45+2" vs "47" vs "45", "90+3" vs "91" → what is stored?
   5b. Type 33 AnnonseradStopptid: **accepted (HTTP 200) but not stored or not listed [live]**; hidden like 1 and 7? Don't use.
6. Official: V at 30' → `varnadmatchminut` 30 **[live: yes]**; then only L at 80' → is the caution kept? Clearing with
   `SparaMatchlagledare` does **not** work **[live]**; remove and re-add does.
7. ~~A result row with (−1, −1) → cleared?~~ **Deleted [live].**
8. ~~`SparaMatchlagledare` with changed discipline but the same role/responsible → no side effects?~~ **None [live].**
9. ~~A one-call substitution → 16 + linked 17? Deleting the 17 → does the 16 stay?~~ **Yes and yes [live].**
10. ~~A penalty goal → automatic #3?~~ **No #3 for a referee's penalty goal [live].**
11. Wrong password on a real account → what does `POST /Account/Login` return? (costs a failed login; once only)
12. Every test ends with a read-back confirming the original state.
13. ~~Line-up entry: new shirt number, bench → start and back~~ **Stored as sent; position kept at 0 [live].**
    Original question: stored as sent?
    Does it overwrite all eight fields? The app gives a bench player position −1; older data holds 0.
15. ~~Edit a substitution in place~~ **Ids and link kept, player and time changed [live].** Original: (`sparaUppdateratByte` [js]: two saves with the existing ids — the 17 with the incoming
    player, the 16 with the outgoing player as the *second* player, `matchdeltagareid: null`) → ids and link kept? Does the
    server store the outgoing player back in the 16's `spelareid`?
16. **Submission rules (probe another day)** — which rules does `SparaMatchGodkannDomarrapport` enforce, and with what
    `Message`? Only probe while a known blocker is in place (away captain removed → "Bortalagets matchtrupp saknar
    lagkapten."), or the report gets submitted with the error in it. The competition's fields say what may apply; 0 seems
    to mean "not checked" (Ligacupen Elit: starters 0 → 9 starters accepted). Cases: more / fewer starters than
    `tavlingantalstartadespelareigodkanddomarrapport` (needs a competition where it is 11); no responsible when
    `tavlingDomareKravForekomstAvAnsvarigLagledareIGodkandDomarrapport`; missing shirt number when
    `TavlingTrojnummerKravsIForeningensLaguppstallning`; duplicate shirt numbers; two captains; captain on the bench;
    more officials than `tavlingantalledareimatchtrupp`; final result ≠ goals; event without a minute; both captains
    missing (home or away checked first).
    **The method is not exhaustive:** a probe that returns the captain message proves nothing (the rule may be missing or
    checked later); only a *different* message proves a rule, and that it is checked before the captain. Ways further: the
    refusal's stack-trace line number (captain: `MatchWebMetoder.aspx.cs:line 1746`) most likely orders the checks, so a
    rule at a lower line is checked earlier; a rule found before the captain can itself serve as the next blocker; SvFF
    may simply have the list. Rules checked after every known blocker cannot be probed safely.
    Note: `tavlingFriaByten` (rolling substitutions) was False on the Ligacupen match whose starter limit was 0.
14. **Open, not planned:** how is a sanction before kick-off recorded (allowed by the Laws, never seen in practice)?
    Minute 0, blank or null; period 0 or 1? The library treats minute 0 with period 0 as "no minute".

## 11. Personal data

- `GetTruppdeltagareListaForLag`, `GetMatchdeltagareListaForMatchlag`, `GetMatchlagledareListaForMatchlag` and
  `GetExtern*` return **personnr**. Event `kommentar` is free text.
- **Protected identities [history][referee]:** people with *skyddade personuppgifter* appear in `domaruppdraglista` as
  `personnamn: "Personuppgifter Skyddade"` (the public web shows this too). Treat it as hidden, never as a name, or all
  protected people collapse into one "person" in statistics.
- **History depth [history]:** a referee's assignments go back to their first season. Paper-era reports (before ~2008) have
  date, teams, competition, venue, crew and final score only; reports are fully digital from about 2012.
