# Event Tracking Guide

This guide provides step-by-step instructions for tracking and managing match events using the FOGIS API Client.

## Prerequisites

- FOGIS API Client installed
- Valid FOGIS credentials with appropriate permissions
- Match ID for the match you want to track events for

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

Before tracking events, it's important to get the match details:

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
    home_team_name = match['hemmalag']
    away_team_name = match['bortalag']

except FogisAPIRequestError as e:
    print(f"Failed to fetch match details: {e}")
    exit(1)
```

## Step 3: Fetch Existing Events

To track events, first fetch any existing events for the match:

```python
try:
    events = client.fetch_match_events_json(match_id)

    print(f"Match has {len(events)} events")

    # Group events by type
    goals = [event for event in events if event.get('mal', False)]
    yellow_cards = [event for event in events if event.get('matchhandelsetypid') == 20]
    red_cards = [event for event in events if event.get('matchhandelsetypid') in [8, 9]]
    substitutions = [event for event in events if event.get('matchhandelsetypid') == 17]

    print(f"Goals: {len(goals)}")
    print(f"Yellow cards: {len(yellow_cards)}")
    print(f"Red cards: {len(red_cards)}")
    print(f"Substitutions: {len(substitutions)}")

    # Print event details
    print("\nEvent Timeline:")
    sorted_events = sorted(events, key=lambda e: e.get('matchminut', 0))

    for event in sorted_events:
        event_id = event.get('matchhandelseid')
        minute = event.get('matchminut', 0)
        period = event.get('period', 1)
        team_name = event.get('matchlagnamn', '')
        player_name = event.get('spelarenamn', 'Unknown')
        event_type = event.get('matchhandelsetypnamn', 'Unknown')

        # Format the event description
        if event.get('mal', False):
            home_score = event.get('hemmamal', 0)
            away_score = event.get('bortamal', 0)
            print(f"{minute}' - GOAL! {player_name} ({team_name}) - Score: {home_score}-{away_score}")
        elif event.get('matchhandelsetypid') == 20:
            print(f"{minute}' - YELLOW CARD: {player_name} ({team_name})")
        elif event.get('matchhandelsetypid') in [8, 9]:
            print(f"{minute}' - RED CARD: {player_name} ({team_name})")
        elif event.get('matchhandelsetypid') == 17:
            player_in = player_name
            player_out = event.get('assisterande', 'Unknown')
            print(f"{minute}' - SUBSTITUTION: {player_in} IN, {player_out} OUT ({team_name})")
        else:
            print(f"{minute}' - {event_type}: {player_name} ({team_name})")

except FogisAPIRequestError as e:
    print(f"Failed to fetch match events: {e}")
    exit(1)
```

## Step 4: Report a New Event

To add a new event to the match:

```python
from fogis_api_client import EVENT_TYPES

# First, fetch players to get their IDs
try:
    players = client.fetch_match_players_json(match_id)
    home_players = players.get('hemmalag', [])
    away_players = players.get('bortalag', [])

    # Example: Report a goal by a home team player
    scorer_id = home_players[0]['spelareid']  # ID of the player who scored

    # Print available event types for reference
    print("\nAvailable Event Types:")
    for code, details in EVENT_TYPES.items():
        print(f"Code: {code}, Name: {details['name']}, Goal: {details['goal']}")

    # Create the event data
    goal_event = {
        "matchid": match_id,
        "matchhandelsetypid": 6,  # Regular goal (see EVENT_TYPES for other goal types)
        "matchminut": 80,  # Minute when the goal was scored
        "matchlagid": home_team_id,
        "spelareid": scorer_id,
        "period": 2,  # 1 for first half, 2 for second half
        "hemmamal": 2,  # Updated score for home team
        "bortamal": 1   # Updated score for away team
    }

    # Report the event
    response = client.report_match_event(goal_event)

    if response.get('success', False):
        new_event_id = response.get('matchhandelseid')
        print(f"Goal reported successfully. Event ID: {new_event_id}")
    else:
        print("Failed to report goal")

except (FogisAPIRequestError, FogisDataError) as e:
    print(f"Error reporting event: {e}")
```

## Step 5: Delete an Event

If you need to delete an event (for example, if it was reported incorrectly):

```python
# Use the event ID from a previously reported event
event_id = 789012  # Replace with the actual event ID

try:
    success = client.delete_match_event(event_id)

    if success:
        print(f"Event {event_id} deleted successfully")
    else:
        print(f"Failed to delete event {event_id}")

except (FogisAPIRequestError, FogisDataError) as e:
    print(f"Error deleting event: {e}")
```

## Step 6: Clear All Events

In some cases, you might need to clear all events for a match and start over:

```python
try:
    response = client.clear_match_events(match_id)

    if response.get('success', False):
        print(f"All events for match {match_id} cleared successfully")
    else:
        print(f"Failed to clear events for match {match_id}")

except (FogisAPIRequestError, FogisDataError) as e:
    print(f"Error clearing events: {e}")
```

## Step 7: Fetch Updated Events

After adding or deleting events, fetch the updated list to verify the changes:

```python
try:
    updated_events = client.fetch_match_events_json(match_id)

    print(f"Match now has {len(updated_events)} events")

    # Print updated event timeline
    print("\nUpdated Event Timeline:")
    sorted_events = sorted(updated_events, key=lambda e: e.get('matchminut', 0))

    for event in sorted_events:
        minute = event.get('matchminut', 0)
        team_name = event.get('matchlagnamn', '')
        player_name = event.get('spelarenamn', 'Unknown')
        event_type = event.get('matchhandelsetypnamn', 'Unknown')

        # Format the event description
        if event.get('mal', False):
            home_score = event.get('hemmamal', 0)
            away_score = event.get('bortamal', 0)
            print(f"{minute}' - GOAL! {player_name} ({team_name}) - Score: {home_score}-{away_score}")
        elif event.get('matchhandelsetypid') == 20:
            print(f"{minute}' - YELLOW CARD: {player_name} ({team_name})")
        elif event.get('matchhandelsetypid') in [8, 9]:
            print(f"{minute}' - RED CARD: {player_name} ({team_name})")
        elif event.get('matchhandelsetypid') == 17:
            player_in = player_name
            player_out = event.get('assisterande', 'Unknown')
            print(f"{minute}' - SUBSTITUTION: {player_in} IN, {player_out} OUT ({team_name})")
        else:
            print(f"{minute}' - {event_type}: {player_name} ({team_name})")

except FogisAPIRequestError as e:
    print(f"Failed to fetch updated match events: {e}")
```

## Complete Example

Here's a complete example that puts all the steps together:

```python
import logging
from fogis_api_client import FogisApiClient, FogisLoginError, FogisAPIRequestError, FogisDataError, EVENT_TYPES

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
    print(f"\nMatch: {match['hemmalag']} vs {match['bortalag']}")
    print(f"Date: {match['datum']}")
    print(f"Venue: {match['arena']}")

    home_team_id = match['hemmalagid']
    away_team_id = match['bortalagid']
    home_team_name = match['hemmalag']
    away_team_name = match['bortalag']

    # Step 3: Fetch existing events
    events = client.fetch_match_events_json(match_id)
    print(f"\nMatch has {len(events)} events")

    # Group events by type
    goals = [event for event in events if event.get('mal', False)]
    yellow_cards = [event for event in events if event.get('handelsekod') == 20]
    red_cards = [event for event in events if event.get('handelsekod') in [8, 9]]
    substitutions = [event for event in events if event.get('handelsekod') == 17]

    print(f"Goals: {len(goals)}")
    print(f"Yellow cards: {len(yellow_cards)}")
    print(f"Red cards: {len(red_cards)}")
    print(f"Substitutions: {len(substitutions)}")

    # Print event timeline
    if events:
        print("\nEvent Timeline:")
        sorted_events = sorted(events, key=lambda e: e.get('minut', 0))

        for event in sorted_events:
            minute = event.get('minut', 0)
            team_name = event.get('lag', '')
            player_name = event.get('spelare', 'Unknown')

            # Format the event description
            if event.get('mal', False):
                home_score = event.get('resultatHemma', 0)
                away_score = event.get('resultatBorta', 0)
                print(f"{minute}' - GOAL! {player_name} ({team_name}) - Score: {home_score}-{away_score}")
            elif event.get('handelsekod') == 20:
                print(f"{minute}' - YELLOW CARD: {player_name} ({team_name})")
            elif event.get('handelsekod') in [8, 9]:
                print(f"{minute}' - RED CARD: {player_name} ({team_name})")
            elif event.get('handelsekod') == 17:
                player_in = player_name
                player_out = event.get('assisterande', 'Unknown')
                print(f"{minute}' - SUBSTITUTION: {player_in} IN, {player_out} OUT ({team_name})")
            else:
                event_type = event.get('handelsetyp', 'Unknown')
                print(f"{minute}' - {event_type}: {player_name} ({team_name})")

    # Step 4: Fetch players for reporting new events
    players = client.fetch_match_players_json(match_id)
    home_players = players.get('hemmalag', [])
    away_players = players.get('bortalag', [])

    print("\nHome Team Players:")
    for i, player in enumerate(home_players[:5]):  # Show first 5 players
        player_id = player.get('personid')
        name = f"{player.get('fornamn', '')} {player.get('efternamn', '')}"
        print(f"{i+1}. ID: {player_id}, Name: {name}")

    print("\nAway Team Players:")
    for i, player in enumerate(away_players[:5]):  # Show first 5 players
        player_id = player.get('personid')
        name = f"{player.get('fornamn', '')} {player.get('efternamn', '')}"
        print(f"{i+1}. ID: {player_id}, Name: {name}")

    # Step 5: Report a new event (example)
    print("\nReporting a new goal...")

    # Use the first home player as the scorer
    scorer_id = home_players[0]['personid']
    scorer_name = f"{home_players[0].get('fornamn', '')} {home_players[0].get('efternamn', '')}"

    # Calculate new score based on existing goals
    home_goals = sum(1 for g in goals if g.get('lagid') == home_team_id)
    away_goals = sum(1 for g in goals if g.get('lagid') == away_team_id)
    new_home_goals = home_goals + 1

    goal_event = {
        "matchid": match_id,
        "handelsekod": 6,  # Regular goal
        "minut": 85,  # Minute when the goal was scored
        "lagid": home_team_id,
        "personid": scorer_id,
        "period": 2,  # Second half
        "resultatHemma": new_home_goals,
        "resultatBorta": away_goals
    }

    response = client.report_match_event(goal_event)

    if response.get('success', False):
        new_event_id = response.get('matchhandelseid')
        print(f"Goal by {scorer_name} reported successfully. Event ID: {new_event_id}")
    else:
        print("Failed to report goal")

    # Step 6: Fetch updated events
    print("\nFetching updated events...")
    updated_events = client.fetch_match_events_json(match_id)

    print(f"Match now has {len(updated_events)} events")

    # Print updated event timeline
    print("\nUpdated Event Timeline:")
    sorted_events = sorted(updated_events, key=lambda e: e.get('minut', 0))

    for event in sorted_events:
        minute = event.get('minut', 0)
        team_name = event.get('lag', '')
        player_name = event.get('spelare', 'Unknown')

        # Format the event description
        if event.get('mal', False):
            home_score = event.get('resultatHemma', 0)
            away_score = event.get('resultatBorta', 0)
            print(f"{minute}' - GOAL! {player_name} ({team_name}) - Score: {home_score}-{away_score}")
        elif event.get('handelsekod') == 20:
            print(f"{minute}' - YELLOW CARD: {player_name} ({team_name})")
        elif event.get('handelsekod') in [8, 9]:
            print(f"{minute}' - RED CARD: {player_name} ({team_name})")
        elif event.get('handelsekod') == 17:
            player_in = player_name
            player_out = event.get('assisterande', 'Unknown')
            print(f"{minute}' - SUBSTITUTION: {player_in} IN, {player_out} OUT ({team_name})")
        else:
            event_type = event.get('handelsetyp', 'Unknown')
            print(f"{minute}' - {event_type}: {player_name} ({team_name})")

    print("\nEvent tracking operations completed successfully")

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

1. **Always fetch the latest events** before adding new ones to ensure you have the most up-to-date information.
2. **Maintain consistent scoring** when reporting goals by ensuring the score is updated correctly.
3. **Report events in chronological order** to maintain a logical timeline.
4. **Double-check player IDs** before reporting events to ensure they're associated with the correct players.
5. **Use the EVENT_TYPES dictionary** to reference the correct event codes.
6. **Handle errors gracefully** to prevent incomplete or inconsistent event reporting.
7. **Consider implementing an undo feature** in your application by storing event IDs for easy deletion if needed.

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Ensure your username and password are correct
   - Check if your account has the necessary permissions

2. **Missing Match Information**
   - Verify that the match ID is correct
   - Ensure the match is properly registered in FOGIS

3. **Event Reporting Failures**
   - Check that all required fields are included in the event data
   - Ensure player IDs are correct
   - Verify that the event type code is valid
   - Make sure the score is updated correctly for goal events

4. **Event Deletion Failures**
   - Verify that the event ID is correct
   - Check if you have permission to delete the event
   - Some events may not be deletable after a certain time

5. **Inconsistent Event Timeline**
   - Events may not appear in chronological order in the API response
   - Always sort events by minute when displaying them

If you encounter persistent issues, refer to the [Troubleshooting](../troubleshooting.md) section for more detailed help.
