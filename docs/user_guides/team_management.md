# Team Management Guide

This guide provides step-by-step instructions for fetching and managing team and player information using the FOGIS API Client.

## Prerequisites

- FOGIS API Client installed
- Valid FOGIS credentials with appropriate permissions
- Team ID for the team you want to manage

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

## Step 2: Fetch Team Players

To get information about players in a team:

> **Note**: The `team_id` parameter must be a match-specific team ID (`matchlagid`), not just the general team ID. You can get this ID from a match object's `hemmalagid` or `bortalagid` properties.

```python
team_id = 12345  # Replace with your team's match-specific ID (matchlagid)

try:
    team_players_response = client.fetch_team_players_json(team_id)

    # The response contains a 'spelare' key with a list of players
    players = team_players_response.get('spelare', [])

    print(f"Team has {len(players)} players")

    # Print player information
    for player in players:
        player_id = player.get('personid')
        first_name = player.get('fornamn', '')
        last_name = player.get('efternamn', '')
        jersey_number = player.get('tshirt', 'N/A')
        position = player.get('position', 'N/A')

        print(f"ID: {player_id}, Name: {first_name} {last_name}, Number: {jersey_number}, Position: {position}")

except FogisAPIRequestError as e:
    print(f"Failed to fetch team players: {e}")
    exit(1)
```

## Step 3: Fetch Team Officials

To get information about team officials (coaches, managers, etc.):

> **Note**: Just like with players, the `team_id` parameter must be a match-specific team ID (`matchlagid`), not just the general team ID.

```python
try:
    officials = client.fetch_team_officials_json(team_id)

    print(f"Team has {len(officials)} officials")

    # Print official information
    for official in officials:
        official_id = official.get('personid')
        first_name = official.get('fornamn', '')
        last_name = official.get('efternamn', '')
        role = official.get('roll', 'N/A')

        print(f"ID: {official_id}, Name: {first_name} {last_name}, Role: {role}")

except FogisAPIRequestError as e:
    print(f"Failed to fetch team officials: {e}")
    exit(1)
```

## Step 4: Fetch Team Matches

To get a list of matches for a team, you need to fetch all matches and filter them:

```python
try:
    # Fetch all matches
    all_matches = client.fetch_matches_list_json()

    # Filter matches for the specific team
    team_matches = [
        match for match in all_matches
        if match.get('hemmalagid') == team_id or match.get('bortalagid') == team_id
    ]

    print(f"Team has {len(team_matches)} matches")

    # Print match information
    for match in team_matches:
        match_id = match.get('matchid')
        date = match.get('datum', '')
        time = match.get('tid', '')
        home_team = match.get('hemmalag', '')
        away_team = match.get('bortalag', '')
        venue = match.get('arena', '')

        print(f"Match ID: {match_id}, Date: {date} {time}")
        print(f"  {home_team} vs {away_team} at {venue}")

except FogisAPIRequestError as e:
    print(f"Failed to fetch matches: {e}")
    exit(1)
```

## Step 5: Fetch Players for a Specific Match

To get player information for a specific match:

```python
match_id = 123456  # Replace with a match ID from the team's matches

try:
    match_players = client.fetch_match_players_json(match_id)

    # Get home and away team players
    home_players = match_players.get('hemmalag', [])
    away_players = match_players.get('bortalag', [])

    print(f"Home team has {len(home_players)} players for this match")
    print(f"Away team has {len(away_players)} players for this match")

    # Determine which list contains our team's players
    our_team_players = home_players if match_players.get('hemmalagid') == team_id else away_players

    # Print our team's player information for this match
    print("\nOur team's players for this match:")
    for player in our_team_players:
        player_id = player.get('personid')
        first_name = player.get('fornamn', '')
        last_name = player.get('efternamn', '')
        jersey_number = player.get('tshirt', 'N/A')
        position = player.get('position', 'N/A')

        print(f"ID: {player_id}, Name: {first_name} {last_name}, Number: {jersey_number}, Position: {position}")

except FogisAPIRequestError as e:
    print(f"Failed to fetch match players: {e}")
    exit(1)
```

## Step 6: Report Team Official Actions

If you need to report disciplinary actions for team officials during a match:

```python
match_id = 123456  # Replace with the match ID
official_id = 67890  # Replace with the official's ID

# Example: Report a yellow card for a team official
action_data = {
    "matchid": match_id,
    "lagid": team_id,
    "personid": official_id,
    "matchlagledaretypid": 1,  # 1 for yellow card
    "minut": 35  # Minute when the action occurred
}

try:
    response = client.report_team_official_action(action_data)

    if response.get('success', False):
        print(f"Team official action reported successfully. Action ID: {response.get('id')}")
    else:
        print("Failed to report team official action")

except (FogisAPIRequestError, FogisDataError) as e:
    print(f"Error reporting team official action: {e}")
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
team_id = 12345  # Replace with your team ID

try:
    # Step 1: Initialize and authenticate
    client = FogisApiClient(username, password)
    client.login()
    print("Authentication successful")

    # Step 2: Fetch team players
    team_players_response = client.fetch_team_players_json(team_id)
    players = team_players_response.get('spelare', [])
    print(f"\nTeam has {len(players)} players")

    # Print player information
    for i, player in enumerate(players[:5]):  # Show first 5 players
        player_id = player.get('personid')
        name = f"{player.get('fornamn', '')} {player.get('efternamn', '')}"
        jersey = player.get('tshirt', 'N/A')
        position = player.get('position', 'N/A')
        print(f"{i+1}. ID: {player_id}, Name: {name}, Number: {jersey}, Position: {position}")

    if len(players) > 5:
        print(f"... and {len(players) - 5} more players")

    # Step 3: Fetch team officials
    officials = client.fetch_team_officials_json(team_id)
    print(f"\nTeam has {len(officials)} officials")

    # Print official information
    for i, official in enumerate(officials):
        official_id = official.get('personid')
        name = f"{official.get('fornamn', '')} {official.get('efternamn', '')}"
        role = official.get('roll', 'N/A')
        print(f"{i+1}. ID: {official_id}, Name: {name}, Role: {role}")

    # Step 4: Fetch team matches
    all_matches = client.fetch_matches_list_json()
    team_matches = [
        match for match in all_matches
        if match.get('hemmalagid') == team_id or match.get('bortalagid') == team_id
    ]
    print(f"\nTeam has {len(team_matches)} matches")

    # Print match information for the next 3 matches
    upcoming_matches = sorted(team_matches, key=lambda m: m.get('datum', ''))[:3]
    for i, match in enumerate(upcoming_matches):
        match_id = match.get('matchid')
        date = match.get('datum', '')
        time = match.get('tid', '')
        home_team = match.get('hemmalag', '')
        away_team = match.get('bortalag', '')
        venue = match.get('arena', '')
        print(f"{i+1}. Match ID: {match_id}, Date: {date} {time}")
        print(f"   {home_team} vs {away_team} at {venue}")

    # Step 5: Fetch players for the next match
    if upcoming_matches:
        next_match = upcoming_matches[0]
        next_match_id = next_match.get('matchid')
        print(f"\nFetching player information for next match (ID: {next_match_id})")

        match_players = client.fetch_match_players_json(next_match_id)
        home_players = match_players.get('hemmalag', [])
        away_players = match_players.get('bortalag', [])

        # Determine which list contains our team's players
        is_home_team = next_match.get('hemmalagid') == team_id
        our_team_players = home_players if is_home_team else away_players
        opponent_players = away_players if is_home_team else home_players

        print(f"\nOur team has {len(our_team_players)} players registered for this match")
        print(f"Opponent has {len(opponent_players)} players registered for this match")

        # Print our team's starting lineup (first 11 players)
        print("\nOur team's starting lineup:")
        for i, player in enumerate(our_team_players[:11]):
            name = f"{player.get('fornamn', '')} {player.get('efternamn', '')}"
            jersey = player.get('tshirt', 'N/A')
            position = player.get('position', 'N/A')
            print(f"{i+1}. {name} (#{jersey}) - {position}")

    print("\nTeam management operations completed successfully")

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

1. **Cache team information** when appropriate to reduce API calls.
2. **Handle missing data gracefully** as not all fields may be populated for all players/officials.
3. **Use environment variables** for storing credentials instead of hardcoding them.
4. **Implement error handling** to gracefully handle API failures.
5. **Respect rate limits** by not making too many requests in a short period.
6. **Filter data client-side** when possible to reduce the number of API calls.

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Ensure your username and password are correct
   - Check if your account has the necessary permissions

2. **Missing Team Information**
   - Verify that the team ID is correct
   - Ensure the team is properly registered in FOGIS

3. **Empty Player Lists**
   - Check if the team roster has been submitted
   - Verify that players have been properly registered

4. **Unable to Report Official Actions**
   - Ensure the match is in a state that allows reporting
   - Verify that the official is properly registered for the match
   - Check that all required fields are included in the action data

5. **Inconsistent Data**
   - FOGIS data may be updated by other users, so always fetch fresh data before making changes
   - Verify that the data you're working with is up-to-date

If you encounter persistent issues, refer to the [Troubleshooting](../troubleshooting.md) section for more detailed help.
