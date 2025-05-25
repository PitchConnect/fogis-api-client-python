"""
Adapters for converting between public and internal data formats.

This module contains functions for converting between the public API data formats
(what users of the library work with) and the internal API data formats
(what the FOGIS API server expects).
"""
import json
from typing import Any, Dict, List, Optional, Union, cast

from fogis_api_client.types import (
    CookieDict,
    EventDict,
    MatchDict,
    MatchParticipantDict,
    MatchResultDict,
    OfficialActionDict,
    OfficialDict,
    PlayerDict,
    TeamPlayersResponse,
)

from .types import (
    InternalCookieDict,
    InternalEventDict,
    InternalMatchDict,
    InternalMatchListResponse,
    InternalMatchParticipantDict,
    InternalMatchResultDict,
    InternalMatchResultItem,
    InternalOfficialActionDict,
    InternalOfficialDict,
    InternalPlayerDict,
    InternalTeamPlayersResponse,
)


def convert_match_result_to_internal(
    result_data: Union[MatchResultDict, Dict[str, Any]]
) -> InternalMatchResultDict:
    """
    Converts a public match result to the internal format expected by the API.

    Args:
        result_data: Match result data in either flat or nested format

    Returns:
        InternalMatchResultDict: Match result in the internal format

    Raises:
        ValueError: If required fields are missing
    """
    # If already in the nested format, just return a deep copy
    if "matchresultatListaJSON" in result_data:
        # Create a deep copy to avoid modifying the original
        result_data_copy = json.loads(json.dumps(result_data))

        # Ensure numeric fields are integers in each result object
        for result_obj in result_data_copy.get("matchresultatListaJSON", []):
            for field in ["matchid", "matchresultattypid", "matchlag1mal", "matchlag2mal"]:
                if field in result_obj and result_obj[field] is not None:
                    value = result_obj[field]
                    if isinstance(value, str):
                        result_obj[field] = int(value)

        return cast(InternalMatchResultDict, result_data_copy)

    # Otherwise, convert from flat format to nested format
    match_id = int(result_data["matchid"]) if isinstance(result_data["matchid"], str) else result_data["matchid"]
    fulltime_home = int(result_data["hemmamal"]) if isinstance(result_data["hemmamal"], str) else result_data["hemmamal"]
    fulltime_away = int(result_data["bortamal"]) if isinstance(result_data["bortamal"], str) else result_data["bortamal"]

    # Half-time scores are optional
    halftime_home = 0
    if "halvtidHemmamal" in result_data and result_data["halvtidHemmamal"] is not None:
        halftime_home = int(result_data["halvtidHemmamal"]) if isinstance(result_data["halvtidHemmamal"], str) else result_data["halvtidHemmamal"]

    halftime_away = 0
    if "halvtidBortamal" in result_data and result_data["halvtidBortamal"] is not None:
        halftime_away = int(result_data["halvtidBortamal"]) if isinstance(result_data["halvtidBortamal"], str) else result_data["halvtidBortamal"]

    # Create the nested structure
    nested_data: InternalMatchResultDict = {
        "matchresultatListaJSON": [
            {
                "matchid": match_id,
                "matchresultattypid": 1,  # Full time
                "matchlag1mal": fulltime_home,
                "matchlag2mal": fulltime_away,
                "wo": False,
                "ow": False,
                "ww": False,
            },
            {
                "matchid": match_id,
                "matchresultattypid": 2,  # Half-time
                "matchlag1mal": halftime_home,
                "matchlag2mal": halftime_away,
                "wo": False,
                "ow": False,
                "ww": False,
            },
        ]
    }

    return nested_data


def convert_internal_to_match_result(
    internal_result: Union[Dict[str, Any], List[Dict[str, Any]]]
) -> MatchResultDict:
    """
    Converts an internal match result to the public format.

    Args:
        internal_result: Match result data from the API

    Returns:
        MatchResultDict: Match result in the public format
    """
    # Handle different response formats
    if isinstance(internal_result, list):
        # If it's a list, find the full-time and half-time results
        fulltime_result = None
        halftime_result = None

        for result in internal_result:
            if result.get("matchresultattypid") == 1:  # Full-time
                fulltime_result = result
            elif result.get("matchresultattypid") == 2:  # Half-time
                halftime_result = result

        if not fulltime_result:
            # If no full-time result found, use the first item
            fulltime_result = internal_result[0] if internal_result else {}

        match_id = fulltime_result.get("matchid")
        hemmamal = fulltime_result.get("matchlag1mal", 0)
        bortamal = fulltime_result.get("matchlag2mal", 0)

        result_dict: MatchResultDict = {
            "matchid": match_id,
            "hemmamal": hemmamal,
            "bortamal": bortamal,
        }

        # Add half-time scores if available
        if halftime_result:
            result_dict["halvtidHemmamal"] = halftime_result.get("matchlag1mal", 0)
            result_dict["halvtidBortamal"] = halftime_result.get("matchlag2mal", 0)

        return result_dict

    elif isinstance(internal_result, dict):
        # If it's a dictionary, it might be a direct result or have a nested structure
        if "matchresultatListaJSON" in internal_result:
            # Nested structure, extract the results
            return convert_internal_to_match_result(internal_result["matchresultatListaJSON"])

        # Direct result format (might be from a different endpoint)
        result_dict: MatchResultDict = {
            "matchid": internal_result.get("matchid", 0),
            "hemmamal": internal_result.get("hemmamal", 0),
            "bortamal": internal_result.get("bortamal", 0),
        }

        # Add half-time scores if available
        if "halvtidHemmamal" in internal_result:
            result_dict["halvtidHemmamal"] = internal_result.get("halvtidHemmamal", 0)
        if "halvtidBortamal" in internal_result:
            result_dict["halvtidBortamal"] = internal_result.get("halvtidBortamal", 0)

        return result_dict

    # Fallback for unexpected formats
    return {"matchid": 0, "hemmamal": 0, "bortamal": 0}


def convert_event_to_internal(event_data: EventDict) -> InternalEventDict:
    """
    Converts a public event to the internal format expected by the API.

    Args:
        event_data: Event data in the public format

    Returns:
        InternalEventDict: Event data in the internal format
    """
    # Create a copy to avoid modifying the original
    event_data_copy = dict(event_data)

    # Apply default values for rarely used fields
    if "sekund" not in event_data_copy or event_data_copy["sekund"] is None:
        event_data_copy["sekund"] = 0

    if "planpositionx" not in event_data_copy or event_data_copy["planpositionx"] is None:
        event_data_copy["planpositionx"] = "-1"

    if "planpositiony" not in event_data_copy or event_data_copy["planpositiony"] is None:
        event_data_copy["planpositiony"] = "-1"

    if "relateradTillMatchhandelseID" not in event_data_copy or event_data_copy["relateradTillMatchhandelseID"] is None:
        event_data_copy["relateradTillMatchhandelseID"] = 0

    # Only set default values for second player fields if not a substitution
    is_substitution = event_data_copy.get("matchhandelsetypid") == 17

    if not is_substitution:
        if "spelareid2" not in event_data_copy or event_data_copy["spelareid2"] is None:
            event_data_copy["spelareid2"] = -1

        if "matchdeltagareid2" not in event_data_copy or event_data_copy["matchdeltagareid2"] is None:
            event_data_copy["matchdeltagareid2"] = -1

    # Ensure numeric fields are integers
    for field in [
        "matchid",
        "matchhandelsetypid",
        "matchminut",
        "matchlagid",
        "spelareid",
        "assisterandeid",
        "period",
        "hemmamal",
        "bortamal",
        "sekund",
        "relateradTillMatchhandelseID",
        "spelareid2",
        "matchdeltagareid2",
    ]:
        if field in event_data_copy and event_data_copy[field] is not None:
            value = event_data_copy[field]
            if isinstance(value, str):
                event_data_copy[field] = int(value)

    return cast(InternalEventDict, event_data_copy)


def convert_internal_to_event(internal_event: Dict[str, Any]) -> EventDict:
    """
    Converts an internal event to the public format.

    Args:
        internal_event: Event data from the API

    Returns:
        EventDict: Event data in the public format
    """
    # For now, the formats are the same, so we just cast
    return cast(EventDict, internal_event)


def convert_internal_to_match(internal_match: Dict[str, Any]) -> MatchDict:
    """
    Converts an internal match to the public format.

    Args:
        internal_match: Match data from the API

    Returns:
        MatchDict: Match data in the public format
    """
    # For now, the formats are the same, so we just cast
    return cast(MatchDict, internal_match)


def convert_internal_to_player(internal_player: Dict[str, Any]) -> PlayerDict:
    """
    Converts an internal player to the public format.

    Args:
        internal_player: Player data from the API

    Returns:
        PlayerDict: Player data in the public format
    """
    # For now, the formats are the same, so we just cast
    return cast(PlayerDict, internal_player)


def convert_internal_to_official(internal_official: Dict[str, Any]) -> OfficialDict:
    """
    Converts an internal official to the public format.

    Args:
        internal_official: Official data from the API

    Returns:
        OfficialDict: Official data in the public format
    """
    # For now, the formats are the same, so we just cast
    return cast(OfficialDict, internal_official)


def convert_official_action_to_internal(
    action_data: OfficialActionDict
) -> InternalOfficialActionDict:
    """
    Converts a public official action to the internal format expected by the API.

    Args:
        action_data: Official action data in the public format

    Returns:
        InternalOfficialActionDict: Official action data in the internal format
    """
    # Create a copy to avoid modifying the original
    action_data_copy = dict(action_data)


    # Ensure IDs are integers
    for key in ["matchid", "matchlagid", "matchlagledareid", "matchlagledaretypid", "matchminut"]:
        if key in action_data_copy and action_data_copy[key] is not None:
            value = action_data_copy[key]
            if isinstance(value, str):
                action_data_copy[key] = int(value)

    return cast(InternalOfficialActionDict, action_data_copy)


def convert_match_participant_to_internal(
    participant_data: MatchParticipantDict
) -> InternalMatchParticipantDict:
    """
    Converts a public match participant to the internal format expected by the API.

    Args:
        participant_data: Match participant data in the public format

    Returns:
        InternalMatchParticipantDict: Match participant data in the internal format
    """
    # Create a copy to avoid modifying the original
    participant_data_copy = dict(participant_data)

    # Ensure numeric fields are integers
    for field in ["matchdeltagareid", "trojnummer", "lagdelid", "positionsnummerhv"]:
        if field in participant_data_copy and participant_data_copy[field] is not None:
            value = participant_data_copy[field]
            if isinstance(value, str):
                participant_data_copy[field] = int(value)

    # Ensure boolean fields are booleans
    for field in ["lagkapten", "ersattare", "arSpelandeLedare", "ansvarig"]:
        if field in participant_data_copy and participant_data_copy[field] is not None:
            value = participant_data_copy[field]
            if not isinstance(value, bool):
                participant_data_copy[field] = bool(value)

    return cast(InternalMatchParticipantDict, participant_data_copy)


def convert_cookies_to_internal(cookies: CookieDict) -> InternalCookieDict:
    """
    Converts public cookies to the internal format.

    Args:
        cookies: Cookies in the public format

    Returns:
        InternalCookieDict: Cookies in the internal format
    """
    # For now, the formats are the same, so we just cast
    return cast(InternalCookieDict, cookies)


def convert_internal_to_cookies(internal_cookies: Dict[str, str]) -> CookieDict:
    """
    Converts internal cookies to the public format.

    Args:
        internal_cookies: Cookies from the API

    Returns:
        CookieDict: Cookies in the public format
    """
    # For now, the formats are the same, so we just cast
    return cast(CookieDict, internal_cookies)


def convert_internal_to_team_players(
    internal_response: Dict[str, Any]
) -> TeamPlayersResponse:
    """
    Converts an internal team players response to the public format.

    Args:
        internal_response: Team players data from the API

    Returns:
        TeamPlayersResponse: Team players data in the public format
    """
    # For tests that expect a dictionary with 'spelare' key
    if isinstance(internal_response, dict) and "spelare" in internal_response:
        return cast(TeamPlayersResponse, internal_response)
    # For tests that expect a list - wrap it in a dictionary
    elif isinstance(internal_response, list):
        return cast(TeamPlayersResponse, {"spelare": internal_response})
    else:
        # Unexpected format, return empty response
        return {"spelare": []}
