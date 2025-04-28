# FOGIS API Contracts

## Introduction

This document outlines the critical API contracts that must be maintained when interacting with the FOGIS API. These contracts define the expected structure of data sent to and received from the API.

## Critical API Endpoints

### Report Match Result

**Endpoint:** `/MatchWebMetoder.aspx/SparaMatchresultatLista`

**Required Structure:**
```json
{
  "matchresultatListaJSON": [
    {
      "matchid": 123456,
      "matchresultattypid": 1,  // Full time
      "matchlag1mal": 2,
      "matchlag2mal": 1,
      "wo": false,
      "ow": false,
      "ww": false
    },
    {
      "matchid": 123456,
      "matchresultattypid": 2,  // Half-time
      "matchlag1mal": 1,
      "matchlag2mal": 0,
      "wo": false,
      "ow": false,
      "ww": false
    }
  ]
}
```

**Important Notes:**
- The API requires the nested structure with `matchresultatListaJSON` array
- Each result object must include all fields shown above
- Field names must match exactly as shown
- Numeric fields must be integers
- Boolean fields must be lowercase `false` or `true`
- `matchresultattypid` values: 1 = Full time, 2 = Half-time

### Report Match Event

**Endpoint:** `/MatchWebMetoder.aspx/SparaMatchhandelse`

**Required Structure (varies by event type):**

For goals:
```json
{
  "matchid": 123456,
  "handelsekod": 6,  // Regular goal
  "minut": 35,
  "lagid": 78910,  // Team ID
  "personid": 12345,  // Player ID
  "period": 1,
  "resultatHemma": 1,
  "resultatBorta": 0
}
```

For cards:
```json
{
  "matchid": 123456,
  "handelsekod": 2,  // Yellow card
  "minut": 35,
  "lagid": 78910,  // Team ID
  "personid": 12345,  // Player ID
  "period": 1
}
```

**Important Notes:**
- Required fields vary by event type (see `EVENT_TYPES` constant)
- Field names must match exactly as shown
- Numeric fields must be integers
- For goals, updated score must be included

### Mark Reporting Finished

**Endpoint:** `/MatchWebMetoder.aspx/SparaMatchGodkannDomarrapport`

**Required Structure:**
```json
{
  "matchid": 123456
}
```

**Important Notes:**
- This is the final step in the referee reporting workflow
- The match ID must be an integer
- This should only be called after all match events and results are reported

## Common API Requirements

For all API endpoints:

1. **Authentication:** All requests require valid authentication cookies
2. **Content-Type:** All requests use `application/json` content type
3. **Field Names:** Field names are case-sensitive
4. **Numeric Values:** All numeric values should be sent as integers, not strings
5. **Boolean Values:** Boolean values should be sent as `true` or `false`, not strings

## Error Handling

The API may return various error responses:

- **400 Bad Request:** Invalid data structure or missing required fields
- **401 Unauthorized:** Invalid or expired authentication
- **403 Forbidden:** Insufficient permissions
- **500 Internal Server Error:** Server-side issues

Always check response status and handle errors appropriately.

## Backward Compatibility

When making changes to the API client:

1. Maintain support for existing input formats
2. Add new features in a backward-compatible way
3. If breaking changes are necessary, use deprecation warnings first
4. Document any changes to API contracts

## Testing API Changes

Before submitting changes that affect API interactions:

1. Test with the actual FOGIS API
2. Verify both success and error cases
3. Test with various input formats
4. Document any changes to expected behavior
