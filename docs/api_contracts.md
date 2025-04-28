# FOGIS API Contracts

## Introduction

This document outlines the critical API contracts that must be maintained when interacting with the FOGIS API. These contracts define the expected structure of data sent to and received from the API.

> **⚠️ WARNING: Critical API Contracts**
> The structures defined in this document represent critical API contracts that must be maintained for proper functionality. Modifying these structures without understanding the server requirements can lead to breaking changes and functionality loss.

## Critical API Endpoints

### Report Match Result

**Endpoint:** `/MatchWebMetoder.aspx/SparaMatchresultatLista`

#### Client-Facing API (Preferred Format)

The client library provides a simplified flat structure for ease of use:

```json
{
  "matchid": 123456,
  "hemmamal": 2,
  "bortamal": 1,
  "halvtidHemmamal": 1,
  "halvtidBortamal": 0
}
```

#### Server API (Required Structure)

The FOGIS server requires a nested structure that the client library automatically converts to:

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

#### Field Mapping

The client library maps between the two formats as follows:

| Client Format (Flat) | Server Format (Nested) |
|---------------------|------------------------|
| `matchid`           | `matchid` in both objects |
| `hemmamal`          | `matchlag1mal` in object with `matchresultattypid=1` |
| `bortamal`          | `matchlag2mal` in object with `matchresultattypid=1` |
| `halvtidHemmamal`   | `matchlag1mal` in object with `matchresultattypid=2` |
| `halvtidBortamal`   | `matchlag2mal` in object with `matchresultattypid=2` |

**Important Notes:**
- The API requires the nested structure with `matchresultatListaJSON` array
- Each result object must include all fields shown above
- Field names must match exactly as shown
- Numeric fields must be integers
- Boolean fields must be lowercase `false` or `true`
- `matchresultattypid` values: 1 = Full time, 2 = Half-time

> **⚠️ WARNING: Critical Structure**
> The nested structure with `matchresultatListaJSON` array is required by the FOGIS API.
> The client library handles this conversion automatically, but any direct API calls must use this structure.

### Report Match Event

**Endpoint:** `/MatchWebMetoder.aspx/SparaMatchhandelse`

**Required Structure (varies by event type):**

#### For Goals
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

#### For Cards
```json
{
  "matchid": 123456,
  "handelsekod": 20,  // Yellow card
  "minut": 35,
  "lagid": 78910,  // Team ID
  "personid": 12345,  // Player ID
  "period": 1
}
```

#### For Substitutions
```json
{
  "matchid": 123456,
  "handelsekod": 17,  // Substitution
  "minut": 65,
  "lagid": 78910,  // Team ID
  "personid": 12345,  // Player coming on
  "assisterandeid": 67890,  // Player going off
  "period": 2
}
```

**Important Notes:**
- Required fields vary by event type (see `EVENT_TYPES` constant)
- Field names must match exactly as shown
- Numeric fields must be integers
- For goals, updated score must be included

> **⚠️ WARNING: Event Type Specific Fields**
> Different event types require different fields. Always include all required fields for the specific event type.
> Missing or incorrect fields will cause the API to reject the request.

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

> **⚠️ WARNING: Type Conversion**
> The FOGIS API is strict about data types. Always ensure that:
> - IDs are converted to integers (e.g., `int(match_id)`)
> - Scores are integers, not strings
> - Boolean values are `true`/`false`, not `"true"`/`"false"`

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

## API Contract Testing Framework

The FOGIS API Client includes a comprehensive API contract testing framework to ensure that all API interactions maintain the correct data structures. This framework consists of:

1. **JSON Schema Definitions:** Each API endpoint has a corresponding JSON schema that defines the expected structure of requests and responses.

2. **Validation Functions:** The `validate_request` and `validate_response` functions validate data against these schemas.

3. **Automatic Validation:** API methods automatically validate data before sending requests and after receiving responses.

4. **Conversion Utilities:** Helper functions like `convert_flat_to_nested_match_result` ensure data is in the correct format.

### Using the API Contract Testing Framework

```python
from fogis_api_client.api_contracts import validate_request, validate_response

# Validate a request payload
try:
    validate_request('/MatchWebMetoder.aspx/SparaMatchresultatLista', payload)
    # Payload is valid
except ValidationError as e:
    # Handle validation error
    print(f"Invalid payload: {e}")

# Validate a response
try:
    validate_response('/MatchWebMetoder.aspx/GetMatchresultatlista', response_data)
    # Response is valid
except ValidationError as e:
    # Handle validation error
    print(f"Invalid response: {e}")
```

## Testing API Changes

Before submitting changes that affect API interactions:

1. Test with the actual FOGIS API
2. Verify both success and error cases
3. Test with various input formats
4. Run the API contract tests to ensure your changes maintain compatibility
5. Document any changes to expected behavior

## Common Mistakes and How to Avoid Them

### 1. Modifying Critical Data Structures

**Problem:** Changing the structure of data sent to the API can break functionality.

**Solution:**
- Always use the client library's methods rather than direct API calls
- If you need to modify API-related code, consult this documentation first
- Look for `AI-CRITICAL-SECTION` comments in the code

### 2. Incorrect Data Types

**Problem:** Sending strings instead of integers or incorrectly formatted booleans.

**Solution:**
- Explicitly convert IDs to integers: `int(match_id)`
- Use Python's native `True`/`False` for boolean values
- Use the validation functions to check your data before sending

### 3. Missing Required Fields

**Problem:** Omitting fields that the API requires.

**Solution:**
- Refer to the schemas in `api_contracts.py`
- Use the validation functions to check your data
- For event reporting, check the specific requirements for each event type

### 4. Incorrect Field Names

**Problem:** Using incorrect field names or wrong capitalization.

**Solution:**
- Copy field names exactly as shown in this documentation
- Use the client library's methods which handle field names correctly
- Test your changes thoroughly before submitting

## Visual Representation of API Contracts

### Match Result Reporting Flow

```
┌─────────────────┐     ┌───────────────────┐     ┌──────────────┐
│ Client Code     │     │ FogisApiClient    │     │ FOGIS Server │
│ (Your App)      │────▶│ (Library)         │────▶│ (API)        │
└─────────────────┘     └───────────────────┘     └──────────────┘
       │                         │                        │
       │                         │                        │
       │  Flat Structure         │  Nested Structure      │
       │  {                      │  {                     │
       │    "matchid": 123456,   │    "matchresultatListaJSON": [
       │    "hemmamal": 2,       │      { ... },          │
       │    "bortamal": 1        │      { ... }           │
       │  }                      │    ]                   │
       │                         │  }                     │
       ▼                         ▼                        ▼
```

This diagram illustrates how the client code uses a simplified flat structure, which the library then converts to the nested structure required by the FOGIS server.
