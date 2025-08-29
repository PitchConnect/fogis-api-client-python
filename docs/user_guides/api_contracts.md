# API Contracts Guide

This guide explains how to work with the FOGIS API contracts and avoid common pitfalls when interacting with the API.

## Understanding API Contracts

API contracts define the expected structure of data sent to and received from the FOGIS API. These contracts are critical for ensuring proper functionality, and modifying them without understanding the server requirements can lead to breaking changes.

## Match Result Reporting

### Flat vs. Nested Structure

The FOGIS API Client supports two different formats for reporting match results:

1. **Flat Structure (Preferred)**: A simplified format that's easier to use and understand
2. **Nested Structure**: The format required by the FOGIS API server

#### Using the Flat Structure (Recommended)

```python
result_data = {
    "matchid": 123456,
    "hemmamal": 2,  # Full-time home team score
    "bortamal": 1,  # Full-time away team score
    "halvtidHemmamal": 1,  # Half-time home team score
    "halvtidBortamal": 0   # Half-time away team score
}

client.report_match_result(result_data)
```

#### Using the Nested Structure (Legacy)

```python
result_data = {
    "matchresultatListaJSON": [
        {
            "matchid": 123456,
            "matchresultattypid": 1,  # Full time
            "matchlag1mal": 2,
            "matchlag2mal": 1,
            "wo": False,
            "ow": False,
            "ww": False
        },
        {
            "matchid": 123456,
            "matchresultattypid": 2,  # Half-time
            "matchlag1mal": 1,
            "matchlag2mal": 0,
            "wo": False,
            "ow": False,
            "ww": False
        }
    ]
}

client.report_match_result(result_data)
```

> **⚠️ WARNING**: The FOGIS API requires the nested structure. The client library automatically converts the flat structure to the nested structure, but if you're making direct API calls, you must use the nested structure.

### Field Mapping

The client library maps between the two formats as follows:

| Client Format (Flat) | Server Format (Nested) |
|---------------------|------------------------|
| `matchid`           | `matchid` in both objects |
| `hemmamal`          | `matchlag1mal` in object with `matchresultattypid=1` |
| `bortamal`          | `matchlag2mal` in object with `matchresultattypid=1` |
| `halvtidHemmamal`   | `matchlag1mal` in object with `matchresultattypid=2` |
| `halvtidBortamal`   | `matchlag2mal` in object with `matchresultattypid=2` |

## Event Reporting

Different event types require different fields. Always include all required fields for the specific event type.

### Reporting a Goal

```python
goal_event = {
    "matchid": match_id,
    "handelsekod": 6,  # Regular goal (see EVENT_TYPES for other goal types)
    "minut": 35,  # Minute when the goal was scored
    "lagid": home_team_id,
    "personid": home_players[0]['personid'],  # ID of the player who scored
    "period": 1,  # 1 for first half, 2 for second half
    "resultatHemma": 1,  # Updated score for home team
    "resultatBorta": 0   # Updated score for away team
}

client.report_match_event(goal_event)
```

> **⚠️ IMPORTANT**: For goals, you must include the updated score (`resultatHemma` and `resultatBorta`).

### Reporting a Card

```python
card_event = {
    "matchid": match_id,
    "handelsekod": 20,  # Yellow card
    "minut": 42,
    "lagid": away_team_id,
    "personid": away_players[0]['personid'],
    "period": 1
}

client.report_match_event(card_event)
```

### Reporting a Substitution

```python
substitution_event = {
    "matchid": match_id,
    "handelsekod": 17,  # Substitution
    "minut": 65,
    "lagid": home_team_id,
    "personid": home_players[1]['personid'],  # Player coming on
    "assisterandeid": home_players[0]['personid'],  # Player going off
    "period": 2
}

client.report_match_event(substitution_event)
```

> **⚠️ IMPORTANT**: For substitutions, you must include both the player coming on (`personid`) and the player going off (`assisterandeid`).

## Common Mistakes and How to Avoid Them

### 1. Modifying Critical Data Structures

**Problem:** Changing the structure of data sent to the API can break functionality.

**Solution:**
- Always use the client library's methods rather than direct API calls
- If you need to modify API-related code, consult the API contracts documentation first
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
- Copy field names exactly as shown in the documentation
- Use the client library's methods which handle field names correctly
- Test your changes thoroughly before submitting

## Validation Functions

The FOGIS API Client includes validation functions to help ensure your data is correctly formatted:

```python
from fogis_api_client.api_contracts import validate_request

# Validate a request payload
try:
    validate_request('/MatchWebMetoder.aspx/SparaMatchresultatLista', payload)
    # Payload is valid
except ValidationError as e:
    # Handle validation error
    print(f"Invalid payload: {e}")
```

## Troubleshooting

### API Returns Error 400

This usually means the data structure is incorrect. Check:
- All required fields are included
- Field names are correct (including capitalization)
- Data types are correct (integers for IDs and scores, booleans for flags)

### Match Result Not Saving

If the match result isn't saving correctly, check:
- The match ID is correct
- The scores are integers, not strings
- For the flat structure, ensure you're using the correct field names (`hemmamal`, `bortamal`, etc.)
- For the nested structure, ensure the `matchresultatListaJSON` array is correctly formatted

### Events Not Appearing

If events aren't appearing in the match report, check:
- The event type code (`handelsekod`) is correct
- All required fields for that event type are included
- The player IDs are correct
- The team ID is correct

## Further Reading

For more detailed information about API contracts, see:
- [API Contracts Documentation](../api_contracts.md)
- [API Reference](../api_reference.md)
