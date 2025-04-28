# API Reference

This document provides detailed information about the FOGIS API Client classes, methods, and data types.

## Table of Contents

- [FogisApiClient Class](#fogisapiclient-class)
- [Exception Classes](#exception-classes)
- [Data Types](#data-types)
- [Event Types](#event-types)
- [API Contracts](#api-contracts)
- [Logging Utilities](#logging-utilities)

## FogisApiClient Class

The main class for interacting with the FOGIS API.

### Constructor

```python
FogisApiClient(username=None, password=None, cookies=None)
```

**Parameters:**
- `username` (Optional[str]): FOGIS username. Required if cookies are not provided.
- `password` (Optional[str]): FOGIS password. Required if cookies are not provided.
- `cookies` (Optional[Dict[str, str]]): Session cookies for authentication. If provided, username and password are not required.

**Raises:**
- `ValueError`: If neither valid credentials nor cookies are provided

**Example:**
```python
# Initialize with username and password
client = FogisApiClient(username="your_username", password="your_password")

# Initialize with cookies
client = FogisApiClient(cookies={"FogisMobilDomarKlient_ASPXAUTH": "cookie_value",
                                "ASP_NET_SessionId": "session_id"})
```

### Authentication Methods

#### login

```python
login() -> Dict[str, str]
```

Logs into the FOGIS API and stores the session cookies.

**Returns:**
- `Dict[str, str]`: The session cookies if login is successful

**Raises:**
- `FogisLoginError`: If login fails or if neither credentials nor cookies are available
- `FogisAPIRequestError`: If there's an error during the login request

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
cookies = client.login()
print("Login successful" if cookies else "Login failed")
```

#### validate_cookies

```python
validate_cookies() -> bool
```

Validates if the current cookies are still valid for authentication.

**Returns:**
- `bool`: True if cookies are valid, False otherwise

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
client.login()
# Later, check if the session is still valid
if client.validate_cookies():
    print("Session is still valid")
else:
    print("Session has expired, need to login again")
```

#### get_cookies

```python
get_cookies() -> Optional[Dict[str, str]]
```

Returns the current session cookies.

**Returns:**
- `Optional[Dict[str, str]]`: The current session cookies, or None if not authenticated

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
client.login()
cookies = client.get_cookies()  # Save these cookies for later use
print("Cookies retrieved" if cookies else "No cookies available")

# Later, in another session:
new_client = FogisApiClient(cookies=cookies)  # Authenticate with saved cookies
print("Using saved cookies for authentication")
```

### Match Methods

#### fetch_matches_list_json

```python
fetch_matches_list_json(filter=None) -> List[Dict[str, Any]]
```

Fetches the list of matches for the logged-in referee.

**Parameters:**
- `filter` (Optional[Dict[str, Any]]): An optional dictionary containing server-side date range filter criteria.
  Common filter parameters include:
  - `datumFran`: Start date in format 'YYYY-MM-DD'
  - `datumTill`: End date in format 'YYYY-MM-DD'
  - `datumTyp`: Date type filter (e.g., 'match', 'all')
  - `sparadDatum`: Saved date filter

**Returns:**
- `List[Dict[str, Any]]`: A list of match dictionaries

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
# Get matches with default date range
matches = client.fetch_matches_list_json()

# Get matches with custom date range
from datetime import datetime, timedelta
today = datetime.now().strftime('%Y-%m-%d')
next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
matches = client.fetch_matches_list_json({
    'datumFran': today,
    'datumTill': next_week,
    'datumTyp': 'match'
})
```

#### fetch_match_json

```python
fetch_match_json(match_id: Union[str, int]) -> Dict[str, Any]
```

Fetches detailed information for a specific match.

**Parameters:**
- `match_id` (Union[str, int]): The ID of the match to fetch

**Returns:**
- `Dict[str, Any]`: Match details including teams, score, venue, etc.

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
match = client.fetch_match_json(123456)
print(f"Match: {match['hemmalag']} vs {match['bortalag']}")
```

#### fetch_match_result_json

```python
fetch_match_result_json(match_id: Union[str, int]) -> Union[Dict[str, Any], List[Dict[str, Any]]]
```

Fetches the match results in JSON format for a given match ID.

**Parameters:**
- `match_id` (Union[str, int]): The ID of the match

**Returns:**
- `Union[Dict[str, Any], List[Dict[str, Any]]]`: Result information for the match, including full-time and half-time scores

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
result = client.fetch_match_result_json(123456)
if isinstance(result, dict):
    print(f"Score: {result.get('hemmamal', 0)}-{result.get('bortamal', 0)}")
else:
    print(f"Multiple results found: {len(result)}")
```

#### report_match_result

```python
report_match_result(result_data: Union[MatchResultDict, Dict[str, Any]]) -> Dict[str, Any]
```

Reports match results (halftime and fulltime) to the FOGIS API.

> **⚠️ WARNING: Critical API Contract**
> This method maintains a critical API contract with the FOGIS server. The server requires a specific nested structure, but the client library provides a simplified flat structure for ease of use. The library automatically handles the conversion between these formats.

**Parameters:**
- `result_data` (Union[MatchResultDict, Dict[str, Any]]): Data containing match results. Can be either:

  **Format 1 (flat structure - PREFERRED):**
  - `matchid`: The ID of the match
  - `hemmamal`: Full-time score for the home team
  - `bortamal`: Full-time score for the away team
  - `halvtidHemmamal`: Half-time score for the home team (optional)
  - `halvtidBortamal`: Half-time score for the away team (optional)

  **Format 2 (nested structure - for backward compatibility):**
  - `matchresultatListaJSON`: Array of match result objects with:
    - `matchid`: The ID of the match
    - `matchresultattypid`: 1 for full-time, 2 for half-time
    - `matchlag1mal`: Score for team 1
    - `matchlag2mal`: Score for team 2
    - `wo`, `ow`, `ww`: Boolean flags

**Returns:**
- `Dict[str, Any]`: Response from the API, typically containing success status

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid or not a dictionary
- `ValueError`: If required fields are missing

**Example (Flat Structure - Recommended):**
```python
client = FogisApiClient(username="your_username", password="your_password")
result = {
    "matchid": 123456,
    "hemmamal": 2,
    "bortamal": 1,
    "halvtidHemmamal": 1,
    "halvtidBortamal": 0
}
response = client.report_match_result(result)
print(f"Result reported successfully: {response.get('success', False)}")
```

**Example (Nested Structure - Legacy):**
```python
client = FogisApiClient(username="your_username", password="your_password")
result = {
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
response = client.report_match_result(result)
print(f"Result reported successfully: {response.get('success', False)}")
```

**Field Mapping:**

| Client Format (Flat) | Server Format (Nested) |
|---------------------|------------------------|
| `matchid`           | `matchid` in both objects |
| `hemmamal`          | `matchlag1mal` in object with `matchresultattypid=1` |
| `bortamal`          | `matchlag2mal` in object with `matchresultattypid=1` |
| `halvtidHemmamal`   | `matchlag1mal` in object with `matchresultattypid=2` |
| `halvtidBortamal`   | `matchlag2mal` in object with `matchresultattypid=2` |

#### mark_reporting_finished

```python
mark_reporting_finished(match_id: Union[str, int]) -> Dict[str, bool]
```

Mark a match report as completed/finished in the FOGIS system.

**Parameters:**
- `match_id` (Union[str, int]): The ID of the match to mark as finished

**Returns:**
- `Dict[str, bool]`: The response from the FOGIS API, typically containing a success status

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid or not a dictionary
- `ValueError`: If match_id is empty or invalid

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
client.login()
result = client.mark_reporting_finished(match_id=123456)
print(f"Report marked as finished: {result.get('success', False)}")
```

### Player and Team Methods

#### fetch_match_players_json

```python
fetch_match_players_json(match_id: Union[str, int]) -> Dict[str, List[Dict[str, Any]]]
```

Fetches player information for a specific match.

**Parameters:**
- `match_id` (Union[str, int]): The ID of the match

**Returns:**
- `Dict[str, List[Dict[str, Any]]]`: Player information for the match, typically containing keys for home and away team players

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid or not a dictionary

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
players = client.fetch_match_players_json(123456)
home_players = players.get('hemmalag', [])
away_players = players.get('bortalag', [])
print(f"Home team has {len(home_players)} players, Away team has {len(away_players)} players")
```

#### fetch_team_players_json

```python
fetch_team_players_json(team_id: Union[str, int]) -> Dict[str, Any]
```

Fetches player information for a specific team.

**Parameters:**
- `team_id` (Union[str, int]): The ID of the team

**Returns:**
- `Dict[str, Any]`: Dictionary containing player information for the team with a 'spelare' key that contains a list of players

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
team_players = client.fetch_team_players_json(12345)
players = team_players.get('spelare', [])
print(f"Team has {len(players)} players")
if players:
    print(f"First player: {players[0]['fornamn']} {players[0]['efternamn']}")
```

#### save_match_participant

```python
save_match_participant(participant_data: Dict[str, Any]) -> Dict[str, Any]
```

Updates specific fields for a match participant in FOGIS while preserving other fields. This method is used to modify only the fields you specify (like jersey number, captain status, etc.) while keeping all other player information unchanged.

**Parameters:**
- `participant_data` (Dict[str, Any]): Data containing match participant details. Must include:
  - `matchdeltagareid`: The ID of the match participant (this is a match-specific ID, NOT the permanent `spelareid`)
  - `trojnummer`: Jersey number
  - `lagdelid`: Team part ID (typically 0)
  - `lagkapten`: Boolean indicating if the player is team captain
  - `ersattare`: Boolean indicating if the player is a substitute
  - `positionsnummerhv`: Position number (typically 0)
  - `arSpelandeLedare`: Boolean indicating if the player is a playing leader
  - `ansvarig`: Boolean indicating if the player is responsible

  **Note:** It's important to use `matchdeltagareid` (match-specific player ID) and not `spelareid` (permanent player ID) when updating player information for a specific match.

**Returns:**
- `Dict[str, Any]`: Response from the API containing:
  - `success`: Boolean indicating if the update was successful
  - `roster`: The updated team roster
  - `updated_player`: The updated player information
  - `verified`: Boolean indicating if the changes were verified in the returned roster

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid or not a dictionary
- `ValueError`: If required fields are missing

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")

# First, get the current player information
match_players = client.fetch_match_players_json(123456)
home_players = match_players.get('hemmalag', [])

# Find the player we want to update
player_to_update = None
for player in home_players:
    if player['fornamn'] == 'John' and player['efternamn'] == 'Doe':
        player_to_update = player
        break

if player_to_update:
    # Create an update object with only the fields we want to change
    # We must include matchdeltagareid to identify the player
    participant_update = {
        "matchdeltagareid": player_to_update['matchdeltagareid'],  # Required to identify the player
        "trojnummer": 10,                                       # Change jersey number to 10
        "lagkapten": True,                                      # Make this player the captain

        # These fields are required by the API but will keep their current values
        "lagdelid": 0,
        "ersattare": player_to_update.get('ersattare', False),
        "positionsnummerhv": 0,
        "arSpelandeLedare": False,
        "ansvarig": False
    }

    # Send only the fields we want to update
    response = client.save_match_participant(participant_update)

    if response["success"] and response["verified"]:
        print(f"Player updated successfully with jersey #{response['updated_player']['trojnummer']}")
        # You can access the full team roster if needed
        roster = response["roster"]
        print(f"Team has {len(roster.get('spelare', []))} players")
    else:
        print("Update failed or changes not verified")
else:
    print("Player not found")
```

### Event Methods

#### fetch_match_events_json

```python
fetch_match_events_json(match_id: Union[str, int]) -> List[Dict[str, Any]]
```

Fetches events information for a specific match.

**Parameters:**
- `match_id` (Union[str, int]): The ID of the match

**Returns:**
- `List[Dict[str, Any]]`: List of events information for the match, including goals, cards, substitutions, and other match events

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid or not a list

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
events = client.fetch_match_events_json(123456)
goals = [event for event in events if event.get('mal', False)]
print(f"Total events: {len(events)}, Goals: {len(goals)}")
```

#### report_match_event

```python
report_match_event(event_data: EventDict) -> Dict[str, Any]
```

Reports a match event to FOGIS.

> **⚠️ WARNING: Critical API Contract**
> This method maintains a critical API contract with the FOGIS server. Different event types require different fields, and all fields must be correctly formatted for the API to accept the request.

**Parameters:**
- `event_data` (EventDict): Data for the event to report. Must include at minimum:
  - `matchid`: The ID of the match (integer)
  - `handelsekod`: The event type code (see EVENT_TYPES)
  - `minut`: The minute when the event occurred
  - `lagid`: The ID of the team associated with the event
  - `period`: The period number (1 for first half, 2 for second half)

  **For Goals (handelsekod 6, 39, 28, 29, 15, 14):**
  - All base fields above
  - `personid`: The ID of the player who scored
  - `resultatHemma`: Updated score for the home team
  - `resultatBorta`: Updated score for the away team
  - `assisterandeid`: The ID of the assisting player (optional)

  **For Cards (handelsekod 20, 8, 9):**
  - All base fields above
  - `personid`: The ID of the player who received the card

  **For Substitutions (handelsekod 17):**
  - All base fields above
  - `personid`: The ID of the player coming on
  - `assisterandeid`: The ID of the player going off

**Returns:**
- `Dict[str, Any]`: Response from the API, typically containing success status and the ID of the created event

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid or not a dictionary

**Example (Goal):**
```python
client = FogisApiClient(username="your_username", password="your_password")
# Report a goal
event = {
    "matchid": 123456,
    "handelsekod": 6,  # Regular goal
    "minut": 35,
    "lagid": 78910,  # Team ID
    "personid": 12345,  # Player ID
    "period": 1,
    "resultatHemma": 1,
    "resultatBorta": 0
}
response = client.report_match_event(event)
print(f"Event reported successfully: {response.get('success', False)}")
```

**Example (Yellow Card):**
```python
client = FogisApiClient(username="your_username", password="your_password")
# Report a yellow card
event = {
    "matchid": 123456,
    "handelsekod": 20,  # Yellow card
    "minut": 42,
    "lagid": 78910,  # Team ID
    "personid": 12345,  # Player ID
    "period": 1
}
response = client.report_match_event(event)
print(f"Event reported successfully: {response.get('success', False)}")
```

**Example (Substitution):**
```python
client = FogisApiClient(username="your_username", password="your_password")
# Report a substitution
event = {
    "matchid": 123456,
    "handelsekod": 17,  # Substitution
    "minut": 65,
    "lagid": 78910,  # Team ID
    "personid": 12345,  # Player coming on
    "assisterandeid": 67890,  # Player going off
    "period": 2
}
response = client.report_match_event(event)
print(f"Event reported successfully: {response.get('success', False)}")
```

#### delete_match_event

```python
delete_match_event(event_id: Union[str, int]) -> bool
```

Deletes a specific event from a match.

**Parameters:**
- `event_id` (Union[str, int]): The ID of the event to delete

**Returns:**
- `bool`: True if deletion was successful, False otherwise

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
# Get all events for a match
events = client.fetch_match_events_json(123456)
if events:
    # Delete the first event
    event_id = events[0]['matchhandelseid']
    success = client.delete_match_event(event_id)
    print(f"Event deletion {'successful' if success else 'failed'}")
```

#### clear_match_events

```python
clear_match_events(match_id: Union[str, int]) -> Dict[str, bool]
```

Clear all events for a match.

**Parameters:**
- `match_id` (Union[str, int]): The ID of the match

**Returns:**
- `Dict[str, bool]`: Response from the API, typically containing a success status

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid or not a dictionary

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
response = client.clear_match_events(123456)
print(f"Events cleared successfully: {response.get('success', False)}")
```

### Official Methods

#### fetch_match_officials_json

```python
fetch_match_officials_json(match_id: Union[str, int]) -> Dict[str, List[Dict[str, Any]]]
```

Fetches officials information for a specific match.

**Parameters:**
- `match_id` (Union[str, int]): The ID of the match

**Returns:**
- `Dict[str, List[Dict[str, Any]]]`: Officials information for the match, typically containing keys for referees and other match officials

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid or not a dictionary

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
officials = client.fetch_match_officials_json(123456)
referees = officials.get('domare', [])
if referees:
    print(f"Main referee: {referees[0]['fornamn']} {referees[0]['efternamn']}")
else:
    print("No referee assigned yet")
```

#### fetch_team_officials_json

```python
fetch_team_officials_json(team_id: Union[str, int]) -> List[Dict[str, Any]]
```

Fetches officials information for a specific team.

**Parameters:**
- `team_id` (Union[str, int]): The ID of the team

**Returns:**
- `List[Dict[str, Any]]`: List of officials information for the team, including coaches, managers, and other team staff

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid or not a list

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
officials = client.fetch_team_officials_json(12345)
print(f"Team has {len(officials)} officials")
if officials:
    coaches = [o for o in officials if o.get('roll', '').lower() == 'tränare']
    print(f"Number of coaches: {len(coaches)}")
```

#### report_team_official_action

```python
report_team_official_action(action_data: Dict[str, Any]) -> Dict[str, Any]
```

Reports team official disciplinary action to the FOGIS API.

**Parameters:**
- `action_data` (Dict[str, Any]): Data containing team official action details. Must include:
  - `matchid`: The ID of the match
  - `lagid`: The ID of the team
  - `personid`: The ID of the team official
  - `matchlagledaretypid`: The type ID of the disciplinary action

  Optional fields:
  - `minut`: The minute when the action occurred

**Returns:**
- `Dict[str, Any]`: Response from the API, typically containing success status and the ID of the created action

**Raises:**
- `FogisLoginError`: If not logged in
- `FogisAPIRequestError`: If there's an error with the API request
- `FogisDataError`: If the response data is invalid or not a dictionary
- `ValueError`: If required fields are missing

**Example:**
```python
client = FogisApiClient(username="your_username", password="your_password")
# Report a yellow card for a team official
action = {
    "matchid": 123456,
    "lagid": 78910,  # Team ID
    "personid": 12345,  # Official ID
    "matchlagledaretypid": 1,  # Yellow card
    "minut": 35
}
response = client.report_team_official_action(action)
print(f"Action reported successfully: {response.get('success', False)}")
```

## Exception Classes

### FogisLoginError

Exception raised when login to FOGIS fails.

This exception is raised in the following cases:
- Invalid credentials
- Missing credentials when no cookies are provided
- Session expired
- Unable to find login form elements

**Attributes:**
- `message` (str): Explanation of the error

### FogisAPIRequestError

Exception raised when an API request to FOGIS fails.

This exception is raised in the following cases:
- Network connectivity issues
- Server errors
- Invalid request parameters
- Timeout errors

**Attributes:**
- `message` (str): Explanation of the error

### FogisDataError

Exception raised when there's an issue with the data from FOGIS.

This exception is raised in the following cases:
- Invalid response format
- Missing expected data fields
- JSON parsing errors
- Unexpected data types

**Attributes:**
- `message` (str): Explanation of the error

## Data Types

The FOGIS API Client uses several TypedDict classes to define the structure of data:

### MatchDict

Type definition for a match object returned by the API.

**Fields:**
- `matchid` (int): The ID of the match
- `matchnr` (str): The match number
- `datum` (str): The date of the match
- `tid` (str): The time of the match
- `hemmalag` (str): The name of the home team
- `bortalag` (str): The name of the away team
- `hemmalagid` (int): The ID of the home team
- `bortalagid` (int): The ID of the away team
- `arena` (str): The venue of the match
- `status` (str): The status of the match
- `domare` (str): The referee of the match
- `ad1` (str): The first assistant referee
- `ad2` (str): The second assistant referee
- `fjarde` (str): The fourth official
- `matchtyp` (str): The type of match
- `tavling` (str): The competition
- `grupp` (str): The group
- `hemmamal` (Optional[int]): The number of goals scored by the home team
- `bortamal` (Optional[int]): The number of goals scored by the away team
- `publik` (Optional[int]): The number of spectators
- `notering` (Optional[str]): Notes about the match
- `rapportstatus` (str): The status of the match report
- `matchstart` (Optional[str]): The start time of the match
- `halvtidHemmamal` (Optional[int]): The number of goals scored by the home team in the first half
- `halvtidBortamal` (Optional[int]): The number of goals scored by the away team in the first half

### PlayerDict

Type definition for a player object returned by the API.

**Fields:**
- `personid` (int): The ID of the player
- `fornamn` (str): The first name of the player
- `efternamn` (str): The last name of the player
- `smeknamn` (Optional[str]): The nickname of the player
- `tshirt` (Optional[str]): The jersey number of the player
- `position` (Optional[str]): The position of the player
- `positionid` (Optional[int]): The ID of the position
- `lagkapten` (Optional[bool]): Whether the player is the team captain
- `spelareid` (Optional[int]): The ID of the player in the match
- `licensnr` (Optional[str]): The license number of the player

### OfficialDict

Type definition for an official object returned by the API.

**Fields:**
- `personid` (int): The ID of the official
- `fornamn` (str): The first name of the official
- `efternamn` (str): The last name of the official
- `roll` (str): The role of the official
- `rollid` (int): The ID of the role

### EventDict

Type definition for an event object returned by the API.

**Fields:**
- `matchhandelseid` (int): The ID of the event
- `matchid` (int): The ID of the match
- `handelsekod` (int): The code of the event
- `handelsetyp` (str): The type of the event
- `minut` (int): The minute when the event occurred
- `lagid` (int): The ID of the team
- `lag` (str): The name of the team
- `personid` (Optional[int]): The ID of the player
- `spelare` (Optional[str]): The name of the player
- `assisterande` (Optional[str]): The name of the assisting player
- `assisterandeid` (Optional[int]): The ID of the assisting player
- `period` (Optional[int]): The period when the event occurred
- `mal` (Optional[bool]): Whether the event is a goal
- `resultatHemma` (Optional[int]): The number of goals scored by the home team after the event
- `resultatBorta` (Optional[int]): The number of goals scored by the away team after the event
- `strafflage` (Optional[str]): The position of the penalty
- `straffriktning` (Optional[str]): The direction of the penalty
- `straffresultat` (Optional[str]): The result of the penalty

## Event Types

The FOGIS API Client defines several event types for match events:

### Goals

- `6`: Regular Goal
- `39`: Header Goal
- `28`: Corner Goal
- `29`: Free Kick Goal
- `15`: Own Goal
- `14`: Penalty Goal

### Penalties

- `18`: Penalty Missing Goal
- `19`: Penalty Save
- `26`: Penalty Hitting the Frame

### Cards

- `20`: Yellow Card
- `8`: Red Card (Denying Goal Opportunity)
- `9`: Red Card (Other Reasons)

### Other Events

- `17`: Substitution

### Control Events

- `31`: Period Start
- `32`: Period End
- `23`: Match Slut (Match End)

## API Contracts

The FOGIS API Client maintains several critical API contracts that define the expected structure of data sent to and received from the FOGIS API. These contracts are essential for ensuring proper functionality.

### What Are API Contracts?

API contracts define the expected structure, data types, and behavior of API requests and responses. They serve as an agreement between the client and the server about how they will communicate.

### Critical API Contracts

#### Match Result Reporting

The FOGIS API requires a specific nested structure for match result reporting, but the client library provides a simplified flat structure for ease of use. The library automatically handles the conversion between these formats.

**Client-Facing API (Flat Structure):**
```json
{
  "matchid": 123456,
  "hemmamal": 2,
  "bortamal": 1,
  "halvtidHemmamal": 1,
  "halvtidBortamal": 0
}
```

**Server API (Nested Structure):**
```json
{
  "matchresultatListaJSON": [
    {
      "matchid": 123456,
      "matchresultattypid": 1,
      "matchlag1mal": 2,
      "matchlag2mal": 1,
      "wo": false,
      "ow": false,
      "ww": false
    },
    {
      "matchid": 123456,
      "matchresultattypid": 2,
      "matchlag1mal": 1,
      "matchlag2mal": 0,
      "wo": false,
      "ow": false,
      "ww": false
    }
  ]
}
```

#### Event Reporting

Different event types require different fields, and all fields must be correctly formatted for the API to accept the request.

**For Goals:**
```json
{
  "matchid": 123456,
  "handelsekod": 6,
  "minut": 35,
  "lagid": 78910,
  "personid": 12345,
  "period": 1,
  "resultatHemma": 1,
  "resultatBorta": 0
}
```

**For Cards:**
```json
{
  "matchid": 123456,
  "handelsekod": 20,
  "minut": 35,
  "lagid": 78910,
  "personid": 12345,
  "period": 1
}
```

**For Substitutions:**
```json
{
  "matchid": 123456,
  "handelsekod": 17,
  "minut": 65,
  "lagid": 78910,
  "personid": 12345,
  "assisterandeid": 67890,
  "period": 2
}
```

### API Contract Validation

The FOGIS API Client includes validation functions to help ensure your data is correctly formatted:

```python
from fogis_api_client.api_contracts import validate_request, validate_response

# Validate a request payload
try:
    validate_request('/MatchWebMetoder.aspx/SparaMatchresultatLista', payload)
    # Payload is valid
except ValidationError as e:
    # Handle validation error
    print(f"Invalid payload: {e}")
```

### Further Reading

For more detailed information about API contracts, see:
- [API Contracts Documentation](api_contracts.md)
- [API Contracts Guide](user_guides/api_contracts.md)

## Logging Utilities

The FOGIS API Client provides several utilities for configuring and using logging.

### configure_logging

```python
configure_logging(level=logging.INFO, format_string=None, log_file=None, log_to_console=True, log_to_file=False)
```

**Parameters:**
- `level` (Union[int, str]): The logging level (e.g., logging.DEBUG, logging.INFO, etc.)
- `format_string` (Optional[str]): Custom format string for log messages
- `log_file` (Optional[str]): Path to the log file (if log_to_file is True)
- `log_to_console` (bool): Whether to log to the console
- `log_to_file` (bool): Whether to log to a file

**Example:**
```python
from fogis_api_client import configure_logging

# Basic configuration with INFO level
configure_logging(level="INFO")

# Log to both console and file with DEBUG level
configure_logging(
    level="DEBUG",
    log_to_console=True,
    log_to_file=True,
    log_file="fogis_api.log"
)
```

### get_logger

```python
get_logger(name)
```

**Parameters:**
- `name` (str): The name of the logger

**Returns:**
- `logging.Logger`: A logger instance

**Example:**
```python
from fogis_api_client import get_logger

logger = get_logger("my_module")
logger.info("This is an info message")
logger.debug("This is a debug message")
```

### set_log_level

```python
set_log_level(level)
```

**Parameters:**
- `level` (Union[int, str]): The logging level (e.g., logging.DEBUG, logging.INFO, etc.)

**Example:**
```python
from fogis_api_client import set_log_level
import logging

# Set log level to DEBUG
set_log_level(logging.DEBUG)

# Or using a string
set_log_level("DEBUG")
```

### get_log_levels

```python
get_log_levels()
```

**Returns:**
- `Dict[str, int]`: A dictionary mapping level names to their numeric values

**Example:**
```python
from fogis_api_client import get_log_levels

levels = get_log_levels()
print(levels)
# {'CRITICAL': 50, 'ERROR': 40, 'WARNING': 30, 'INFO': 20, 'DEBUG': 10, 'NOTSET': 0}
```

### add_sensitive_filter

```python
add_sensitive_filter()
```

Adds a filter to mask sensitive information in log messages.

**Example:**
```python
from fogis_api_client import add_sensitive_filter, get_logger

add_sensitive_filter()
logger = get_logger("my_module")
logger.info("Password: secret123")  # Will log "Password: ********"
```

### SensitiveFilter

```python
SensitiveFilter(patterns=None)
```

A logging filter that masks sensitive information in log messages.

**Parameters:**
- `patterns` (Optional[Dict[str, str]]): A dictionary mapping patterns to their masked values

**Example:**
```python
from fogis_api_client import SensitiveFilter, get_logger
import logging

# Create a custom filter with additional patterns
filter = SensitiveFilter({
    "password": "********",
    "api_key": "[MASKED_API_KEY]",
    "secret": "[MASKED_SECRET]"
})

# Add the filter to a logger
logger = get_logger("my_module")
for handler in logger.handlers:
    handler.addFilter(filter)

logger.info("API Key: abc123")  # Will log "API Key: [MASKED_API_KEY]"
```
