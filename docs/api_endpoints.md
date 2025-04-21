# FOGIS API Endpoints Reference

This document provides a reference for all the API endpoints used in the FOGIS API Client. This is intended to help prevent issues with incorrect endpoint URLs and to make it easier to fix problems if they occur in the future.

## Base URL

All endpoints are relative to the base URL:

```
https://fogis.svenskfotboll.se/mdk
```

## Authentication Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/Login.aspx?ReturnUrl=%2fmdk%2f` | POST | Authenticates a user | `ctl00$MainContent$UserName`, `ctl00$MainContent$Password`, `ctl00$MainContent$LoginButton` |

## Match Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/MatchWebMetoder.aspx/GetMatcherAttRapportera` | POST | Fetches the list of matches | `filter`: Object with date range and other filters |
| `/MatchWebMetoder.aspx/GetMatch` | POST | Fetches detailed information for a specific match | `matchid`: Integer |
| `/MatchWebMetoder.aspx/GetMatchdeltagareLista` | POST | Fetches the list of players for a match | `matchid`: Integer |
| `/MatchWebMetoder.aspx/GetMatchfunktionarerLista` | POST | Fetches the list of officials for a match | `matchid`: Integer |
| `/MatchWebMetoder.aspx/GetMatchhandelselista` | POST | Fetches the list of events for a match | `matchid`: Integer |
| `/MatchWebMetoder.aspx/GetMatchresultatlista` | POST | Fetches the match result | `matchid`: Integer |
| `/MatchWebMetoder.aspx/ClearMatchEvents` | POST | Clears all events for a match | `matchid`: Integer |
| `/MatchWebMetoder.aspx/SparaMatchGodkannDomarrapport` | POST | Marks a match report as finished | `matchid`: Integer |

## Team Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/MatchWebMetoder.aspx/GetMatchdeltagareListaForMatchlag` | POST | Fetches the list of players for a team | `matchlagid`: Integer |
| `/MatchWebMetoder.aspx/GetMatchlagledareListaForMatchlag` | POST | Fetches the list of officials for a team | `matchlagid`: Integer |

## Event Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/MatchWebMetoder.aspx/SparaMatchhandelse` | POST | Reports a match event | Event data object |
| `/MatchWebMetoder.aspx/RaderaMatchhandelse` | POST | Deletes a match event | `matchhandelseid`: Integer |

## Result Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/MatchWebMetoder.aspx/SparaMatchresultatLista` | POST | Reports match results | Result data object |

## Official Action Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/MatchWebMetoder.aspx/SparaMatchlagledare` | POST | Reports team official disciplinary action | Action data object |

## Payload Structures

### Match List Filter

```json
{
  "filter": {
    "datumFran": "YYYY-MM-DD",  // Start date
    "datumTill": "YYYY-MM-DD",  // End date
    "datumTyp": 0,              // Date type filter
    "typ": "alla",              // Match type
    "status": ["avbruten", "uppskjuten", "installd"],  // Match status
    "alderskategori": [1, 2, 3, 4, 5],  // Age categories
    "kon": [3, 2, 4],           // Gender categories
    "sparadDatum": "YYYY-MM-DD" // Saved date
  }
}
```

## Common Issues and Solutions

### Incorrect Endpoint Names

If you encounter 404 or 500 errors when making API requests, check that you're using the correct endpoint names. The FOGIS API uses a mix of Swedish and English in its endpoint names, which can be confusing.

Common patterns:
- GET operations typically use the prefix `Get` (not `Hamta`)
- SAVE operations typically use the prefix `Spara`
- DELETE operations typically use the prefix `Radera`

### Authentication Issues

If you're getting authentication errors:
1. Check that your cookies are valid
2. Try logging in again with username and password
3. Verify that the login form field names haven't changed

### Payload Structure Issues

If you're getting 500 errors when making API requests:
1. Check that your payload structure matches what the API expects
2. Ensure that IDs are properly converted to integers
3. Verify that date formats are correct (YYYY-MM-DD)

## Version History

This document was created to prevent issues with incorrect endpoint URLs after discovering that several endpoints had been incorrectly changed from their working versions.

- **v0.2.1**: Fixed login redirect URL handling and corrected all API endpoint URLs
- **v0.2.0**: Added mock FOGIS API server for integration tests
- **v0.1.0**: Initial release with working endpoints
- **v0.0.5**: Last known good version before endpoint issues
