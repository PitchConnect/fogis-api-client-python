"""
Internal API client for communicating with the FOGIS API server.

This module handles the low-level communication with the FOGIS API server,
ensuring that the data sent to and received from the server matches the expected format.
"""
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast

import requests
from bs4 import BeautifulSoup
from jsonschema import ValidationError

from fogis_api_client.internal.api_contracts import extract_endpoint_from_url, validate_request, validate_response
from fogis_api_client.internal.types import (
    InternalCookieDict,
    InternalEventDict,
    InternalMatchDict,
    InternalMatchListResponse,
    InternalMatchParticipantDict,
    InternalMatchResultDict,
    InternalOfficialActionDict,
    InternalOfficialDict,
    InternalPlayerDict,
    InternalTeamPlayersResponse,
)


class InternalApiError(Exception):
    """Exception raised when an internal API request fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class InternalApiClient:
    """
    Internal API client for communicating with the FOGIS API server.

    This class handles the low-level communication with the FOGIS API server,
    ensuring that the data sent to and received from the server matches the expected format.
    """

    BASE_URL: str = "https://fogis.svenskfotboll.se/mdk"
    logger: logging.Logger = logging.getLogger("fogis_api_client.internal.api")

    def __init__(self, session: requests.Session) -> None:
        """
        Initialize the internal API client.

        Args:
            session: The requests session to use for API calls
        """
        self.session = session

    def api_request(self, url: str, payload: Dict[str, Any]) -> Any:
        """
        Make an API request to the FOGIS API server.

        Args:
            url: The URL to send the request to
            payload: The payload to send with the request

        Returns:
            Any: The response data from the API

        Raises:
            InternalApiError: If the request fails
        """
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        }

        # Check if the URL is using the default base URL and replace it with the current base URL
        default_base_url = "https://fogis.svenskfotboll.se/mdk"
        if url.startswith(default_base_url):
            endpoint_path = url[len(default_base_url):]
            url = f"{self.BASE_URL}{endpoint_path}"
            self.logger.debug(f"Using current base URL: {url}")

        # Extract the endpoint for validation
        endpoint = extract_endpoint_from_url(url)

        # Validate the request payload
        try:
            validate_request(endpoint, payload)
        except ValidationError as e:
            error_msg = f"Request validation failed: {e}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg) from e
        except ValueError:
            # No schema defined for this endpoint, just log and continue
            self.logger.debug(f"No request schema defined for {endpoint}")

        try:
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()

            # Parse the JSON response
            response_data = response.json()

            # Extract the 'd' field if it exists (FOGIS API wraps responses in a 'd' field)
            if isinstance(response_data, dict) and "d" in response_data:
                # The 'd' field contains a JSON string that needs to be parsed
                try:
                    parsed_data = json.loads(response_data["d"])

                    # Validate the response
                    try:
                        validate_response(endpoint, parsed_data)
                    except ValidationError as e:
                        self.logger.warning(f"Response validation warning: {e}")
                    except ValueError:
                        # No schema defined for this response, just log and continue
                        self.logger.debug(f"No response schema defined for {endpoint}")

                    return parsed_data
                except (json.JSONDecodeError, TypeError):
                    # If parsing fails, return the raw 'd' field
                    return response_data["d"]

            return response_data

        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {e}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg) from e

    def get_matches_list(self, filter_params: Dict[str, Any]) -> InternalMatchListResponse:
        """
        Get the list of matches for the logged-in referee.

        Args:
            filter_params: Filter parameters for the match list

        Returns:
            InternalMatchListResponse: The match list response

        Raises:
            InternalApiError: If the request fails
        """
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatcherAttRapportera"

        # Build the payload with the filter parameters
        payload = {"filter": filter_params}

        response_data = self.api_request(url, payload)

        if not isinstance(response_data, dict) or "matchlista" not in response_data:
            error_msg = f"Invalid match list response: {response_data}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg)

        return cast(InternalMatchListResponse, response_data)

    def get_match(self, match_id: int) -> InternalMatchDict:
        """
        Get detailed information for a specific match.

        Args:
            match_id: The ID of the match

        Returns:
            InternalMatchDict: The match details

        Raises:
            InternalApiError: If the request fails
        """
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatch"
        payload = {"matchid": match_id}

        response_data = self.api_request(url, payload)

        if not isinstance(response_data, dict):
            error_msg = f"Invalid match response: {response_data}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg)

        return cast(InternalMatchDict, response_data)

    def get_match_players(self, match_id: int) -> Dict[str, List[InternalPlayerDict]]:
        """
        Get player information for a specific match.

        Args:
            match_id: The ID of the match

        Returns:
            Dict[str, List[InternalPlayerDict]]: Player information for the match

        Raises:
            InternalApiError: If the request fails
        """
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchdeltagareLista"
        payload = {"matchid": match_id}

        response_data = self.api_request(url, payload)

        if not isinstance(response_data, dict):
            error_msg = f"Invalid match players response: {response_data}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg)

        return cast(Dict[str, List[InternalPlayerDict]], response_data)

    def get_match_officials(self, match_id: int) -> Dict[str, List[InternalOfficialDict]]:
        """
        Get officials information for a specific match.

        Args:
            match_id: The ID of the match

        Returns:
            Dict[str, List[InternalOfficialDict]]: Officials information for the match

        Raises:
            InternalApiError: If the request fails
        """
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchfunktionarerLista"
        payload = {"matchid": match_id}

        response_data = self.api_request(url, payload)

        if not isinstance(response_data, dict):
            error_msg = f"Invalid match officials response: {response_data}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg)

        return cast(Dict[str, List[InternalOfficialDict]], response_data)

    def get_match_events(self, match_id: int) -> List[InternalEventDict]:
        """
        Get events information for a specific match.

        Args:
            match_id: The ID of the match

        Returns:
            List[InternalEventDict]: Events information for the match

        Raises:
            InternalApiError: If the request fails
        """
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchhandelselista"
        payload = {"matchid": match_id}

        response_data = self.api_request(url, payload)

        if not isinstance(response_data, list):
            error_msg = f"Invalid match events response: {response_data}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg)

        return cast(List[InternalEventDict], response_data)

    def get_team_players(self, team_id: int) -> InternalTeamPlayersResponse:
        """
        Get player information for a specific team.

        Args:
            team_id: The ID of the team

        Returns:
            InternalTeamPlayersResponse: Player information for the team

        Raises:
            InternalApiError: If the request fails
        """
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchdeltagareListaForMatchlag"
        payload = {"matchlagid": team_id}

        response_data = self.api_request(url, payload)

        # Handle different response formats
        if isinstance(response_data, dict) and "spelare" in response_data:
            return cast(InternalTeamPlayersResponse, response_data)
        elif isinstance(response_data, list):
            return cast(InternalTeamPlayersResponse, {"spelare": response_data})
        else:
            error_msg = f"Invalid team players response: {response_data}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg)

    def get_team_officials(self, team_id: int) -> List[InternalOfficialDict]:
        """
        Get officials information for a specific team.

        Args:
            team_id: The ID of the team

        Returns:
            List[InternalOfficialDict]: Officials information for the team

        Raises:
            InternalApiError: If the request fails
        """
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchlagledareListaForMatchlag"
        payload = {"matchlagid": team_id}

        response_data = self.api_request(url, payload)

        if not isinstance(response_data, list):
            error_msg = f"Invalid team officials response: {response_data}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg)

        return cast(List[InternalOfficialDict], response_data)

    def save_match_event(self, event_data: InternalEventDict) -> Dict[str, Any]:
        """
        Save a match event to the FOGIS API.

        Args:
            event_data: The event data to save

        Returns:
            Dict[str, Any]: The response from the API

        Raises:
            InternalApiError: If the request fails
        """
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchhandelse"

        response_data = self.api_request(url, event_data)

        if not isinstance(response_data, dict):
            error_msg = f"Invalid save match event response: {response_data}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg)

        return response_data

    def save_match_result(self, result_data: InternalMatchResultDict) -> Dict[str, Any]:
        """
        Save match results to the FOGIS API.

        Args:
            result_data: The match result data to save

        Returns:
            Dict[str, Any]: The response from the API

        Raises:
            InternalApiError: If the request fails
        """
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchresultatLista"

        response_data = self.api_request(url, result_data)

        if not isinstance(response_data, dict):
            error_msg = f"Invalid save match result response: {response_data}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg)

        return response_data

    def delete_match_event(self, event_id: int) -> Dict[str, Any]:
        """
        Delete a match event from the FOGIS API.

        Args:
            event_id: The ID of the event to delete

        Returns:
            Dict[str, Any]: The response from the API

        Raises:
            InternalApiError: If the request fails
        """
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/RaderaMatchhandelse"
        payload = {"matchhandelseid": event_id}

        response_data = self.api_request(url, payload)

        # Handle different response formats
        if response_data is None:
            # Original API returns None on successful deletion
            return {"success": True}
        elif isinstance(response_data, dict):
            return response_data
        else:
            error_msg = f"Invalid delete match event response: {response_data}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg)

    def save_team_official_action(self, action_data: InternalOfficialActionDict) -> Dict[str, Any]:
        """
        Save a team official action to the FOGIS API.

        Args:
            action_data: The team official action data to save

        Returns:
            Dict[str, Any]: The response from the API

        Raises:
            InternalApiError: If the request fails
        """
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchlagledare"

        response_data = self.api_request(url, action_data)

        if not isinstance(response_data, dict):
            error_msg = f"Invalid save team official action response: {response_data}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg)

        return response_data

    def clear_match_events(self, match_id: int) -> Dict[str, bool]:
        """
        Clear all events for a match.

        Args:
            match_id: The ID of the match

        Returns:
            Dict[str, bool]: The response from the API

        Raises:
            InternalApiError: If the request fails
        """
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/ClearMatchEvents"
        payload = {"matchid": match_id}

        response_data = self.api_request(url, payload)

        if not isinstance(response_data, dict):
            error_msg = f"Invalid clear match events response: {response_data}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg)

        return cast(Dict[str, bool], response_data)

    def get_match_result(self, match_id: int) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get the match results for a given match ID.

        Args:
            match_id: The ID of the match

        Returns:
            Union[Dict[str, Any], List[Dict[str, Any]]]: The match results

        Raises:
            InternalApiError: If the request fails
        """
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchresultatlista"
        payload = {"matchid": match_id}

        response_data = self.api_request(url, payload)

        if not isinstance(response_data, (dict, list)):
            error_msg = f"Invalid match result response: {response_data}"
            self.logger.error(error_msg)
            raise InternalApiError(error_msg)

        return response_data
