"""
Public API client for the FOGIS API.

This module provides a client for interacting with the FOGIS API.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast

import requests
from bs4 import BeautifulSoup

from fogis_api_client.types import (
    CookieDict,
    EventDict,
    MatchDict,
    MatchListResponse,
    MatchParticipantDict,
    MatchResultDict,
    OfficialActionDict,
    OfficialDict,
    PlayerDict,
    TeamPlayersResponse,
)


class FogisApiError(Exception):
    """Base exception for all FOGIS API errors."""


class FogisLoginError(FogisApiError):
    """Exception raised when login fails."""


class FogisAPIRequestError(FogisApiError):
    """Exception raised when an API request fails."""


class FogisDataError(FogisApiError):
    """Exception raised when data validation fails."""


class FogisApiClient:
    """
    A client for interacting with the FOGIS API.

    This client implements lazy login, meaning it will automatically authenticate
    when making API requests if not already logged in. You can also explicitly call
    login() if you want to pre-authenticate.
    """

    BASE_URL: str = "https://fogis.svenskfotboll.se/mdk"
    logger: logging.Logger = logging.getLogger("fogis_api_client.api")

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        cookies: Optional[CookieDict] = None,
    ) -> None:
        self.username: Optional[str] = username
        self.password: Optional[str] = password
        self.session: requests.Session = requests.Session()
        self.cookies: Optional[CookieDict] = None

        if cookies:
            self.cookies = cookies
            for key, value in cookies.items():
                if isinstance(value, str):
                    self.session.cookies.set(key, value)
        elif not (username and password):
            raise ValueError("Either username and password OR cookies must be provided")

    def _api_request(self, url: str, payload: Optional[Dict[str, Any]] = None, method: str = "POST") -> Any:
        """Internal helper to make API requests."""
        if not self.cookies:
            self.login()

        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            if method.upper() == "POST":
                response = self.session.post(url, json=payload, headers=headers)
            elif method.upper() == "GET":
                response = self.session.get(url, params=payload, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            response_json = response.json()

            if "d" in response_json:
                if isinstance(response_json["d"], str):
                    try:
                        return json.loads(response_json["d"])
                    except json.JSONDecodeError:
                        return response_json["d"]
                return response_json["d"]
            return response_json
        except requests.exceptions.RequestException as e:
            raise FogisAPIRequestError(f"API request failed: {e}") from e
        except json.JSONDecodeError as e:
            raise FogisDataError(f"Failed to parse API response: {e}") from e

    def login(self) -> CookieDict:
        """Logs into the FOGIS API."""
        if self.cookies:
            return self.cookies
        if not (self.username and self.password):
            raise FogisLoginError("Login failed: No credentials provided.")

        login_url = f"{self.BASE_URL}/Login.aspx?ReturnUrl=%2fmdk%2f"
        try:
            response = self.session.get(login_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            form = soup.find("form", {"id": "aspnetForm"})
            if not form:
                raise FogisLoginError("Login failed: Could not find login form.")

            hidden_fields = {
                tag.get("name"): tag.get("value", "")
                for tag in form.find_all("input", {"type": "hidden"})
            }
            login_data = {
                **hidden_fields,
                "ctl00$MainContent$UserName": self.username,
                "ctl00$MainContent$Password": self.password,
                "ctl00$MainContent$LoginButton": "Logga in",
            }

            response = self.session.post(login_url, data=login_data, allow_redirects=False)
            if response.status_code == 302 and "FogisMobilDomarKlient.ASPXAUTH" in response.cookies:
                self.cookies = cast(CookieDict, self.session.cookies.get_dict())
                return self.cookies
            else:
                raise FogisLoginError("Login failed: Invalid credentials or session issue.")
        except requests.exceptions.RequestException as e:
            raise FogisAPIRequestError(f"Login request failed: {e}") from e

    def fetch_matches_list_json(self, filter_params: Optional[Dict[str, Any]] = None) -> MatchListResponse:
        """Fetch the list of matches for the logged-in referee."""
        if filter_params is None:
            today = datetime.now().strftime("%Y-%m-%d")
            next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            filter_params = {
                "datumFran": today, "datumTill": next_week, "datumTyp": 1,
                "status": ["Ej rapporterad", "Påbörjad rapportering"],
            }

        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatcherAttRapportera"
        payload = {"filter": filter_params}
        response_data = self._api_request(url, payload)

        if not isinstance(response_data, dict) or "matchlista" not in response_data:
            raise FogisDataError(f"Invalid match list response: {response_data}")
        return cast(MatchListResponse, response_data)

    def fetch_match_json(self, match_id: Union[int, str]) -> MatchDict:
        """Fetch detailed information for a specific match."""
        match_id_int = int(match_id)
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatch"
        payload = {"matchid": match_id_int}
        response_data = self._api_request(url, payload)

        if not isinstance(response_data, dict):
            raise FogisDataError(f"Invalid match response: {response_data}")
        return cast(MatchDict, response_data)

    def fetch_match_players_json(self, match_id: Union[int, str]) -> Dict[str, List[PlayerDict]]:
        """Fetch player information for a specific match."""
        match_id_int = int(match_id)
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchdeltagareLista"
        payload = {"matchid": match_id_int}
        response_data = self._api_request(url, payload)

        if not isinstance(response_data, dict):
            raise FogisDataError(f"Invalid match players response: {response_data}")
        return cast(Dict[str, List[PlayerDict]], response_data)

    def fetch_match_officials_json(self, match_id: Union[int, str]) -> Dict[str, List[OfficialDict]]:
        """Fetch officials information for a specific match."""
        match_id_int = int(match_id)
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchfunktionarerLista"
        payload = {"matchid": match_id_int}
        response_data = self._api_request(url, payload)

        if not isinstance(response_data, dict):
            raise FogisDataError(f"Invalid match officials response: {response_data}")
        return cast(Dict[str, List[OfficialDict]], response_data)

    def fetch_match_events_json(self, match_id: Union[int, str]) -> List[EventDict]:
        """Fetch events information for a specific match."""
        match_id_int = int(match_id)
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchhandelselista"
        payload = {"matchid": match_id_int}
        response_data = self._api_request(url, payload)

        if not isinstance(response_data, list):
            raise FogisDataError(f"Invalid match events response: {response_data}")
        return cast(List[EventDict], response_data)

    def fetch_team_players_json(self, team_id: Union[int, str]) -> TeamPlayersResponse:
        """Fetch player information for a specific team."""
        team_id_int = int(team_id)
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchdeltagareListaForMatchlag"
        payload = {"matchlagid": team_id_int}
        response_data = self._api_request(url, payload)

        if isinstance(response_data, dict) and "spelare" in response_data:
            return cast(TeamPlayersResponse, response_data)
        elif isinstance(response_data, list):
            return cast(TeamPlayersResponse, {"spelare": response_data})
        else:
            raise FogisDataError(f"Invalid team players response: {response_data}")

    def fetch_team_officials_json(self, team_id: Union[int, str]) -> List[OfficialDict]:
        """Fetch officials information for a specific team."""
        team_id_int = int(team_id)
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchlagledareListaForMatchlag"
        payload = {"matchlagid": team_id_int}
        response_data = self._api_request(url, payload)

        if not isinstance(response_data, list):
            raise FogisDataError(f"Invalid team officials response: {response_data}")
        return cast(List[OfficialDict], response_data)

    def report_match_event(self, event_data: EventDict) -> Dict[str, Any]:
        """Report a match event to the FOGIS API."""
        required_fields = ["matchid", "matchhandelsetypid", "matchminut", "matchlagid", "period"]
        if any(field not in event_data for field in required_fields):
            raise ValueError("Missing required field in event data")

        # In-line logic from convert_event_to_internal adapter
        internal_event = dict(event_data)
        internal_event.setdefault("sekund", 0)
        internal_event.setdefault("planpositionx", "-1")
        internal_event.setdefault("planpositiony", "-1")
        internal_event.setdefault("relateradTillMatchhandelseID", 0)
        if internal_event.get("matchhandelsetypid") != 17:
            internal_event.setdefault("spelareid2", -1)
            internal_event.setdefault("matchdeltagareid2", -1)
        for field in ["matchid", "matchhandelsetypid", "matchminut", "matchlagid", "spelareid", "assisterandeid", "period", "hemmamal", "bortamal", "sekund", "relateradTillMatchhandelseID", "spelareid2", "matchdeltagareid2"]:
            if field in internal_event and internal_event[field] is not None:
                internal_event[field] = int(internal_event[field])

        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchhandelse"
        response_data = self._api_request(url, internal_event)

        if not isinstance(response_data, dict):
            raise FogisDataError(f"Invalid save match event response: {response_data}")
        return response_data

    def fetch_match_result_json(self, match_id: Union[int, str]) -> MatchResultDict:
        """Fetch the match results for a given match ID."""
        match_id_int = int(match_id)
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/GetMatchresultatlista"
        payload = {"matchid": match_id_int}
        internal_result = self._api_request(url, payload)

        # In-line logic from convert_internal_to_match_result adapter
        if isinstance(internal_result, list):
            fulltime = next((r for r in internal_result if r.get("matchresultattypid") == 1), internal_result[0] if internal_result else {})
            halftime = next((r for r in internal_result if r.get("matchresultattypid") == 2), None)
            result_dict: MatchResultDict = {"matchid": fulltime.get("matchid"), "hemmamal": fulltime.get("matchlag1mal", 0), "bortamal": fulltime.get("matchlag2mal", 0)}
            if halftime:
                result_dict["halvtidHemmamal"] = halftime.get("matchlag1mal", 0)
                result_dict["halvtidBortamal"] = halftime.get("matchlag2mal", 0)
            return result_dict
        elif isinstance(internal_result, dict):
            if "matchresultatListaJSON" in internal_result:
                return self.fetch_match_result_json(match_id) # Recursive call for nested structure
            return cast(MatchResultDict, internal_result)
        raise FogisDataError(f"Invalid match result response: {internal_result}")

    def report_match_result(self, result_data: MatchResultDict) -> Dict[str, Any]:
        """Report match results to the FOGIS API."""
        # In-line logic from convert_match_result_to_internal adapter
        if "matchresultatListaJSON" in result_data:
            internal_result = json.loads(json.dumps(result_data))
            for res_obj in internal_result.get("matchresultatListaJSON", []):
                for field in ["matchid", "matchresultattypid", "matchlag1mal", "matchlag2mal"]:
                    if field in res_obj and res_obj[field] is not None:
                        res_obj[field] = int(res_obj[field])
        else:
            required_fields = ["matchid", "hemmamal", "bortamal"]
            if any(field not in result_data for field in required_fields):
                raise ValueError("Missing required fields in result data")
            match_id = int(result_data["matchid"])
            internal_result = {
                "matchresultatListaJSON": [
                    {"matchid": match_id, "matchresultattypid": 1, "matchlag1mal": int(result_data["hemmamal"]), "matchlag2mal": int(result_data["bortamal"]), "wo": False, "ow": False, "ww": False},
                    {"matchid": match_id, "matchresultattypid": 2, "matchlag1mal": int(result_data.get("halvtidHemmamal", 0)), "matchlag2mal": int(result_data.get("halvtidBortamal", 0)), "wo": False, "ow": False, "ww": False},
                ]
            }

        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchresultatLista"
        response_data = self._api_request(url, internal_result)

        if not isinstance(response_data, dict):
            raise FogisDataError(f"Invalid save match result response: {response_data}")
        return response_data

    def delete_match_event(self, event_id: Union[int, str]) -> Dict[str, Any]:
        """Delete a match event from the FOGIS API."""
        event_id_int = int(event_id)
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/RaderaMatchhandelse"
        payload = {"matchhandelseid": event_id_int}
        response_data = self._api_request(url, payload)

        if response_data is None:
            return {"success": True}
        elif isinstance(response_data, dict):
            return response_data
        raise FogisDataError(f"Invalid delete match event response: {response_data}")

    def report_team_official_action(self, action_data: OfficialActionDict) -> Dict[str, Any]:
        """Report a team official action to the FOGIS API."""
        required_fields = ["matchid", "matchlagid", "matchlagledareid", "matchlagledaretypid"]
        if any(field not in action_data for field in required_fields):
            raise ValueError("Missing required field in action data")

        internal_action = dict(action_data)
        for key in ["matchid", "matchlagid", "matchlagledareid", "matchlagledaretypid", "matchminut"]:
            if key in internal_action and internal_action[key] is not None:
                internal_action[key] = int(internal_action[key])

        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchlagledare"
        response_data = self._api_request(url, internal_action)

        if not isinstance(response_data, dict):
            raise FogisDataError(f"Invalid save team official action response: {response_data}")
        return response_data

    def save_match_participant(self, participant_data: MatchParticipantDict) -> Dict[str, Any]:
        """Save a match participant to the FOGIS API."""
        required_fields = ["matchdeltagareid", "trojnummer", "lagdelid"]
        if any(field not in participant_data for field in required_fields):
            raise ValueError("Missing required field in participant data")

        internal_participant = dict(participant_data)
        for field in ["matchdeltagareid", "trojnummer", "lagdelid", "positionsnummerhv"]:
            if field in internal_participant and internal_participant[field] is not None:
                internal_participant[field] = int(internal_participant[field])
        for field in ["lagkapten", "ersattare", "arSpelandeLedare", "ansvarig"]:
            if field in internal_participant and internal_participant[field] is not None:
                internal_participant[field] = bool(internal_participant[field])

        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchdeltagare"
        response_data = self._api_request(url, internal_participant)

        if not isinstance(response_data, dict):
            raise FogisDataError(f"Invalid save match participant response: {response_data}")
        return response_data

    def clear_match_events(self, match_id: Union[int, str]) -> Dict[str, bool]:
        """Clear all events for a match."""
        match_id_int = int(match_id)
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/ClearMatchEvents"
        payload = {"matchid": match_id_int}
        response_data = self._api_request(url, payload)

        if not isinstance(response_data, dict):
            raise FogisDataError(f"Invalid clear match events response: {response_data}")
        return cast(Dict[str, bool], response_data)

    def mark_reporting_finished(self, match_id: Union[int, str]) -> Dict[str, bool]:
        """Mark match reporting as finished."""
        if not match_id:
            raise ValueError("match_id cannot be empty")

        match_id_int = int(match_id)
        url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchGodkannDomarrapport"
        payload = {"matchid": match_id_int}
        response = self._api_request(url, payload)

        if not isinstance(response, dict):
            raise FogisDataError(f"Invalid mark reporting finished response: {response}")
        return cast(Dict[str, bool], response)

    def get_cookies(self) -> Optional[CookieDict]:
        """Get the current session cookies."""
        return self.cookies

    def hello_world(self) -> str:
        """Simple test method."""
        return "Hello, brave new world!"
