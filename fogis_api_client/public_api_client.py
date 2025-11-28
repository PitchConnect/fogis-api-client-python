"""
Enhanced FOGIS Public API Client with OAuth 2.0 Support

This module provides the main API client interface with support for both
OAuth 2.0 PKCE authentication and ASP.NET form authentication fallback.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

import requests

from fogis_api_client.internal.auth import (
    FogisAuthenticationError,
    FogisOAuthAuthenticationError,
    authenticate,
)


# Custom exceptions
class FogisLoginError(Exception):
    """Exception raised when login to FOGIS fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class FogisAPIRequestError(Exception):
    """Exception raised when an API request to FOGIS fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class FogisDataError(Exception):
    """Exception raised when FOGIS returns invalid or unexpected data."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class PublicApiClient:
    """
    Enhanced FOGIS API client with OAuth 2.0 PKCE support.

    This client automatically handles both OAuth 2.0 and ASP.NET authentication
    based on the server's response, providing seamless authentication regardless
    of which method FOGIS is using.
    """

    BASE_URL = "https://fogis.svenskfotboll.se/mdk"

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        oauth_tokens: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the FOGIS API client.

        Args:
            username: FOGIS username
            password: FOGIS password
            cookies: Optional pre-existing session cookies (ASP.NET)
            oauth_tokens: Optional pre-existing OAuth tokens
        """
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.logger = logging.getLogger("fogis_api_client.api")
        self.base_url = self.BASE_URL

        # Authentication state
        self.cookies: Optional[Dict[str, str]] = None
        self.oauth_tokens: Optional[Dict[str, Any]] = None
        self.authentication_method: Optional[str] = None  # 'oauth' or 'aspnet'

        # Initialize with provided authentication
        if oauth_tokens:
            self.oauth_tokens = oauth_tokens
            self.authentication_method = "oauth"
            # Set OAuth authorization header
            if "access_token" in oauth_tokens:
                self.session.headers["Authorization"] = f"Bearer {oauth_tokens['access_token']}"
            self.logger.info("Initialized with OAuth tokens")

        elif cookies:
            self.cookies = cookies
            self.authentication_method = "aspnet"
            # Add cookies to the session
            for key, value in cookies.items():
                if isinstance(value, str) and not key.startswith("oauth"):
                    self.session.cookies.set(key, value)
            self.logger.info("Initialized with ASP.NET cookies")

        elif not (username and password):
            raise ValueError("Either username and password OR cookies/oauth_tokens must be provided")

    def _check_existing_authentication(self) -> Optional[Union[Dict[str, str], Dict[str, Any]]]:
        """Check if already authenticated and return existing credentials."""
        if self.oauth_tokens and self.authentication_method == "oauth":
            self.logger.debug("Already authenticated with OAuth, using existing tokens")
            return self.oauth_tokens
        elif self.cookies and self.authentication_method == "aspnet":
            self.logger.debug("Already authenticated with ASP.NET, using existing cookies")
            return self.cookies
        return None

    def _handle_oauth_authentication_result(self, auth_result: Dict[str, Any]) -> Union[Dict[str, str], Dict[str, Any]]:
        """Handle OAuth authentication result."""
        if auth_result.get("authentication_method") == "oauth_hybrid":
            # OAuth hybrid: OAuth login but ASP.NET session cookies for API access
            self.cookies = {
                k: v for k, v in auth_result.items() if not k.startswith("oauth") and not k.startswith("authentication")
            }
            self.authentication_method = "oauth_hybrid"
            self.logger.info("OAuth hybrid authentication successful (OAuth login + ASP.NET cookies)")

            # Set cookies in session for API calls
            for key, value in self.cookies.items():
                self.session.cookies.set(key, value)

            return self.cookies
        else:
            # Pure OAuth authentication with tokens
            self.oauth_tokens = auth_result
            self.authentication_method = "oauth"
            self.logger.info("OAuth authentication successful")
            return self.oauth_tokens

    def login(self) -> Union[Dict[str, str], Dict[str, Any]]:
        """
        Logs into the FOGIS API using OAuth 2.0 or ASP.NET authentication.

        Returns:
            Authentication tokens/cookies if login is successful

        Raises:
            FogisLoginError: If login fails
            FogisAPIRequestError: If there is an error during the login request
        """
        # Check if already authenticated
        existing_auth = self._check_existing_authentication()
        if existing_auth is not None:
            return existing_auth

        # Validate credentials
        if not (self.username and self.password):
            error_msg = "Login failed: No credentials provided and no existing authentication available"
            self.logger.error(error_msg)
            raise FogisLoginError(error_msg)

        try:
            # Attempt authentication
            auth_result = authenticate(self.session, self.username, self.password, self.BASE_URL)

            # Process authentication result
            if "oauth_authenticated" in auth_result:
                return self._handle_oauth_authentication_result(auth_result)
            elif "aspnet_authenticated" in auth_result:
                # Traditional ASP.NET authentication
                self.cookies = {k: v for k, v in auth_result.items() if not k.startswith("aspnet")}
                self.authentication_method = "aspnet"
                self.logger.info("ASP.NET authentication successful")
                return self.cookies
            else:
                # Unknown authentication result
                self.logger.error("Unknown authentication result format")
                raise FogisLoginError("Authentication completed but result format is unknown")

        except FogisOAuthAuthenticationError as e:
            error_msg = f"OAuth authentication failed: {e}"
            self.logger.error(error_msg)
            raise FogisLoginError(error_msg) from e

        except FogisAuthenticationError as e:
            error_msg = f"Authentication failed: {e}"
            self.logger.error(error_msg)
            raise FogisLoginError(error_msg) from e

        except requests.exceptions.RequestException as e:
            error_msg = f"Login request failed: {e}"
            self.logger.error(error_msg)
            raise FogisAPIRequestError(error_msg) from e

    def refresh_authentication(self) -> bool:
        """
        Refresh authentication tokens/session.

        Returns:
            True if refresh was successful, False otherwise
        """
        if self.authentication_method == "oauth" and self.oauth_tokens:
            # Try to refresh OAuth tokens
            try:
                from fogis_api_client.internal.fogis_oauth_manager import FogisOAuthManager

                oauth_manager = FogisOAuthManager(self.session)

                # Set current tokens
                oauth_manager.access_token = self.oauth_tokens.get("access_token")
                oauth_manager.refresh_token = self.oauth_tokens.get("refresh_token")

                # Attempt refresh
                if oauth_manager.refresh_access_token():
                    # Update stored tokens
                    self.oauth_tokens.update(
                        {
                            "access_token": oauth_manager.access_token,
                            "refresh_token": oauth_manager.refresh_token,
                            "expires_in": oauth_manager.token_expires_in,
                        }
                    )
                    self.logger.info("OAuth tokens refreshed successfully")
                    return True
                else:
                    self.logger.error("OAuth token refresh failed")
                    return False

            except Exception as e:
                self.logger.error(f"Error refreshing OAuth tokens: {e}")
                return False

        elif self.authentication_method == "aspnet":
            # For ASP.NET, we need to re-authenticate
            try:
                self.cookies = None
                self.login()
                return True
            except Exception as e:
                self.logger.error(f"Error re-authenticating ASP.NET session: {e}")
                return False

        return False

    def is_authenticated(self) -> bool:
        """
        Check if the client is currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        if self.authentication_method == "oauth":
            return self.oauth_tokens is not None and "access_token" in self.oauth_tokens
        elif self.authentication_method in ["aspnet", "oauth_hybrid"]:
            return self.cookies is not None and len(self.cookies) > 0
        return False

    def get_authentication_info(self) -> Dict[str, Any]:
        """
        Get information about the current authentication state.

        Returns:
            Dictionary with authentication information
        """
        return {
            "method": self.authentication_method,
            "authenticated": self.is_authenticated(),
            "has_oauth_tokens": self.oauth_tokens is not None,
            "has_aspnet_cookies": self.cookies is not None,
            "oauth_token_info": (self.oauth_tokens.get("expires_in") if self.oauth_tokens else None),
        }

    def _ensure_authenticated(self) -> None:
        """
        Ensure the client is authenticated, performing login if necessary.

        Raises:
            FogisLoginError: If authentication fails
        """
        if not self.is_authenticated():
            self.logger.info("Not authenticated, performing automatic login...")
            self.login()

    def _make_authenticated_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make an authenticated request to the FOGIS API with proper headers and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            FogisAPIRequestError: If the request fails
        """
        # Ensure we're authenticated
        self._ensure_authenticated()

        # Prepare FOGIS-specific headers (same as original implementation)
        api_headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "https://fogis.svenskfotboll.se",
            "Referer": f"{self.BASE_URL}/",
            "X-Requested-With": "XMLHttpRequest",
        }

        # Merge with any provided headers
        if "headers" in kwargs:
            api_headers.update(kwargs["headers"])
        kwargs["headers"] = api_headers

        # Make the request
        try:
            response = self.session.request(method, url, **kwargs)

            # Check for authentication errors
            if response.status_code == 401:
                self.logger.warning("Received 401 Unauthorized, attempting to refresh authentication")
                if self.refresh_authentication():
                    # Retry the request
                    response = self.session.request(method, url, **kwargs)
                else:
                    raise FogisAPIRequestError("Authentication refresh failed")

            # Raise for HTTP errors
            response.raise_for_status()

            return response

        except requests.exceptions.RequestException as e:
            raise FogisAPIRequestError(f"Request failed: {e}")

    # Placeholder for additional API methods
    def fetch_matches_list_json(self, filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch the list of matches for the logged-in referee.

        Args:
            filter_params: Optional filter parameters

        Returns:
            List of match dictionaries
        """
        self.logger.info("Fetching matches list...")

        # Use the correct FOGIS API endpoint
        matches_url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatcherAttRapportera"

        # Build the default payload with the same structure as the working implementation
        from datetime import datetime, timedelta

        today = datetime.now().strftime("%Y-%m-%d")
        default_datum_fran = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")  # One week ago
        default_datum_till = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")  # 365 days ahead

        payload_filter = {
            "datumFran": default_datum_fran,
            "datumTill": default_datum_till,
            "datumTyp": 0,  # INTEGER, not string
            "typ": "alla",
            "status": ["avbruten", "uppskjuten", "installd"],
            "alderskategori": [1, 2, 3, 4, 5],
            "kon": [3, 2, 4],
            "sparadDatum": today,
        }

        # Update with any custom filter parameters
        if filter_params:
            payload_filter.update(filter_params)

        # Wrap the filter in the expected payload structure
        payload = {"filter": payload_filter}

        response = self._make_authenticated_request("POST", matches_url, json=payload)

        if response.status_code == 200:
            try:
                response_json = response.json()

                # FOGIS API returns data in a 'd' key (same as original implementation)
                if "d" in response_json:
                    # The 'd' value is a JSON string that needs to be parsed again
                    if isinstance(response_json["d"], str):
                        parsed_data = json.loads(response_json["d"])

                        # Extract matches from the response
                        if isinstance(parsed_data, dict) and "matchlista" in parsed_data:
                            return parsed_data["matchlista"]
                        elif isinstance(parsed_data, list):
                            return parsed_data
                        else:
                            return []
                    else:
                        # 'd' is already parsed
                        if isinstance(response_json["d"], dict) and "matchlista" in response_json["d"]:
                            return response_json["d"]["matchlista"]
                        elif isinstance(response_json["d"], list):
                            return response_json["d"]
                        else:
                            return []
                else:
                    # Fallback: direct response parsing
                    if isinstance(response_json, dict) and "matchlista" in response_json:
                        return response_json["matchlista"]
                    elif isinstance(response_json, list):
                        return response_json
                    else:
                        return []

            except json.JSONDecodeError as e:
                raise FogisAPIRequestError(f"Failed to parse API response: {e}")
        else:
            raise FogisAPIRequestError(f"Failed to fetch matches: {response.status_code}")

    def hello_world(self) -> str:
        """
        Return a hello world message for API compatibility.

        Returns:
            str: Hello world message
        """
        return "Hello, brave new world!"

    def get_match_details(self, match_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get match details from the comprehensive match list data.

        This method extracts match details from the match list response, which contains
        85 comprehensive fields including all necessary match information.

        Args:
            match_id: The ID of the match to get details for

        Returns:
            Dict containing match details from the match list

        Raises:
            FogisAPIRequestError: If the match is not found
        """
        self.logger.info(f"Getting match details for match ID: {match_id}")

        # Get all matches and find the specific one
        matches = self.fetch_matches_list_json()

        match_id_int = int(match_id)
        for match in matches:
            if match.get("matchid") == match_id_int:
                return match

        raise FogisAPIRequestError(f"Match with ID {match_id} not found in match list")

    def get_cookies(self) -> Dict[str, str]:
        """
        Get current session cookies.

        Returns:
            Dictionary of current cookies
        """
        cookies = {}
        for cookie in self.session.cookies:
            # Handle multiple cookies with same name by using the last one
            cookies[cookie.name] = cookie.value
        return cookies

    def get_match_players(self, match_id: Union[int, str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all players for a match using team-specific endpoints.

        This method uses the working team-specific endpoints to fetch players
        for both home and away teams.

        Args:
            match_id: The ID of the match to get players for

        Returns:
            Dict with 'hemmalag' and 'bortalag' keys containing player lists

        Raises:
            FogisAPIRequestError: If the match is not found or API request fails
        """
        self.logger.info(f"Getting players for match ID: {match_id}")

        # Get match details to find team IDs
        match_details = self.get_match_details(match_id)
        home_team_id = match_details.get("matchlag1id")
        away_team_id = match_details.get("matchlag2id")

        if not home_team_id or not away_team_id:
            raise FogisAPIRequestError(f"Could not find team IDs for match {match_id}")

        # Fetch players for both teams using working endpoints
        home_players_data = self.fetch_team_players_json(home_team_id)
        away_players_data = self.fetch_team_players_json(away_team_id)

        # Extract player lists from team responses
        home_players = home_players_data.get("spelare", []) if isinstance(home_players_data, dict) else home_players_data
        away_players = away_players_data.get("spelare", []) if isinstance(away_players_data, dict) else away_players_data

        return {"home": home_players, "away": away_players}

    def fetch_match_events_json(self, match_id: Union[int, str]) -> List[Dict[str, Any]]:
        """
        Fetch match events data in JSON format.

        Args:
            match_id: The ID of the match to fetch events for

        Returns:
            List of event dictionaries
        """
        self.logger.info(f"Fetching events for match ID: {match_id}")

        # Ensure we're authenticated
        if not self.is_authenticated():
            self.logger.info("Not authenticated, performing automatic login...")
            self.login()

        # Use correct FOGIS API endpoint for events
        events_url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchhandelselista"
        match_id_int = int(match_id) if isinstance(match_id, (str, int)) else match_id
        payload = {"matchid": match_id_int}

        response = self._make_authenticated_request("POST", events_url, json=payload)

        if response.status_code == 200:
            try:
                response_json = response.json()

                # FOGIS API returns data in a 'd' key
                if "d" in response_json:
                    if isinstance(response_json["d"], str):
                        import json

                        parsed_data = json.loads(response_json["d"])
                        if isinstance(parsed_data, list):
                            return parsed_data
                        elif isinstance(parsed_data, dict) and "events" in parsed_data:
                            return parsed_data["events"]
                        else:
                            return []
                    else:
                        if isinstance(response_json["d"], list):
                            return response_json["d"]
                        elif isinstance(response_json["d"], dict) and "events" in response_json["d"]:
                            return response_json["d"]["events"]
                        else:
                            return []
                else:
                    # Fallback: direct response parsing
                    if isinstance(response_json, list):
                        return response_json
                    elif isinstance(response_json, dict) and "events" in response_json:
                        return response_json["events"]
                    else:
                        return []

            except json.JSONDecodeError as e:
                raise FogisAPIRequestError(f"Failed to parse API response: {e}")
        else:
            raise FogisAPIRequestError(f"Failed to fetch match events: {response.status_code}")

    def get_match_officials(self, match_id: Union[int, str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all officials for a match using team-specific endpoints.

        This method uses the working team-specific endpoints to fetch officials
        for both home and away teams, plus referee information from match details.

        Args:
            match_id: The ID of the match to get officials for

        Returns:
            Dict with team officials and referee information

        Raises:
            FogisAPIRequestError: If the match is not found or API request fails
        """
        self.logger.info(f"Getting officials for match ID: {match_id}")

        # Get match details to find team IDs and referee info
        match_details = self.get_match_details(match_id)
        home_team_id = match_details.get("matchlag1id")
        away_team_id = match_details.get("matchlag2id")

        result = {}

        # Get team officials if team IDs are available
        if home_team_id:
            try:
                home_officials = self.fetch_team_officials_json(home_team_id)
                result["home"] = home_officials if isinstance(home_officials, list) else []
            except Exception as e:
                self.logger.warning(f"Could not fetch home team officials: {e}")
                result["home"] = []

        if away_team_id:
            try:
                away_officials = self.fetch_team_officials_json(away_team_id)
                result["away"] = away_officials if isinstance(away_officials, list) else []
            except Exception as e:
                self.logger.warning(f"Could not fetch away team officials: {e}")
                result["away"] = []

        # Note: Referees are kept in match_details.domaruppdraglista, not returned here
        # This method returns team officials only

        return result

    def fetch_team_officials_json(self, matchlagid: Union[int, str]) -> List[Dict[str, Any]]:
        """
        Fetch team officials data for a specific team in a match.

        Args:
            matchlagid: The match-specific team ID

        Returns:
            List of team officials

        Raises:
            FogisAPIRequestError: If the API request fails
        """
        self.logger.info(f"Fetching team officials for matchlagid: {matchlagid}")

        # Ensure we're authenticated
        if not self.is_authenticated():
            self.logger.info("Not authenticated, performing automatic login...")
            self.login()

        # Use the working team officials endpoint
        officials_url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchlagledareListaForMatchlag"
        matchlagid_int = int(matchlagid) if isinstance(matchlagid, (str, int)) else matchlagid
        payload = {"matchlagid": matchlagid_int}

        response = self._make_authenticated_request("POST", officials_url, json=payload)

        if response.status_code == 200:
            try:
                response_json = response.json()

                # FOGIS API returns data in a 'd' key
                if "d" in response_json:
                    if isinstance(response_json["d"], str):
                        import json

                        parsed_data = json.loads(response_json["d"])
                        return parsed_data if isinstance(parsed_data, list) else []
                    else:
                        return response_json["d"] if isinstance(response_json["d"], list) else []
                else:
                    # Fallback: direct response parsing
                    return response_json if isinstance(response_json, list) else []

            except json.JSONDecodeError as e:
                raise FogisAPIRequestError(f"Failed to parse API response: {e}")
        else:
            raise FogisAPIRequestError(f"Failed to fetch team officials: {response.status_code}")

    def fetch_team_players_json(self, team_id: Union[int, str]) -> Dict[str, Any]:
        """
        Fetch team players data for a specific team in a match.

        Args:
            team_id: The match-specific team ID (matchlagid)

        Returns:
            Dict containing team players with 'spelare' key

        Raises:
            FogisAPIRequestError: If the API request fails
        """
        self.logger.info(f"Fetching team players for team ID: {team_id}")

        # Ensure we're authenticated
        if not self.is_authenticated():
            self.logger.info("Not authenticated, performing automatic login...")
            self.login()

        # Use the working team players endpoint
        players_url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchdeltagareListaForMatchlag"
        team_id_int = int(team_id) if isinstance(team_id, (str, int)) else team_id
        payload = {"matchlagid": team_id_int}

        response = self._make_authenticated_request("POST", players_url, json=payload)

        if response.status_code == 200:
            try:
                response_json = response.json()

                # FOGIS API returns data in a 'd' key
                if "d" in response_json:
                    if isinstance(response_json["d"], str):
                        import json

                        parsed_data = json.loads(response_json["d"])
                        return parsed_data if isinstance(parsed_data, dict) else {"spelare": []}
                    else:
                        return response_json["d"] if isinstance(response_json["d"], dict) else {"spelare": []}
                else:
                    # Fallback: direct response parsing
                    return response_json if isinstance(response_json, dict) else {"spelare": []}

            except json.JSONDecodeError as e:
                raise FogisAPIRequestError(f"Failed to parse API response: {e}")
        else:
            raise FogisAPIRequestError(f"Failed to fetch team players: {response.status_code}")

    def fetch_match_result_json(self, match_id: Union[int, str]) -> Dict[str, Any]:
        """
        Fetch match result data in JSON format.

        Args:
            match_id: The ID of the match to fetch result for

        Returns:
            Dictionary containing match result
        """
        self.logger.info(f"Fetching result for match ID: {match_id}")

        # Ensure we're authenticated
        if not self.is_authenticated():
            self.logger.info("Not authenticated, performing automatic login...")
            self.login()

        # Use correct FOGIS API endpoint for result
        result_url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchresultatlista"
        match_id_int = int(match_id) if isinstance(match_id, (str, int)) else match_id
        payload = {"matchid": match_id_int}

        response = self._make_authenticated_request("POST", result_url, json=payload)

        if response.status_code == 200:
            try:
                response_json = response.json()

                # FOGIS API returns data in a 'd' key
                if "d" in response_json:
                    if isinstance(response_json["d"], str):
                        import json

                        parsed_data = json.loads(response_json["d"])
                        if isinstance(parsed_data, dict):
                            return parsed_data
                        elif isinstance(parsed_data, list) and len(parsed_data) > 0:
                            # Return first result if multiple results
                            return parsed_data[0]
                        else:
                            return {}
                    else:
                        if isinstance(response_json["d"], dict):
                            return response_json["d"]
                        elif isinstance(response_json["d"], list) and len(response_json["d"]) > 0:
                            # Return first result if multiple results
                            return response_json["d"][0]
                        else:
                            return {}
                else:
                    # Fallback: direct response parsing
                    if isinstance(response_json, dict):
                        return response_json
                    elif isinstance(response_json, list) and len(response_json) > 0:
                        # Return first result if multiple results
                        return response_json[0]
                    else:
                        return {}

            except json.JSONDecodeError as e:
                raise FogisAPIRequestError(f"Failed to parse API response: {e}")
        else:
            raise FogisAPIRequestError(f"Failed to fetch match result: {response.status_code}")

    # New convenience methods for improved API experience
    def fetch_complete_match(self, match_id: Union[int, str], include_optional: bool = True) -> Dict[str, Any]:
        """
        Fetch complete match information in a single call.

        This method aggregates all match-related data from multiple FOGIS endpoints
        and returns a unified, well-structured match object. It serves as both a
        convenience method and living documentation of how to properly fetch
        complete match data.

        Args:
            match_id: The ID of the match to fetch
            include_optional: Whether to include optional data (players, officials)
                             that might fail for some matches (default: True)

        Returns:
            Dict containing complete match data:
                - match_details: Basic match information (85 fields from match list)
                - players: Home and away team players (if include_optional=True)
                - officials: Team officials and referees (if include_optional=True)
                - events: Match events (goals, cards, substitutions)
                - result: Final match result
                - metadata: Fetch status, timing, and any warnings

        Raises:
            FogisAPIRequestError: If critical data (match details) cannot be fetched

        Examples:
            >>> client = PublicApiClient(username="user", password="pass")
            >>> client.login()
            >>>
            >>> # Get complete match data
            >>> match_data = client.fetch_complete_match(123456)
            >>>
            >>> # Check what data was successfully fetched
            >>> print(f"Teams: {match_data['match_details']['lag1namn']} vs {match_data['match_details']['lag2namn']}")
            >>> print(f"Events: {len(match_data['events'])} events")
            >>> print(f"Warnings: {match_data['metadata']['warnings']}")
            >>>
            >>> # Handle missing optional data gracefully
            >>> if match_data['players']:
            >>>     home_players = match_data['players']['hemmalag']
            >>>     print(f"Home team: {len(home_players)} players")
            >>> else:
            >>>     print("Player data not available")
        """
        from datetime import datetime

        self.logger.info(f"Fetching complete match data for match ID: {match_id}")

        result = {
            "match_id": match_id,
            "match_details": None,
            "players": None,
            "officials": None,
            "events": None,
            "result": None,
            "metadata": {
                "fetch_time": datetime.now().isoformat(),
                "success": {},
                "errors": {},
                "warnings": [],
                "include_optional": include_optional,
            },
        }

        # 1. CRITICAL: Match details (required)
        try:
            result["match_details"] = self.get_match_details(match_id)
            result["metadata"]["success"]["match_details"] = True
            self.logger.debug("✅ Match details fetched successfully")
        except Exception as e:
            result["metadata"]["errors"]["match_details"] = str(e)
            self.logger.error(f"❌ Failed to fetch critical match details: {e}")
            raise FogisAPIRequestError(f"Failed to fetch critical match details: {e}")

        # 2. IMPORTANT: Events and results (usually available)
        for endpoint_name, method in [("events", self.fetch_match_events_json), ("result", self.fetch_match_result_json)]:
            try:
                result[endpoint_name] = method(match_id)
                result["metadata"]["success"][endpoint_name] = True
                self.logger.debug(f"✅ {endpoint_name} fetched successfully")
            except Exception as e:
                result["metadata"]["errors"][endpoint_name] = str(e)
                result["metadata"]["warnings"].append(f"Could not fetch {endpoint_name}: {e}")
                self.logger.warning(f"⚠️ Could not fetch {endpoint_name}: {e}")

        # 3. OPTIONAL: Players and officials (might fail for some matches)
        if include_optional:
            for endpoint_name, method in [("players", self.get_match_players), ("officials", self.get_match_officials)]:
                try:
                    result[endpoint_name] = method(match_id)
                    result["metadata"]["success"][endpoint_name] = True
                    self.logger.debug(f"✅ {endpoint_name} fetched successfully")
                except Exception as e:
                    result["metadata"]["errors"][endpoint_name] = str(e)
                    result["metadata"]["warnings"].append(f"Could not fetch {endpoint_name}: {e}")
                    self.logger.warning(f"⚠️ Could not fetch {endpoint_name}: {e}")

        # Log summary
        successful_fetches = len(result["metadata"]["success"])
        total_attempted = 5 if include_optional else 3
        self.logger.info(f"Complete match fetch summary: {successful_fetches}/{total_attempted} endpoints successful")

        return result

    def get_recent_matches(self, days: int = 30, include_future: bool = False) -> List[Dict[str, Any]]:
        """
        Get recent matches within a specified time period.

        This convenience method simplifies fetching matches from recent dates
        without needing to construct complex filter parameters.

        Args:
            days: Number of days to look back from today (default: 30)
            include_future: Whether to include future matches (default: False)

        Returns:
            List of match dictionaries sorted by date (newest first)

        Examples:
            >>> client = PublicApiClient(username="user", password="pass")
            >>>
            >>> # Get matches from last 7 days
            >>> recent = client.get_recent_matches(days=7)
            >>> print(f"Found {len(recent)} matches in last 7 days")
            >>>
            >>> # Get matches from last 30 days including future matches
            >>> all_recent = client.get_recent_matches(days=30, include_future=True)
        """
        from datetime import datetime, timedelta

        self.logger.info(f"Fetching recent matches: {days} days back, include_future={include_future}")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        if include_future:
            # Extend end date to include future matches
            end_date = end_date + timedelta(days=30)

        # Build filter parameters
        filter_params = {"datumFran": start_date.strftime("%Y-%m-%d"), "datumTill": end_date.strftime("%Y-%m-%d")}

        # Fetch matches
        matches = self.fetch_matches_list_json(filter_params)

        # Sort by date (newest first)
        def get_match_date(match):
            try:
                return datetime.strptime(match.get("datum", "1900-01-01"), "%Y-%m-%d")
            except (ValueError, TypeError):
                return datetime.min

        sorted_matches = sorted(matches, key=get_match_date, reverse=True)

        self.logger.info(f"Found {len(sorted_matches)} recent matches")
        return sorted_matches

    def get_match_summary(self, match_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get a concise summary of match information.

        This method provides essential match information in a clean, structured format
        suitable for display purposes or quick overview.

        Args:
            match_id: The ID of the match

        Returns:
            Dict containing match summary with standardized keys

        Examples:
            >>> summary = client.get_match_summary(123456)
            >>> print(f"{summary['home_team']} vs {summary['away_team']}")
            >>> print(f"Date: {summary['date']}, Status: {summary['status']}")
        """
        self.logger.info(f"Getting match summary for match ID: {match_id}")

        # Get match details
        match_details = self.get_match_details(match_id)

        # Extract and standardize key information
        summary = {
            "match_id": match_details.get("matchid"),
            "home_team": match_details.get("lag1namn", "Unknown"),
            "away_team": match_details.get("lag2namn", "Unknown"),
            "date": match_details.get("datum"),
            "time": match_details.get("tid"),
            "venue": match_details.get("anlaggningnamn"),
            "status": match_details.get("status", "Unknown"),
            "competition": match_details.get("serienamn"),
            "referee_assigned": bool(match_details.get("domaruppdraglista")),
            "home_score": match_details.get("lag1resultat"),
            "away_score": match_details.get("lag2resultat"),
        }

        # Add computed fields
        if summary["home_score"] is not None and summary["away_score"] is not None:
            summary["final_score"] = f"{summary['home_score']}-{summary['away_score']}"
            summary["match_completed"] = True
        else:
            summary["final_score"] = None
            summary["match_completed"] = False

        self.logger.debug(f"Match summary: {summary['home_team']} vs {summary['away_team']}")
        return summary

    def get_match_events_by_type(self, match_id: Union[int, str], event_type: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get match events organized by type for easier processing.

        This method fetches match events and organizes them by type (goals, cards, etc.)
        for more convenient access and processing.

        Args:
            match_id: The ID of the match
            event_type: Optional filter for specific event type (e.g., 'goal', 'card')

        Returns:
            Dict with event types as keys and lists of events as values

        Examples:
            >>> events = client.get_match_events_by_type(123456)
            >>> print(f"Goals: {len(events.get('goals', []))}")
            >>> print(f"Cards: {len(events.get('cards', []))}")
            >>>
            >>> # Get only goals
            >>> goals = client.get_match_events_by_type(123456, event_type='goal')
        """
        self.logger.info(f"Getting match events by type for match ID: {match_id}")

        # Fetch all events
        events = self.fetch_match_events_json(match_id)

        # Organize by type
        events_by_type = {"goals": [], "cards": [], "substitutions": [], "other": []}

        for event in events:
            event_type_key = self._categorize_event(event)
            events_by_type[event_type_key].append(event)

        # Filter by specific type if requested
        if event_type:
            event_type_lower = event_type.lower()
            if event_type_lower in events_by_type:
                return {event_type_lower: events_by_type[event_type_lower]}
            else:
                return {event_type_lower: []}

        # Log summary
        summary = {k: len(v) for k, v in events_by_type.items() if v}
        self.logger.info(f"Events by type: {summary}")

        return events_by_type

    def _categorize_event(self, event: Dict[str, Any]) -> str:
        """Categorize an event based on its properties."""
        event_type = event.get("typ", "").lower()
        event_name = event.get("namn", "").lower()

        # Goal-related events
        if "mål" in event_type or "goal" in event_type or "mål" in event_name:
            return "goals"

        # Card-related events
        if "kort" in event_type or "card" in event_type or "gult" in event_name or "rött" in event_name:
            return "cards"

        # Substitution-related events
        if "byte" in event_type or "substitution" in event_type or "in" in event_name or "ut" in event_name:
            return "substitutions"

        return "other"

    def get_team_statistics(self, match_id: Union[int, str]) -> Dict[str, Dict[str, Any]]:
        """
        Get comprehensive team statistics for a match.

        This method aggregates player and event data to provide team-level statistics.

        Args:
            match_id: The ID of the match

        Returns:
            Dict with 'home' and 'away' keys containing team statistics

        Examples:
            >>> stats = client.get_team_statistics(123456)
            >>> home_stats = stats['home']
            >>> print(f"Home team players: {home_stats['player_count']}")
            >>> print(f"Home team goals: {home_stats['goals']}")
        """
        self.logger.info(f"Getting team statistics for match ID: {match_id}")

        # Get match data
        match_details = self.get_match_details(match_id)

        try:
            players = self.get_match_players(match_id)
            events_by_type = self.get_match_events_by_type(match_id)
        except Exception as e:
            self.logger.warning(f"Could not fetch complete data for statistics: {e}")
            players = {"home": [], "away": []}
            events_by_type = {"goals": [], "cards": [], "substitutions": []}

        # Build statistics
        stats = {
            "home": {
                "team_name": match_details.get("lag1namn", "Unknown"),
                "player_count": len(players.get("home", [])),
                "goals": len([g for g in events_by_type.get("goals", []) if self._is_home_team_event(g, match_details)]),
                "cards": len([c for c in events_by_type.get("cards", []) if self._is_home_team_event(c, match_details)]),
                "substitutions": len(
                    [s for s in events_by_type.get("substitutions", []) if self._is_home_team_event(s, match_details)]
                ),
            },
            "away": {
                "team_name": match_details.get("lag2namn", "Unknown"),
                "player_count": len(players.get("away", [])),
                "goals": len([g for g in events_by_type.get("goals", []) if not self._is_home_team_event(g, match_details)]),
                "cards": len([c for c in events_by_type.get("cards", []) if not self._is_home_team_event(c, match_details)]),
                "substitutions": len(
                    [s for s in events_by_type.get("substitutions", []) if not self._is_home_team_event(s, match_details)]
                ),
            },
        }

        self.logger.info(f"Team statistics: {stats['home']['team_name']} vs {stats['away']['team_name']}")
        return stats

    def _is_home_team_event(self, event: Dict[str, Any], match_details: Dict[str, Any]) -> bool:
        """Determine if an event belongs to the home team."""
        # This is a simplified implementation - in practice, you'd need to check
        # team IDs or player associations in the event data
        event_team = event.get("lag", "")
        home_team = match_details.get("lag1namn", "")

        return event_team == home_team or "hemma" in event_team.lower()

    def find_matches(
        self,
        team_name: str = None,
        date_from: str = None,
        date_to: str = None,
        status: List[str] = None,
        competition: str = None,
        limit: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Find matches using simplified search criteria.

        This convenience method provides an intuitive interface for finding matches
        without needing to understand FOGIS filter parameter structure.

        Args:
            team_name: Name of team to search for (partial match)
            date_from: Start date in YYYY-MM-DD format
            date_to: End date in YYYY-MM-DD format
            status: List of match statuses to include
            competition: Competition/series name to filter by
            limit: Maximum number of matches to return

        Returns:
            List of matching matches

        Examples:
            >>> # Find recent matches for a specific team
            >>> matches = client.find_matches(team_name="IFK", date_from="2025-01-01")
            >>>
            >>> # Find completed matches in a date range
            >>> completed = client.find_matches(
            ...     date_from="2025-01-01",
            ...     date_to="2025-01-31",
            ...     status=["klar"]
            ... )
        """
        self.logger.info(f"Finding matches with criteria: team={team_name}, dates={date_from} to {date_to}")

        # Build filter parameters
        filter_params = {}

        if date_from:
            filter_params["datumFran"] = date_from
        if date_to:
            filter_params["datumTill"] = date_to
        if status:
            filter_params["status"] = status

        # Fetch matches
        matches = self.fetch_matches_list_json(filter_params)

        # Apply additional filters
        filtered_matches = matches

        # Filter by team name
        if team_name:
            team_name_lower = team_name.lower()
            filtered_matches = [
                match
                for match in filtered_matches
                if (
                    team_name_lower in match.get("lag1namn", "").lower()
                    or team_name_lower in match.get("lag2namn", "").lower()
                )
            ]

        # Filter by competition
        if competition:
            competition_lower = competition.lower()
            filtered_matches = [match for match in filtered_matches if competition_lower in match.get("serienamn", "").lower()]

        # Apply limit
        if limit and limit > 0:
            filtered_matches = filtered_matches[:limit]

        self.logger.info(f"Found {len(filtered_matches)} matches matching criteria")
        return filtered_matches

    def get_matches_requiring_action(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get matches that require referee action or attention.

        This convenience method identifies matches that need referee attention,
        such as upcoming matches or matches requiring reports.

        Returns:
            Dict categorizing matches by action type

        Examples:
            >>> action_matches = client.get_matches_requiring_action()
            >>> upcoming = action_matches['upcoming']
            >>> print(f"You have {len(upcoming)} upcoming matches")
        """
        self.logger.info("Getting matches requiring action")

        from datetime import datetime, timedelta

        # Get matches from recent past and near future
        today = datetime.now()
        past_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")

        filter_params = {"datumFran": past_date, "datumTill": future_date}

        matches = self.fetch_matches_list_json(filter_params)

        # Categorize matches
        action_matches = {"upcoming": [], "needs_report": [], "recently_completed": [], "cancelled": []}

        today_str = today.strftime("%Y-%m-%d")

        for match in matches:
            match_date = match.get("datum", "")
            status = match.get("status", "").lower()

            if status in ["avbruten", "uppskjuten"]:
                action_matches["cancelled"].append(match)
            elif match_date > today_str:
                action_matches["upcoming"].append(match)
            elif status == "klar" and match_date >= (today - timedelta(days=3)).strftime("%Y-%m-%d"):
                action_matches["recently_completed"].append(match)
            elif status in ["pagar", "ej_pabörjad"] and match_date <= today_str:
                action_matches["needs_report"].append(match)

        # Log summary
        summary = {k: len(v) for k, v in action_matches.items() if v}
        self.logger.info(f"Matches requiring action: {summary}")

        return action_matches

    # Write operations for match reporting
    def save_match_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a match event (goal, card, substitution, etc.) to the FOGIS API.

        Args:
            event_data: Data containing match event details. Must include:
                - matchid: The ID of the match
                - matchhandelsetypid: The type ID of the event
                - Additional fields depending on event type (player IDs, minute, etc.)

        Returns:
            Dict[str, Any]: Response from the API, typically containing success status
                and the ID of the created event

        Raises:
            FogisLoginError: If not logged in
            FogisAPIRequestError: If there's an error with the API request
            FogisDataError: If the response data is invalid or not a dictionary

        Examples:
            >>> client = PublicApiClient(username="your_username", password="your_password")
            >>> # Save a goal event
            >>> event = {
            ...     "matchid": 123456,
            ...     "matchhandelsetypid": 1,  # Goal
            ...     "spelareid": 78910,
            ...     "minut": 25
            ... }
            >>> response = client.save_match_event(event)
            >>> print(f"Event saved successfully: {response.get('success', False)}")
            Event saved successfully: True
        """
        self.logger.info("Saving match event...")

        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchhandelse"
        response = self._make_authenticated_request("POST", url, json=event_data)

        if response.status_code == 200:
            try:
                response_json = response.json()

                # FOGIS API returns data in a 'd' key
                if "d" in response_json:
                    if isinstance(response_json["d"], str):
                        parsed_data = json.loads(response_json["d"])
                        if isinstance(parsed_data, dict):
                            return parsed_data
                        else:
                            return {"success": True, "data": parsed_data}
                    else:
                        if isinstance(response_json["d"], dict):
                            return response_json["d"]
                        else:
                            return {"success": True, "data": response_json["d"]}
                else:
                    # Fallback: direct response parsing
                    if isinstance(response_json, dict):
                        return response_json
                    else:
                        return {"success": True, "data": response_json}

            except json.JSONDecodeError as e:
                raise FogisAPIRequestError(f"Failed to parse API response: {e}")
        else:
            raise FogisAPIRequestError(f"Failed to save match event: {response.status_code}")

    def delete_match_event(self, event_id: Union[str, int]) -> bool:  # noqa: C901
        """
        Delete a specific event from a match.

        Args:
            event_id: The ID of the event to delete

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            FogisLoginError: If not logged in
            FogisAPIRequestError: If there's an error with the API request

        Examples:
            >>> client = PublicApiClient(username="your_username", password="your_password")
            >>> # Get all events for a match
            >>> events = client.fetch_match_events_json(123456)
            >>> if events:
            ...     # Delete the first event
            ...     event_id = events[0]['matchhandelseid']
            ...     success = client.delete_match_event(event_id)
            ...     print(f"Event deletion {'successful' if success else 'failed'}")
            Event deletion successful
        """
        self.logger.info(f"Deleting match event with ID: {event_id}")

        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/RaderaMatchhandelse"

        # Ensure event_id is an integer
        event_id_int = int(event_id) if isinstance(event_id, str) else event_id
        payload = {"matchhandelseid": event_id_int}

        try:
            response = self._make_authenticated_request("POST", url, json=payload)

            if response.status_code == 200:
                try:
                    response_json = response.json()

                    # Handle different response formats
                    if "d" in response_json:
                        if isinstance(response_json["d"], str):
                            parsed_data = json.loads(response_json["d"])
                            if isinstance(parsed_data, dict) and "success" in parsed_data:
                                return bool(parsed_data["success"])
                            # If parsed_data doesn't have success field, assume success
                            return True
                        elif isinstance(response_json["d"], dict) and "success" in response_json["d"]:
                            return bool(response_json["d"]["success"])
                        else:
                            # Original API returns None on successful deletion
                            return True
                    elif isinstance(response_json, dict) and "success" in response_json:
                        return bool(response_json["success"])
                    else:
                        # Assume success if we got a 200 response
                        return True

                except json.JSONDecodeError:
                    # If response is not JSON, assume success based on status code
                    return True
            else:
                return False

        except FogisAPIRequestError as e:
            self.logger.error(f"Error deleting event with ID {event_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error deleting event with ID {event_id}: {e}")
            return False

    def report_match_result(self, result_data: Dict[str, Any]) -> Dict[str, Any]:  # noqa: C901
        """
        Report match results (halftime and fulltime) to the FOGIS API.

        This method supports two different input formats:
        1. The flat format with direct fields (hemmamal, bortamal, etc.) - PREFERRED
        2. The nested format with matchresultatListaJSON array (for backward compatibility)

        Args:
            result_data: Data containing match results. Can be either:

                Format 1 (flat structure - PREFERRED):
                - matchid: The ID of the match
                - hemmamal: Full-time score for the home team
                - bortamal: Full-time score for the away team
                - halvtidHemmamal: Half-time score for the home team (optional)
                - halvtidBortamal: Half-time score for the away team (optional)

                Format 2 (nested structure - for backward compatibility):
                - matchresultatListaJSON: Array of match result objects with:
                  - matchid: The ID of the match
                  - matchresultattypid: 1 for full-time, 2 for half-time
                  - matchlag1mal: Score for team 1
                  - matchlag2mal: Score for team 2
                  - wo, ow, ww: Boolean flags

        Returns:
            Dict[str, Any]: Response from the API, typically containing success status

        Raises:
            FogisLoginError: If not logged in
            FogisAPIRequestError: If there's an error with the API request
            FogisDataError: If the response data is invalid or not a dictionary
            ValueError: If required fields are missing

        Examples:
            >>> client = PublicApiClient(username="your_username", password="your_password")
            >>> # Format 1 (flat structure)
            >>> result = {
            ...     "matchid": 123456,
            ...     "hemmamal": 2,
            ...     "bortamal": 1,
            ...     "halvtidHemmamal": 1,
            ...     "halvtidBortamal": 0
            ... }
            >>> response = client.report_match_result(result)
            >>> print(f"Result reported successfully: {response.get('success', False)}")
            Result reported successfully: True
        """
        self.logger.info("Reporting match result...")

        # Import the conversion function
        try:
            from fogis_api_client.api_contracts import convert_flat_to_nested_match_result
        except ImportError:
            # Fallback if api_contracts module is not available
            convert_flat_to_nested_match_result = None

        # Determine the format and convert if necessary
        if "matchresultatListaJSON" in result_data:
            # Already in the nested format for the API
            self.logger.info("Using nested matchresultatListaJSON format for reporting match result")
            result_data_copy = json.loads(json.dumps(result_data))

            # Ensure numeric fields are integers in each result object
            for result_obj in result_data_copy.get("matchresultatListaJSON", []):
                for field in ["matchid", "matchresultattypid", "matchlag1mal", "matchlag2mal"]:
                    if field in result_obj and result_obj[field] is not None:
                        value = result_obj[field]
                        if isinstance(value, str):
                            result_obj[field] = int(value)
        else:
            # We have the flat structure, need to convert to nested structure
            self.logger.info("Converting flat result structure to nested matchresultatListaJSON format")

            if convert_flat_to_nested_match_result:
                try:
                    result_data_copy = convert_flat_to_nested_match_result(result_data)
                except Exception as e:
                    error_msg = f"Invalid match result data: {e}"
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)
            else:
                # Manual conversion if api_contracts is not available
                match_id = result_data.get("matchid")
                if not match_id:
                    raise ValueError("Missing required field 'matchid' in result data")

                result_list = []

                # Full-time result
                if "hemmamal" in result_data and "bortamal" in result_data:
                    result_list.append(
                        {
                            "matchid": int(match_id),
                            "matchresultattypid": 1,  # Full-time
                            "matchlag1mal": int(result_data["hemmamal"]),
                            "matchlag2mal": int(result_data["bortamal"]),
                            "wo": result_data.get("wo", False),
                            "ow": result_data.get("ow", False),
                            "ww": result_data.get("ww", False),
                        }
                    )

                # Half-time result
                if "halvtidHemmamal" in result_data and "halvtidBortamal" in result_data:
                    result_list.append(
                        {
                            "matchid": int(match_id),
                            "matchresultattypid": 2,  # Half-time
                            "matchlag1mal": int(result_data["halvtidHemmamal"]),
                            "matchlag2mal": int(result_data["halvtidBortamal"]),
                            "wo": False,
                            "ow": False,
                            "ww": False,
                        }
                    )

                result_data_copy = {"matchresultatListaJSON": result_list}

        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchresultatLista"
        response = self._make_authenticated_request("POST", url, json=result_data_copy)

        if response.status_code == 200:
            try:
                response_json = response.json()

                # FOGIS API returns data in a 'd' key
                if "d" in response_json:
                    if isinstance(response_json["d"], str):
                        parsed_data = json.loads(response_json["d"])
                        if isinstance(parsed_data, dict):
                            return parsed_data
                        else:
                            return {"success": True, "data": parsed_data}
                    else:
                        if isinstance(response_json["d"], dict):
                            return response_json["d"]
                        else:
                            return {"success": True, "data": response_json["d"]}
                else:
                    # Fallback: direct response parsing
                    if isinstance(response_json, dict):
                        return response_json
                    else:
                        return {"success": True, "data": response_json}

            except json.JSONDecodeError as e:
                raise FogisAPIRequestError(f"Failed to parse API response: {e}")
        else:
            raise FogisAPIRequestError(f"Failed to report match result: {response.status_code}")

    def mark_reporting_finished(self, match_id: Union[str, int]) -> Dict[str, bool]:
        """
        Mark a match report as completed/finished in the FOGIS system.

        This is the final step in the referee reporting workflow that finalizes
        the match report and submits it officially.

        Args:
            match_id: The ID of the match to mark as finished

        Returns:
            Dict[str, bool]: The response from the FOGIS API, typically containing a success status

        Raises:
            FogisLoginError: If not logged in
            FogisAPIRequestError: If there's an error with the API request
            FogisDataError: If the response data is invalid or not a dictionary
            ValueError: If match_id is empty or invalid

        Examples:
            >>> client = PublicApiClient(username="your_username", password="your_password")
            >>> client.login()
            >>> result = client.mark_reporting_finished(match_id=123456)
            >>> print(f"Report marked as finished: {result.get('success', False)}")
            Report marked as finished: True
        """
        # Validate match_id
        if not match_id:
            error_msg = "match_id cannot be empty"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.info(f"Marking match ID {match_id} reporting as finished")

        # Ensure match_id is an integer
        match_id_int = int(match_id) if isinstance(match_id, (str, int)) else match_id
        payload = {"matchid": match_id_int}

        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchGodkannDomarrapport"
        response = self._make_authenticated_request("POST", url, json=payload)

        if response.status_code == 200:
            try:
                response_json = response.json()

                # FOGIS API returns data in a 'd' key
                if "d" in response_json:
                    if isinstance(response_json["d"], str):
                        parsed_data = json.loads(response_json["d"])
                        if isinstance(parsed_data, dict):
                            return parsed_data
                        else:
                            return {"success": True, "data": parsed_data}
                    else:
                        if isinstance(response_json["d"], dict):
                            return response_json["d"]
                        else:
                            return {"success": True, "data": response_json["d"]}
                else:
                    # Fallback: direct response parsing
                    if isinstance(response_json, dict):
                        return response_json
                    else:
                        return {"success": True, "data": response_json}

            except json.JSONDecodeError as e:
                raise FogisAPIRequestError(f"Failed to parse API response: {e}")
        else:
            raise FogisAPIRequestError(f"Failed to mark reporting finished: {response.status_code}")

    def save_match_participant(self, participant_data: Dict[str, Any]) -> Dict[str, Any]:  # noqa: C901
        """
        Update specific fields for a match participant in FOGIS while preserving other fields.

        This method is used to modify only the fields you specify (like jersey number, captain status, etc.)
        while keeping all other player information unchanged. You identify the player using their
        match-specific ID (matchdeltagareid), and provide only the fields you want to update.

        Args:
            participant_data: Data containing match participant details. Must include:
                - matchdeltagareid: The ID of the match participant
                - trojnummer: Jersey number
                - lagdelid: Team part ID (typically 0)
                - lagkapten: Boolean indicating if the player is team captain
                - ersattare: Boolean indicating if the player is a substitute
                - positionsnummerhv: Position number (typically 0)
                - arSpelandeLedare: Boolean indicating if the player is a playing leader
                - ansvarig: Boolean indicating if the player is responsible

        Returns:
            Dict[str, Any]: Response from the API containing the updated team roster

        Raises:
            FogisLoginError: If not logged in
            FogisAPIRequestError: If there's an error with the API request
            FogisDataError: If the response data is invalid or not a dictionary
            ValueError: If required fields are missing

        Examples:
            >>> client = PublicApiClient(username="your_username", password="your_password")
            >>> # Update a player's jersey number and set as captain
            >>> participant = {
            ...     "matchdeltagareid": 46123762,
            ...     "trojnummer": 10,
            ...     "lagkapten": True,
            ...     "ersattare": False,
            ...     "lagdelid": 0,
            ...     "positionsnummerhv": 0,
            ...     "arSpelandeLedare": False,
            ...     "ansvarig": False
            ... }
            >>> response = client.save_match_participant(participant)
            >>> print(f"Participant updated successfully: {response.get('success', False)}")
            Participant updated successfully: True
        """
        self.logger.info("Saving match participant...")

        # Ensure required fields are present
        required_fields = [
            "matchdeltagareid",
            "trojnummer",
            "lagdelid",
            "lagkapten",
            "ersattare",
            "positionsnummerhv",
            "arSpelandeLedare",
            "ansvarig",
        ]
        for field in required_fields:
            if field not in participant_data:
                error_msg = f"Missing required field '{field}' in participant data"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

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
                if isinstance(value, str):
                    participant_data_copy[field] = value.lower() == "true"
                elif not isinstance(value, bool):
                    participant_data_copy[field] = bool(value)

        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchdeltagare"
        response = self._make_authenticated_request("POST", url, json=participant_data_copy)

        if response.status_code == 200:
            try:
                response_json = response.json()

                # FOGIS API returns data in a 'd' key
                if "d" in response_json:
                    if isinstance(response_json["d"], str):
                        parsed_data = json.loads(response_json["d"])
                        if isinstance(parsed_data, dict):
                            return parsed_data
                        else:
                            return {"success": True, "data": parsed_data}
                    else:
                        if isinstance(response_json["d"], dict):
                            return response_json["d"]
                        else:
                            return {"success": True, "data": response_json["d"]}
                else:
                    # Fallback: direct response parsing
                    if isinstance(response_json, dict):
                        return response_json
                    else:
                        return {"success": True, "data": response_json}

            except json.JSONDecodeError as e:
                raise FogisAPIRequestError(f"Failed to parse API response: {e}")
        else:
            raise FogisAPIRequestError(f"Failed to save match participant: {response.status_code}")

    def save_team_official(self, official_data: Dict[str, Any]) -> Dict[str, Any]:  # noqa: C901
        """
        Report team official disciplinary action to the FOGIS API.

        Args:
            official_data: Data containing team official action details. Must include:
                - matchid: The ID of the match
                - lagid: The ID of the team
                - personid: The ID of the team official
                - matchlagledaretypid: The type ID of the disciplinary action

                Optional fields:
                - minut: The minute when the action occurred

        Returns:
            Dict[str, Any]: Response from the API, typically containing success status
                and the ID of the created action

        Raises:
            FogisLoginError: If not logged in
            FogisAPIRequestError: If there's an error with the API request
            FogisDataError: If the response data is invalid or not a dictionary
            ValueError: If required fields are missing

        Examples:
            >>> client = PublicApiClient(username="your_username", password="your_password")
            >>> # Report a yellow card for a team official
            >>> action = {
            ...     "matchid": 123456,
            ...     "lagid": 78910,  # Team ID
            ...     "personid": 12345,  # Official ID
            ...     "matchlagledaretypid": 1,  # Yellow card
            ...     "minut": 35
            ... }
            >>> response = client.save_team_official(action)
            >>> print(f"Action reported successfully: {response.get('success', False)}")
            Action reported successfully: True
        """
        self.logger.info("Saving team official action...")

        # Ensure required fields are present
        required_fields = ["matchid", "lagid", "personid", "matchlagledaretypid"]
        for field in required_fields:
            if field not in official_data:
                error_msg = f"Missing required field '{field}' in official data"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

        # Create a copy to avoid modifying the original
        official_data_copy = dict(official_data)

        # Ensure IDs are integers
        for key in ["matchid", "lagid", "personid", "matchlagledaretypid", "minut"]:
            if key in official_data_copy and official_data_copy[key] is not None:
                value = official_data_copy[key]
                if isinstance(value, str):
                    official_data_copy[key] = int(value)

        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchlagledare"
        response = self._make_authenticated_request("POST", url, json=official_data_copy)

        if response.status_code == 200:
            try:
                response_json = response.json()

                # FOGIS API returns data in a 'd' key
                if "d" in response_json:
                    if isinstance(response_json["d"], str):
                        parsed_data = json.loads(response_json["d"])
                        if isinstance(parsed_data, dict):
                            return parsed_data
                        else:
                            return {"success": True, "data": parsed_data}
                    else:
                        if isinstance(response_json["d"], dict):
                            return response_json["d"]
                        else:
                            return {"success": True, "data": response_json["d"]}
                else:
                    # Fallback: direct response parsing
                    if isinstance(response_json, dict):
                        return response_json
                    else:
                        return {"success": True, "data": response_json}

            except json.JSONDecodeError as e:
                raise FogisAPIRequestError(f"Failed to parse API response: {e}")
        else:
            raise FogisAPIRequestError(f"Failed to save team official: {response.status_code}")

    def clear_match_events(self, match_id: Union[str, int]) -> Dict[str, bool]:
        """
        Clear all events for a match.

        Args:
            match_id: The ID of the match

        Returns:
            Dict[str, bool]: Response from the API, typically containing a success status

        Raises:
            FogisLoginError: If not logged in
            FogisAPIRequestError: If there's an error with the API request
            FogisDataError: If the response data is invalid or not a dictionary

        Examples:
            >>> client = PublicApiClient(username="your_username", password="your_password")
            >>> response = client.clear_match_events(123456)
            >>> print(f"Events cleared successfully: {response.get('success', False)}")
            Events cleared successfully: True
        """
        self.logger.info(f"Clearing all events for match ID {match_id}")

        # Ensure match_id is an integer
        match_id_int = int(match_id) if isinstance(match_id, (str, int)) else match_id
        payload = {"matchid": match_id_int}

        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/ClearMatchEvents"
        response = self._make_authenticated_request("POST", url, json=payload)

        if response.status_code == 200:
            try:
                response_json = response.json()

                # FOGIS API returns data in a 'd' key
                if "d" in response_json:
                    if isinstance(response_json["d"], str):
                        parsed_data = json.loads(response_json["d"])
                        if isinstance(parsed_data, dict):
                            return parsed_data
                        else:
                            return {"success": True, "data": parsed_data}
                    else:
                        if isinstance(response_json["d"], dict):
                            return response_json["d"]
                        else:
                            return {"success": True, "data": response_json["d"]}
                else:
                    # Fallback: direct response parsing
                    if isinstance(response_json, dict):
                        return response_json
                    else:
                        return {"success": True, "data": response_json}

            except json.JSONDecodeError as e:
                raise FogisAPIRequestError(f"Failed to parse API response: {e}")
        else:
            raise FogisAPIRequestError(f"Failed to clear match events: {response.status_code}")

    # Backward compatibility methods (deprecated but functional)
    def fetch_match_json(self, match_id: Union[int, str]) -> Dict[str, Any]:
        """
        Fetch match details (backward compatibility method).

        .. deprecated:: 2.0.0
            Use :meth:`get_match_details` or :meth:`fetch_complete_match` instead.
            This method now uses the comprehensive match list data.

        Args:
            match_id: The ID of the match to fetch

        Returns:
            Dict containing match details

        Migration:
            Replace ``client.fetch_match_json(match_id)`` with:
            - ``client.get_match_details(match_id)`` for basic match info
            - ``client.fetch_complete_match(match_id)`` for comprehensive data
        """
        import warnings

        warnings.warn(
            "fetch_match_json() is deprecated and will be removed in v3.0. "
            "Use get_match_details() for basic info or fetch_complete_match() for comprehensive data.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_match_details(match_id)

    def fetch_match_players_json(self, match_id: Union[int, str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch match players (backward compatibility method).

        .. deprecated:: 2.0.0
            Use :meth:`get_match_players` or :meth:`fetch_complete_match` instead.
            This method now uses working team-specific endpoints.

        Args:
            match_id: The ID of the match to fetch players for

        Returns:
            Dict with 'hemmalag' and 'bortalag' keys containing player lists (legacy format)

        Migration:
            Replace ``client.fetch_match_players_json(match_id)`` with:
            - ``client.get_match_players(match_id)`` for player data with standardized names
            - ``client.fetch_complete_match(match_id)['players']`` for comprehensive data
        """
        import warnings

        warnings.warn(
            "fetch_match_players_json() is deprecated and will be removed in v3.0. "
            "Use get_match_players() or fetch_complete_match() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Get new format and convert to legacy format for backward compatibility
        new_format = self.get_match_players(match_id)
        return {"hemmalag": new_format.get("home", []), "bortalag": new_format.get("away", [])}

    def fetch_match_officials_json(self, match_id: Union[int, str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch match officials (backward compatibility method).

        .. deprecated:: 2.0.0
            Use :meth:`get_match_officials` or :meth:`fetch_complete_match` instead.
            This method now uses working team-specific endpoints.

        Args:
            match_id: The ID of the match to fetch officials for

        Returns:
            Dict with team officials and referee information (legacy format)

        Migration:
            Replace ``client.fetch_match_officials_json(match_id)`` with:
            - ``client.get_match_officials(match_id)`` for team officials with standardized names
            - ``client.fetch_complete_match(match_id)`` for comprehensive data including referees
        """
        import warnings

        warnings.warn(
            "fetch_match_officials_json() is deprecated and will be removed in v3.0. "
            "Use get_match_officials() or fetch_complete_match() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Get new format and convert to legacy format for backward compatibility
        new_format = self.get_match_officials(match_id)

        # Get referees from match details for legacy compatibility
        try:
            match_details = self.get_match_details(match_id)
            referees = match_details.get("domaruppdraglista", [])
        except Exception:
            referees = []

        return {"hemmalag": new_format.get("home", []), "bortalag": new_format.get("away", []), "domare": referees}


# Maintain backward compatibility
FogisApiClient = PublicApiClient
