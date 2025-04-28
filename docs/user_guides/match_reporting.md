# Match Reporting Guide

This guide provides step-by-step instructions for reporting match events, results, and completing match reports using the FOGIS API Client.

## Prerequisites

- FOGIS API Client installed
- Valid FOGIS credentials with referee permissions
- Match ID for the match you want to report

## Step 1: Initialize the Client and Authenticate

First, initialize the FOGIS API Client and authenticate:

```python
import logging
from fogis_api_client import FogisApiClient, FogisLoginError, FogisAPIRequestError

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize the client
username = "your_fogis_username"
password = "your_fogis_password"

try:
    client = FogisApiClient(username, password)
    client.login()  # Explicitly authenticate
    print("Authentication successful")
except FogisLoginError as e:
    print(f"Authentication failed: {e}")
    exit(1)
```

## Step 2: Fetch Match Details

Before reporting events, it's a good idea to fetch the match details to ensure you have the correct match ID and to get information about the teams:

```python
match_id = 123456  # Replace with your match ID

try:
    match = client.fetch_match_json(match_id)
    print(f"Match: {match['hemmalag']} vs {match['bortalag']}")
    print(f"Date: {match['datum']}")
    print(f"Venue: {match['arena']}")

    # Store team IDs for later use
    home_team_id = match['hemmalagid']
    away_team_id = match['bortalagid']

except FogisAPIRequestError as e:
    print(f"Failed to fetch match details: {e}")
    exit(1)
```

## Step 3: Fetch Players

To report player-specific events (like goals or cards), you need to fetch the player information:

```python
try:
    players = client.fetch_match_players_json(match_id)

    home_players = players.get('hemmalag', [])
    away_players = players.get('bortalag', [])

    print(f"Home team has {len(home_players)} players")
    print(f"Away team has {len(away_players)} players")

    # Print player information for reference
    print("\nHome Team Players:")
    for player in home_players:
        print(f"ID: {player['personid']}, Name: {player['fornamn']} {player['efternamn']}, Number: {player.get('tshirt', 'N/A')}")

    print("\nAway Team Players:")
    for player in away_players:
        print(f"ID: {player['personid']}, Name: {player['fornamn']} {player['efternamn']}, Number: {player.get('tshirt', 'N/A')}")

except FogisAPIRequestError as e:
    print(f"Failed to fetch players: {e}")
    exit(1)
```

## Step 4: Report Match Events

Now you can report match events such as goals, cards, and substitutions:

### Reporting a Goal

```python
# Example: Report a goal by a home team player
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

try:
    response = client.report_match_event(goal_event)
    if response.get('success', False):
        print(f"Goal reported successfully. Event ID: {response.get('matchhandelseid')}")
    else:
        print("Failed to report goal")
except (FogisAPIRequestError, FogisDataError) as e:
    print(f"Error reporting goal: {e}")
```

### Reporting a Yellow Card

```python
# Example: Report a yellow card for an away team player
card_event = {
    "matchid": match_id,
    "handelsekod": 20,  # Yellow card
    "minut": 42,
    "lagid": away_team_id,
    "personid": away_players[0]['personid'],
    "period": 1
}

try:
    response = client.report_match_event(card_event)
    if response.get('success', False):
        print(f"Yellow card reported successfully. Event ID: {response.get('matchhandelseid')}")
    else:
        print("Failed to report yellow card")
except (FogisAPIRequestError, FogisDataError) as e:
    print(f"Error reporting yellow card: {e}")
```

### Reporting a Substitution

```python
# Example: Report a substitution for the home team
substitution_event = {
    "matchid": match_id,
    "handelsekod": 17,  # Substitution
    "minut": 65,
    "lagid": home_team_id,
    "personid": home_players[1]['personid'],  # Player coming on
    "assisterandeid": home_players[0]['personid'],  # Player going off
    "period": 2
}

try:
    response = client.report_match_event(substitution_event)
    if response.get('success', False):
        print(f"Substitution reported successfully. Event ID: {response.get('matchhandelseid')}")
    else:
        print("Failed to report substitution")
except (FogisAPIRequestError, FogisDataError) as e:
    print(f"Error reporting substitution: {e}")
```

## Step 5: Report Match Result

After reporting all events, you need to report the final match result. The client library supports two formats for reporting match results, but the flat structure is recommended for most cases.

### Using the Flat Structure (Recommended)

```python
# Example: Report a 2-1 result with 1-0 at halftime
result_data = {
    "matchid": match_id,
    "hemmamal": 2,  # Full-time home team score
    "bortamal": 1,  # Full-time away team score
    "halvtidHemmamal": 1,  # Half-time home team score
    "halvtidBortamal": 0   # Half-time away team score
}

try:
    response = client.report_match_result(result_data)
    if response.get('success', False):
        print("Match result reported successfully")
    else:
        print("Failed to report match result")
except (FogisAPIRequestError, FogisDataError) as e:
    print(f"Error reporting match result: {e}")
```

> **⚠️ IMPORTANT**: The FOGIS API requires a specific nested structure, but the client library automatically converts the flat structure to the required format. Always use the client library's `report_match_result` method rather than making direct API calls.

### Using the Nested Structure (Legacy)

For backward compatibility, the client library also supports the nested structure that matches the API's requirements:

```python
# Example: Report a 2-1 result with 1-0 at halftime using the nested structure
result_data = {
    "matchresultatListaJSON": [
        {
            "matchid": match_id,
            "matchresultattypid": 1,  # Full time
            "matchlag1mal": 2,  # Full-time home team score
            "matchlag2mal": 1,  # Full-time away team score
            "wo": False,
            "ow": False,
            "ww": False
        },
        {
            "matchid": match_id,
            "matchresultattypid": 2,  # Half-time
            "matchlag1mal": 1,  # Half-time home team score
            "matchlag2mal": 0,  # Half-time away team score
            "wo": False,
            "ow": False,
            "ww": False
        }
    ]
}

try:
    response = client.report_match_result(result_data)
    if response.get('success', False):
        print("Match result reported successfully")
    else:
        print("Failed to report match result")
except (FogisAPIRequestError, FogisDataError) as e:
    print(f"Error reporting match result: {e}")
```

For more details on the API contracts and data structures, see the [API Contracts Guide](api_contracts.md).

## Step 6: Mark Reporting as Finished

The final step is to mark the match reporting as finished:

```python
try:
    response = client.mark_reporting_finished(match_id)
    if response.get('success', False):
        print("Match reporting marked as finished successfully")
    else:
        print("Failed to mark match reporting as finished")
except (FogisAPIRequestError, FogisDataError) as e:
    print(f"Error marking match reporting as finished: {e}")
```

## Complete Example

Here's a complete example that puts all the steps together:

```python
import logging
from fogis_api_client import FogisApiClient, FogisLoginError, FogisAPIRequestError, FogisDataError

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize the client
username = "your_fogis_username"
password = "your_fogis_password"
match_id = 123456  # Replace with your match ID

try:
    # Step 1: Initialize and authenticate
    client = FogisApiClient(username, password)
    client.login()
    print("Authentication successful")

    # Step 2: Fetch match details
    match = client.fetch_match_json(match_id)
    print(f"Match: {match['hemmalag']} vs {match['bortalag']}")
    home_team_id = match['hemmalagid']
    away_team_id = match['bortalagid']

    # Step 3: Fetch players
    players = client.fetch_match_players_json(match_id)
    home_players = players.get('hemmalag', [])
    away_players = players.get('bortalag', [])

    # Step 4: Report match events

    # First half events
    # Home team goal at 35'
    goal1_event = {
        "matchid": match_id,
        "handelsekod": 6,  # Regular goal
        "minut": 35,
        "lagid": home_team_id,
        "personid": home_players[0]['personid'],
        "period": 1,
        "resultatHemma": 1,
        "resultatBorta": 0
    }
    client.report_match_event(goal1_event)
    print("First goal reported")

    # Away team yellow card at 42'
    card_event = {
        "matchid": match_id,
        "handelsekod": 20,  # Yellow card
        "minut": 42,
        "lagid": away_team_id,
        "personid": away_players[0]['personid'],
        "period": 1
    }
    client.report_match_event(card_event)
    print("Yellow card reported")

    # Second half events
    # Home team substitution at 65'
    sub_event = {
        "matchid": match_id,
        "handelsekod": 17,  # Substitution
        "minut": 65,
        "lagid": home_team_id,
        "personid": home_players[1]['personid'],  # Player coming on
        "assisterandeid": home_players[0]['personid'],  # Player going off
        "period": 2
    }
    client.report_match_event(sub_event)
    print("Substitution reported")

    # Home team second goal at 75'
    goal2_event = {
        "matchid": match_id,
        "handelsekod": 6,  # Regular goal
        "minut": 75,
        "lagid": home_team_id,
        "personid": home_players[1]['personid'],
        "period": 2,
        "resultatHemma": 2,
        "resultatBorta": 0
    }
    client.report_match_event(goal2_event)
    print("Second goal reported")

    # Away team goal at 85'
    goal3_event = {
        "matchid": match_id,
        "handelsekod": 6,  # Regular goal
        "minut": 85,
        "lagid": away_team_id,
        "personid": away_players[0]['personid'],
        "period": 2,
        "resultatHemma": 2,
        "resultatBorta": 1
    }
    client.report_match_event(goal3_event)
    print("Third goal reported")

    # Step 5: Report match result
    result_data = {
        "matchid": match_id,
        "hemmamal": 2,
        "bortamal": 1,
        "halvtidHemmamal": 1,
        "halvtidBortamal": 0
    }
    client.report_match_result(result_data)
    print("Match result reported")

    # Step 6: Mark reporting as finished
    client.mark_reporting_finished(match_id)
    print("Match reporting marked as finished")

    print("Match reporting completed successfully")

except FogisLoginError as e:
    print(f"Authentication failed: {e}")
except FogisAPIRequestError as e:
    print(f"API request error: {e}")
except FogisDataError as e:
    print(f"Data error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Tips and Best Practices

1. **Always verify match details** before reporting events to ensure you're working with the correct match.
2. **Report events in chronological order** to maintain consistency in the match timeline.
3. **Update scores correctly** when reporting goals to ensure the final result matches the reported goals.
4. **Handle errors gracefully** to prevent incomplete match reports.
5. **Test with non-production matches** if possible before using in real matches.
6. **Save event IDs** returned from the API to allow for corrections if needed.

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Ensure your username and password are correct
   - Check if your account has the necessary permissions
   - Verify that your session hasn't expired (use `client.validate_cookies()` to check)

2. **Missing Player Information**
   - Ensure the match has been properly set up in FOGIS
   - Verify that team rosters have been submitted
   - Check if you have the correct match ID

3. **Event Reporting Failures**
   - Check that all required fields are included in the event data
   - Ensure player IDs are correct and are integers, not strings
   - Verify that the event type code is valid (see `EVENT_TYPES` constant)
   - For goals, make sure you include the updated score (`resultatHemma` and `resultatBorta`)
   - For substitutions, ensure both `personid` (player coming on) and `assisterandeid` (player going off) are included

4. **Result Reporting Failures**
   - Ensure the reported goals match the final result
   - Check that both full-time and half-time scores are included
   - Verify that scores are integers, not strings
   - If using the nested structure, ensure the `matchresultatListaJSON` array is correctly formatted
   - Check that the match ID is correct and is an integer

5. **Unable to Mark Reporting as Finished**
   - Ensure all required match information has been reported
   - Check for any validation errors in the match report
   - Verify that you've reported both the match result and all events

### Debugging API Contracts

If you're experiencing issues with API contracts, you can use the validation functions to check your data:

```python
from fogis_api_client.api_contracts import validate_request

# Validate match result data before sending
try:
    validate_request('/MatchWebMetoder.aspx/SparaMatchresultatLista', result_data)
    print("Data is valid")
except ValidationError as e:
    print(f"Invalid data: {e}")
```

### Common API Contract Mistakes

1. **Using Strings Instead of Integers**
   ```python
   # Incorrect
   result_data = {
       "matchid": "123456",  # String instead of integer
       "hemmamal": "2",     # String instead of integer
       "bortamal": "1"      # String instead of integer
   }

   # Correct
   result_data = {
       "matchid": 123456,  # Integer
       "hemmamal": 2,     # Integer
       "bortamal": 1      # Integer
   }
   ```

2. **Missing Required Fields**
   ```python
   # Incorrect (missing halvtid scores)
   result_data = {
       "matchid": 123456,
       "hemmamal": 2,
       "bortamal": 1
       # Missing halvtidHemmamal and halvtidBortamal
   }

   # Correct
   result_data = {
       "matchid": 123456,
       "hemmamal": 2,
       "bortamal": 1,
       "halvtidHemmamal": 1,
       "halvtidBortamal": 0
   }
   ```

3. **Incorrect Field Names**
   ```python
   # Incorrect (wrong field names)
   result_data = {
       "match_id": 123456,    # Underscore instead of camelCase
       "homescore": 2,       # Wrong field name
       "awayscore": 1        # Wrong field name
   }

   # Correct
   result_data = {
       "matchid": 123456,
       "hemmamal": 2,
       "bortamal": 1
   }
   ```

For more detailed information about API contracts, see the [API Contracts Guide](api_contracts.md) and the [API Contracts Documentation](../api_contracts.md).
