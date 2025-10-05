# API Client to Mock Server Endpoint Mapping Reference

**Quick reference for developers**

---

## Read Operations (Implemented in Both)

| Client Method | HTTP Method | Mock Endpoint | Request Params | Response Format | Status |
|---------------|-------------|---------------|----------------|-----------------|--------|
| `login()` | POST | `/mdk/Login.aspx` | Form data: username, password | Cookies + redirect | ✅ |
| `fetch_matches_list_json()` | POST | `/mdk/MatchWebMetoder.aspx/GetMatcherAttRapportera` | `{"filter": {...}}` | `{"d": json_string}` | ✅ |
| `fetch_team_players_json()` | POST | `/mdk/MatchWebMetoder.aspx/GetMatchdeltagareListaForMatchlag` | `{"matchlagid": int}` | `{"d": json_string}` | ✅ |
| `fetch_team_officials_json()` | POST | `/mdk/MatchWebMetoder.aspx/GetMatchlagledareListaForMatchlag` | `{"matchlagid": int}` | `{"d": json_string}` | ✅ |
| `fetch_match_events_json()` | POST | `/mdk/MatchWebMetoder.aspx/GetMatchhandelselista` | `{"matchid": int}` | `{"d": json_string}` | ✅ |
| `fetch_match_result_json()` | POST | `/mdk/MatchWebMetoder.aspx/GetMatchresultatlista` | `{"matchid": int}` | `{"d": result_data}` | ⚠️ Format inconsistency |

---

## Write Operations (Mock Only - NOT in Client)

| Operation | HTTP Method | Mock Endpoint | Request Params | Response Format | Client Method |
|-----------|-------------|---------------|----------------|-----------------|---------------|
| Save match event | POST | `/mdk/MatchWebMetoder.aspx/SparaMatchhandelse` | Event data object | `{"d": json_string}` | ❌ **MISSING** |
| Delete match event | POST | `/mdk/MatchWebMetoder.aspx/RaderaMatchhandelse` | `{"matchhandelseid": int}` | `{"d": json_string}` | ❌ **MISSING** |
| Report match result | POST | `/mdk/MatchWebMetoder.aspx/SparaMatchresultatLista` | Result data object | `{"d": json_string}` | ❌ **MISSING** |
| Mark reporting finished | POST | `/mdk/MatchWebMetoder.aspx/SparaMatchGodkannDomarrapport` | `{"matchid": int}` | `{"d": json_string}` | ❌ **MISSING** |
| Mark reporting finished (alt) | POST | `/mdk/Fogis/Match/SparaMatchGodkannDomarrapport` | `{"matchid": int}` | `{"d": json_string}` | ❌ **MISSING** |
| Save match participant | POST | `/mdk/MatchWebMetoder.aspx/SparaMatchdeltagare` | Participant data | `{"d": json_string}` | ❌ **MISSING** |
| Save team official | POST | `/mdk/MatchWebMetoder.aspx/SparaMatchlagledare` | Official data | `{"d": json_string}` | ❌ **MISSING** |
| Clear match events | POST | `/mdk/MatchWebMetoder.aspx/RensaMatchhandelser` | `{"matchid": int}` | `{"d": json_string}` | ❌ **MISSING** |
| Clear match events (alt) | POST | `/mdk/Fogis/Match/ClearMatchEvents` | `{"matchid": int}` | `{"d": json_string}` | ❌ **MISSING** |
| Clear match events (alt2) | POST | `/mdk/MatchWebMetoder.aspx/ClearMatchEvents` | `{"matchid": int}` | `{"d": json_string}` | ❌ **MISSING** |

---

## Legacy Endpoints (Mock Only - Deprecated)

| Operation | HTTP Method | Mock Endpoint | Modern Equivalent | Status |
|-----------|-------------|---------------|-------------------|--------|
| Fetch match list | POST | `/mdk/MatchWebMetoder.aspx/HamtaMatchLista` | `GetMatcherAttRapportera` | 🟡 Legacy |
| Fetch match details | POST | `/mdk/MatchWebMetoder.aspx/HamtaMatch` | `GetMatch` | 🟡 Legacy |
| Fetch match players | POST | `/mdk/MatchWebMetoder.aspx/HamtaMatchSpelare` | `GetMatchdeltagareLista` | 🟡 Legacy |
| Fetch match officials | POST | `/mdk/MatchWebMetoder.aspx/HamtaMatchFunktionarer` | `GetMatchfunktionarerLista` | 🟡 Legacy |
| Fetch match events | POST | `/mdk/MatchWebMetoder.aspx/HamtaMatchHandelser` | `GetMatchhandelselista` | 🟡 Legacy |

---

## Alternative Endpoints (Mock Only - Not Used by Client)

| Operation | HTTP Method | Mock Endpoint | Primary Endpoint | Notes |
|-----------|-------------|---------------|------------------|-------|
| Get match details | POST | `/mdk/MatchWebMetoder.aspx/GetMatch` | Client uses match list | Alternative API |
| Get match players | POST | `/mdk/MatchWebMetoder.aspx/GetMatchdeltagareLista` | `GetMatchdeltagareListaForMatchlag` | Match-level vs team-level |
| Get match officials | POST | `/mdk/MatchWebMetoder.aspx/GetMatchfunktionarerLista` | `GetMatchlagledareListaForMatchlag` | Match-level vs team-level |
| Get match result | POST | `/mdk/MatchWebMetoder.aspx/GetMatchresultat` | `GetMatchresultatlista` | Single vs list |

---

## Utility Endpoints (Mock Only)

| Operation | HTTP Method | Mock Endpoint | Purpose | Client Access |
|-----------|-------------|---------------|---------|---------------|
| Health check | GET | `/health` | Server health status | ❌ Not used |
| Hello world | GET | `/hello` | Test endpoint | ❌ Not used (client has `hello_world()` method) |
| Request history | GET | `/request-history` | Debugging | ❌ Not used |
| Clear history | POST | `/clear-request-history` | Debugging | ❌ Not used |
| Dashboard | GET | `/mdk/` | Post-login page | ❌ Not used |

---

## CLI API Endpoints (Mock Only)

| Operation | HTTP Method | Mock Endpoint | Purpose |
|-----------|-------------|---------------|---------|
| Get status | GET | `/api/cli/status` | Server status |
| Get history | GET | `/api/cli/history` | Request history |
| Clear history | DELETE | `/api/cli/history` | Clear history |
| Get validation | GET | `/api/cli/validation` | Validation status |
| Set validation | POST | `/api/cli/validation` | Enable/disable validation |
| Shutdown | POST | `/api/cli/shutdown` | Stop server |

---

## OAuth Endpoints (Mock Only)

| Operation | HTTP Method | Mock Endpoint | Purpose | Client Support |
|-----------|-------------|---------------|---------|----------------|
| Authorize | GET | `/oauth/authorize` | OAuth authorization | ✅ Client handles OAuth |
| Callback | GET | `/oauth/callback` | OAuth callback | ✅ Client handles OAuth |
| Token exchange | POST | `/oauth/token` | Get access token | ✅ Client handles OAuth |

---

## Convenience Methods (Client Only - No Direct Endpoint)

These client methods aggregate data from multiple endpoints or provide derived data:

| Client Method | Description | Underlying Endpoints |
|---------------|-------------|---------------------|
| `hello_world()` | Returns static string | None (utility method) |
| `get_match_details()` | Extract match from list | `GetMatcherAttRapportera` |
| `get_match_players()` | Aggregate team players | `GetMatchdeltagareListaForMatchlag` (2x) |
| `get_match_officials()` | Aggregate team officials | `GetMatchlagledareListaForMatchlag` (2x) |
| `fetch_complete_match()` | Fetch all match data | Multiple endpoints |
| `get_recent_matches()` | Filter matches by date | `GetMatcherAttRapportera` |
| `get_match_summary()` | Summarize match info | `GetMatcherAttRapportera` |
| `get_match_events_by_type()` | Categorize events | `GetMatchhandelselista` |
| `get_team_statistics()` | Calculate team stats | Multiple endpoints |
| `find_matches()` | Search matches | `GetMatcherAttRapportera` |
| `get_matches_requiring_action()` | Filter actionable matches | `GetMatcherAttRapportera` |

---

## Response Format Patterns

### Pattern 1: JSON String in "d" field
```json
{
  "d": "{\"key\": \"value\"}"
}
```
**Used by:**
- `GetMatcherAttRapportera`
- `GetMatchdeltagareListaForMatchlag`
- `GetMatchlagledareListaForMatchlag`
- `GetMatchhandelselista`
- Most write operations

### Pattern 2: Direct Object in "d" field
```json
{
  "d": {"key": "value"}
}
```
**Used by:**
- `GetMatchresultatlista` (⚠️ inconsistent)
- `HamtaMatchHandelser` (legacy)

### Pattern 3: Direct Array in "d" field
```json
{
  "d": [{"item": 1}, {"item": 2}]
}
```
**Used by:**
- Some legacy endpoints

---

## Request Parameter Patterns

### Pattern 1: Match ID
```json
{"matchid": 123456}
```
**Used by:**
- `GetMatchhandelselista`
- `GetMatchresultatlista`
- Write operations

### Pattern 2: Team ID
```json
{"matchlagid": 1000}
```
**Used by:**
- `GetMatchdeltagareListaForMatchlag`
- `GetMatchlagledareListaForMatchlag`

### Pattern 3: Filter Object
```json
{
  "filter": {
    "datumFran": "2025-01-01",
    "datumTill": "2025-12-31",
    "datumTyp": 0,
    "typ": "alla",
    "status": ["avbruten", "uppskjuten", "installd"],
    "alderskategori": [1, 2, 3, 4, 5],
    "kon": [3, 2, 4],
    "sparadDatum": "2025-10-05"
  }
}
```
**Used by:**
- `GetMatcherAttRapportera`

---

## Authentication Requirements

### All Endpoints Require Authentication EXCEPT:
- `/mdk/Login.aspx` (GET)
- `/health`
- `/hello`
- `/oauth/*` endpoints

### Authentication Methods Supported:
1. **ASP.NET Cookies:**
   - `FogisMobilDomarKlient.ASPXAUTH`
   - `ASP.NET_SessionId`

2. **OAuth 2.0:**
   - Bearer token in `Authorization` header
   - Hybrid mode: OAuth login + ASP.NET cookies

3. **Session:**
   - Flask session with `authenticated=True`

---

## Quick Troubleshooting

### Issue: 401 Unauthorized
- **Check:** Cookies are set correctly
- **Check:** Session is authenticated
- **Check:** OAuth token is valid

### Issue: 400 Bad Request
- **Check:** Request parameters match expected format
- **Check:** Validation is enabled in mock
- **Check:** Required fields are present

### Issue: Response parsing error
- **Check:** Response format (JSON string vs direct object)
- **Check:** "d" field exists in response
- **Check:** Data type matches expectation

---

## File Locations

- **API Client:** `fogis_api_client/public_api_client.py`
- **Mock Server:** `integration_tests/mock_fogis_server.py`
- **Request Validator:** `integration_tests/request_validator.py`
- **Data Factory:** `integration_tests/sample_data_factory.py`

---

**Last Updated:** 2025-10-05
**Maintained by:** Development Team
