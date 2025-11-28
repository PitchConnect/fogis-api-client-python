"""
Mock FOGIS API Server for integration testing.

This module provides a Flask-based mock server that simulates the FOGIS API endpoints
for integration testing without requiring real credentials or internet access.
"""

import json
import logging
import os
import random
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, Response, jsonify, redirect, request, session

# Import request validator
from integration_tests.request_validator import RequestValidationError, RequestValidator

# Import data factory for the mock server
from integration_tests.sample_data_factory import MockDataFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockFogisServer:
    """A Flask-based mock server that simulates the FOGIS API endpoints."""

    def __init__(self, host: str = "localhost", port: int = 5001, oauth_mode: bool = False):
        """
        Initialize the mock server.

        Args:
            host: The host to run the server on
            port: The port to run the server on
            oauth_mode: If True, simulate OAuth redirect; if False, use ASP.NET form auth
                       Can also be controlled via MOCK_SERVER_OAUTH_MODE environment variable

        Note:
            OAuth mode is disabled by default because the real client checks for
            "auth.fogis.se" in the response URL, which cannot be simulated in a
            localhost mock server. To test OAuth flows, you need to either:
            1. Use ASP.NET form authentication (default)
            2. Mock/patch the OAuth detection logic in tests
            3. Use a proper DNS setup with auth.fogis.se pointing to localhost
        """
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.app.secret_key = "mock_fogis_server_secret_key"

        # OAuth mode configuration - can be overridden by environment variable
        self.oauth_mode = os.environ.get("MOCK_SERVER_OAUTH_MODE", str(oauth_mode)).lower() in ("true", "1", "yes")

        # Store registered users
        self.users = {
            "test_user": "test_password",
        }

        # Store session data
        self.sessions: Dict[str, Dict] = {}

        # Store OAuth tokens (token -> username mapping)
        self.oauth_tokens: Dict[str, str] = {}

        # Store OAuth authorization codes (code -> username mapping)
        self.oauth_codes: Dict[str, str] = {}

        # Store request history
        self.request_history: List[Dict[str, Any]] = []

        # Request validation flag
        self.validation_enabled = True

        # Server status
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.shutdown_requested = False

        # Store reported events
        self.reported_events: List[Dict] = []

        # Store request history for validation and debugging
        self.request_history: List[Dict[str, Any]] = []

        # Flag to enable/disable request validation
        self.validate_requests = True

        # Generate consistent sample data for testing
        self._initialize_sample_data()

        # Register routes
        self._register_routes()
        self._register_convenience_method_routes()

        # Register before_request handler to track all requests
        @self.app.before_request
        def track_request():
            """Track all requests to the server."""
            self._track_request(request.path)

    def _initialize_sample_data(self):
        """Initialize consistent sample data for testing."""
        # Generate a fixed set of matches for consistency
        self.sample_matches = []
        base_match_ids = [123456, 234567, 345678, 456789, 567890]

        for i, match_id in enumerate(base_match_ids):
            match = {
                "matchid": match_id,
                "matchnr": f"{100000 + i:06d}",
                "lag1namn": f"Home Team {i+1}",
                "lag2namn": f"Away Team {i+1}",
                "lag1resultat": i if i < 3 else None,  # Some completed matches
                "lag2resultat": (i + 1) % 3 if i < 3 else None,
                "datum": "2025-01-15",
                "tid": f"{19 + i % 3}:00",
                "anlaggningnamn": f"Stadium {i+1}",
                "status": "klar" if i < 3 else "ej_pabörjad",
                "serienamn": f"Division {(i % 3) + 1}",
                "matchlag1id": 1000 + i * 2,  # Team-specific IDs for players/officials
                "matchlag2id": 1000 + i * 2 + 1,
                "domaruppdraglista": [{"namn": f"Referee {i+1}", "roll": "Huvuddomare"}] if i % 2 == 0 else [],
            }
            self.sample_matches.append(match)

        # Store the match list response
        self.sample_match_list_response = {"matchlista": self.sample_matches}

    def _register_routes(self):
        """Register the API routes."""

        # Login route
        @self.app.route("/mdk/Login.aspx", methods=["GET", "POST"])
        def login():
            if request.method == "GET":
                # Check if OAuth mode is enabled
                if self.oauth_mode:
                    # Simulate OAuth redirect by returning a page that redirects to OAuth
                    # The client will follow this redirect and detect the OAuth flow
                    return_url = request.args.get("ReturnUrl", "/mdk/")
                    # Store return URL in session for later use
                    session["oauth_return_url"] = return_url

                    # Build OAuth authorization URL with PKCE parameters
                    # Simulate the parameters that FOGIS would use
                    import secrets
                    import urllib.parse

                    state = f"OpenIdConnect.AuthenticationProperties={secrets.token_urlsafe(32)}"
                    nonce = secrets.token_urlsafe(32)
                    code_challenge = secrets.token_urlsafe(32)

                    oauth_params = {
                        "client_id": "fogis.mobildomarklient",
                        "redirect_uri": f"http://{self.host}:{self.port}/mdk/signin-oidc",
                        "response_type": "code",
                        "scope": "openid fogis profile anvandare personid offline_access",
                        "code_challenge": code_challenge,
                        "code_challenge_method": "S256",
                        "state": state,
                        "nonce": nonce,
                    }

                    oauth_url = f"http://{self.host}:{self.port}/oauth/authorize?" + urllib.parse.urlencode(oauth_params)

                    # Return a redirect response that the client will follow
                    # The client checks for "auth.fogis.se" in response.url, but since
                    # we can't use that domain, we use a special path that simulates it
                    return redirect(oauth_url, code=302)
                else:
                    # Return ASP.NET login form
                    return """
                    <html>
                    <body>
                        <form method="post" id="aspnetForm">
                            <input type="hidden" name="__VIEWSTATE"
                                value="viewstate_value" />
                            <input type="hidden" name="__EVENTVALIDATION"
                                value="eventvalidation_value" />
                            <input type="text" name="ctl00$cphMain$tbUsername" />
                            <input type="password" name="ctl00$cphMain$tbPassword" />
                            <input type="text" name="ctl00$MainContent$UserName" />
                            <input type="password" name="ctl00$MainContent$Password" />
                            <input type="submit" name="ctl00$cphMain$btnLogin" value="Logga in" />
                            <input type="submit" name="ctl00$MainContent$LoginButton"
                                value="Logga in" />
                        </form>
                    </body>
                    </html>
                    """
            else:  # POST
                # Try both field name formats
                username = request.form.get("ctl00$cphMain$tbUsername") or request.form.get("ctl00$MainContent$UserName")
                password = request.form.get("ctl00$cphMain$tbPassword") or request.form.get("ctl00$MainContent$Password")

                if username in self.users and self.users[username] == password:
                    # Successful login
                    session["authenticated"] = True
                    session["username"] = username

                    # Set cookies - use the same cookie names as expected by the client
                    # The client checks for FogisMobilDomarKlient.ASPXAUTH (with a dot)
                    resp = Response("Login successful")
                    resp.set_cookie("FogisMobilDomarKlient.ASPXAUTH", "mock_auth_cookie")
                    resp.set_cookie("ASP.NET_SessionId", "mock_session_id")
                    resp.headers["Location"] = "/mdk/"
                    resp.status_code = 302
                    return resp
                else:
                    # Failed login - return 200 with a login page that has an error message
                    # This matches the behavior of the real FOGIS API
                    return """
                    <html>
                    <body>
                        <div class="error-message">Invalid username or password</div>
                        <form method="post" id="aspnetForm">
                            <input type="hidden" name="__VIEWSTATE"
                                value="viewstate_value" />
                            <input type="hidden" name="__EVENTVALIDATION"
                                value="eventvalidation_value" />
                            <input type="text" name="ctl00$cphMain$tbUsername" />
                            <input type="password" name="ctl00$cphMain$tbPassword" />
                            <input type="text" name="ctl00$MainContent$UserName" />
                            <input type="password" name="ctl00$MainContent$Password" />
                            <input type="submit" name="ctl00$cphMain$btnLogin" value="Logga in" />
                            <input type="submit" name="ctl00$MainContent$LoginButton"
                                value="Logga in" />
                        </form>
                    </body>
                    </html>
                    """

        # Match list endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/HamtaMatchLista", methods=["POST"])
        def fetch_matches_list():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Parse filter from request (not used in mock implementation)
            # request.json would contain filter parameters in a real implementation

            # Generate a fresh match list using the factory
            match_list_response = MockDataFactory.generate_match_list()

            # Return the response
            return jsonify(match_list_response)

        # Match list endpoint (new API version)
        @self.app.route("/mdk/MatchWebMetoder.aspx/GetMatcherAttRapportera", methods=["POST"])
        def fetch_matches_list_new():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Parse filter from request
            data = request.json or {}
            data.get("filter", {})

            # Use consistent sample match list data
            response_data = {
                "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatcherAttRapportera",
                "anvandare": None,
                "anvandareforeningid": 0,
                "anvandartyp": "Domare",
                "matchlista": self.sample_matches,  # Use consistent data
                "success": True,
            }

            # Return the response
            return jsonify({"d": json.dumps(response_data)})

        # Match details endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/HamtaMatch", methods=["POST"])
        def fetch_match():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get match ID from request
            data = request.json or {}
            match_id = data.get("matchid")

            # Find match in consistent data or generate new one
            match_data = None
            for match in self.sample_matches:
                if match["matchid"] == match_id:
                    match_data = match
                    break

            if not match_data:
                match_data = MockDataFactory.generate_match_details(match_id)

            return jsonify({"d": json.dumps(match_data)})

        # Match players endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/HamtaMatchSpelare", methods=["POST"])
        def fetch_match_players():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get match ID from request
            data = request.json or {}
            match_id = data.get("matchid")

            # Generate players data using the factory
            players_data = MockDataFactory.generate_match_players(match_id)

            # For match players, we need to keep the JSON structure
            return jsonify({"d": json.dumps(players_data)})

        # Match officials endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/HamtaMatchFunktionarer", methods=["POST"])
        def fetch_match_officials():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get match ID from request
            data = request.json or {}
            match_id = data.get("matchid")

            # Generate officials data using the factory
            officials_data = MockDataFactory.generate_match_officials_simple(match_id)

            # For match officials, we need to keep the JSON structure
            return jsonify({"d": json.dumps(officials_data)})

        # Match events endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/HamtaMatchHandelser", methods=["POST"])
        def fetch_match_events():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get match ID from request
            data = request.json or {}
            match_id = data.get("matchid")

            # Generate events data using the factory
            events_data = MockDataFactory.generate_match_events(match_id)

            # For match events, the response format is different
            # It's a direct array in the "d" field rather than a JSON string
            return jsonify({"d": events_data})

        # Match result endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/GetMatchresultatlista", methods=["POST"])
        def fetch_match_result():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get match ID from request
            data = request.json or {}
            match_id = data.get("matchid")

            # Generate result data using the factory
            result_data = MockDataFactory.generate_match_result(match_id)

            # For match results, the response format is different -
            # it's a direct array in the "d" field
            # rather than a JSON string
            return jsonify({"d": result_data})

        # Report match event endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/SparaMatchhandelse", methods=["POST"])
        def report_match_event():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get event data from request
            event_data = request.json or {}

            # Validate and log the request
            endpoint = "/MatchWebMetoder.aspx/SparaMatchhandelse"
            is_valid, error_msg = self._validate_and_log_request(endpoint, event_data)
            if not is_valid:
                return jsonify({"d": json.dumps({"success": False, "error": error_msg})}), 400

            # Store the reported event
            self.reported_events.append(event_data)

            # Return success response
            return jsonify({"d": json.dumps({"success": True, "id": len(self.reported_events)})})

        # Clear match events endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/RensaMatchhandelser", methods=["POST"])
        @self.app.route("/mdk/Fogis/Match/ClearMatchEvents", methods=["POST"])
        def clear_match_events():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get match ID from request (not used in mock implementation)
            # In a real implementation, we would use match_id to clear specific events

            # Clear all events (simplified implementation)
            self.reported_events = []

            # Return success response
            return jsonify({"d": json.dumps({"success": True})})

        # Mark reporting finished endpoint
        @self.app.route("/mdk/Fogis/Match/SparaMatchGodkannDomarrapport", methods=["POST"])
        def mark_reporting_finished():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get match ID from request (not used in mock implementation)
            # In a real implementation, we would use match_id to mark specific match as reported

            # Return success response with a dictionary containing success=true
            # This matches what the client expects
            return jsonify({"d": json.dumps({"success": True})})

        # Team players endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/GetMatchdeltagareListaForMatchlag", methods=["POST"])
        def fetch_team_players_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get team ID from request
            data = request.json or {}
            team_id = data.get("matchlagid")  # Use the correct parameter name

            # Generate team players data using the factory
            players_data = MockDataFactory.generate_team_players(team_id)

            # Return the response
            return jsonify({"d": json.dumps(players_data)})

        # Team officials endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/GetMatchlagledareListaForMatchlag", methods=["POST"])
        def fetch_team_officials_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get team ID from request
            data = request.json or {}
            team_id = data.get("matchlagid")  # Use the correct parameter name

            # Generate team officials data using the factory
            officials_data = MockDataFactory.generate_team_officials(team_id)

            # Return the response
            return jsonify({"d": json.dumps(officials_data)})

        # Match details endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/GetMatch", methods=["POST"])
        def fetch_match_details_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get match ID from request
            data = request.json or {}
            match_id = data.get("matchid")

            # Generate match data using the factory
            match_data = MockDataFactory.generate_match_details(match_id)

            # Return the response
            return jsonify({"d": json.dumps(match_data)})

        # Match players endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/GetMatchdeltagareLista", methods=["POST"])
        def fetch_match_players_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get match ID from request
            data = request.json or {}
            match_id = data.get("matchid")

            # Validate and log the request
            endpoint = "/MatchWebMetoder.aspx/GetMatchdeltagareLista"
            is_valid, error_msg = self._validate_and_log_request(endpoint, data)
            if not is_valid:
                return jsonify({"d": json.dumps({"success": False, "error": error_msg})}), 400

            # Generate match players data using the factory
            players_data = MockDataFactory.generate_match_players(match_id)

            # Return the response
            return jsonify({"d": json.dumps(players_data)})

        # Match officials endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/GetMatchfunktionarerLista", methods=["POST"])
        def fetch_match_officials_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get match ID from request
            data = request.json or {}
            data.get("matchid")

            # Validate and log the request
            endpoint = "/MatchWebMetoder.aspx/GetMatchfunktionarerLista"
            is_valid, error_msg = self._validate_and_log_request(endpoint, data)
            if not is_valid:
                return jsonify({"d": json.dumps({"success": False, "error": error_msg})}), 400

            # Generate match officials data using the factory
            # The client expects a dictionary with keys 'hemmalag' and 'bortalag',
            # each containing a list of officials
            officials_data = {
                "hemmalag": [
                    {
                        "personid": 11111,
                        "fornamn": "John",
                        "efternamn": "Doe",
                        "roll": "Tränare",
                        "rollid": 1,
                        "matchlagid": 12345,
                    }
                ],
                "bortalag": [
                    {
                        "personid": 22222,
                        "fornamn": "Jane",
                        "efternamn": "Smith",
                        "roll": "Assisterande tränare",
                        "rollid": 2,
                        "matchlagid": 67890,
                    }
                ],
            }

            # Return the response
            return jsonify({"d": json.dumps(officials_data)})

        # Match events endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/GetMatchhandelselista", methods=["POST"])
        def fetch_match_events_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get match ID from request
            data = request.json or {}
            match_id = data.get("matchid")

            # Generate match events data using the factory
            events_data = MockDataFactory.generate_match_events(match_id)

            # Return the response
            return jsonify({"d": json.dumps(events_data)})

        # Match result endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/GetMatchresultat", methods=["POST"])
        def fetch_match_result_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get match ID from request
            data = request.json or {}
            match_id = data.get("matchid")

            # Generate match result data using the factory
            result_data = MockDataFactory.generate_match_result(match_id)

            # Return the response
            return jsonify({"d": json.dumps(result_data)})

        # Match result list endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/GetMatchresultatlista", methods=["POST"])
        def fetch_match_result_list_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get match ID from request
            data = request.json or {}
            match_id = data.get("matchid")

            # Validate and log the request
            endpoint = "/MatchWebMetoder.aspx/GetMatchresultatlista"
            is_valid, error_msg = self._validate_and_log_request(endpoint, data)
            if not is_valid:
                return jsonify({"d": json.dumps({"success": False, "error": error_msg})}), 400

            # Generate match result list data using the factory
            result_list_data = MockDataFactory.generate_match_result_list(match_id)

            # Return the response
            return jsonify({"d": json.dumps(result_list_data)})

        # Clear match events endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/ClearMatchEvents", methods=["POST"])
        def clear_match_events_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Return success response
            return jsonify({"d": json.dumps({"success": True})})

        # Report match event endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/SparaMatchhandelse", methods=["POST"])
        def report_match_event_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Return success response
            return jsonify({"d": json.dumps({"success": True})})

        # Delete match event endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/RaderaMatchhandelse", methods=["POST"])
        def delete_match_event_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get event ID from request
            data = request.json or {}
            data.get("matchhandelseid")

            # Validate and log the request
            endpoint = "/MatchWebMetoder.aspx/RaderaMatchhandelse"
            is_valid, error_msg = self._validate_and_log_request(endpoint, data)
            if not is_valid:
                return jsonify({"d": json.dumps({"success": False, "error": error_msg})}), 400

            # In a real implementation, we would delete the event with the given ID
            # For the mock server, we just return success

            # Return success response
            return jsonify({"d": json.dumps({"success": True})})

        # Mark reporting finished endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/SparaMatchGodkannDomarrapport", methods=["POST"])
        def mark_reporting_finished_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Return success response
            return jsonify({"d": json.dumps({"success": True})})

        # Report match result endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/SparaMatchresultatLista", methods=["POST"])
        def report_match_result():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get result data from request
            result_data = request.json or {}

            # Validate and log the request
            endpoint = "/MatchWebMetoder.aspx/SparaMatchresultatLista"
            is_valid, error_msg = self._validate_and_log_request(endpoint, result_data)
            if not is_valid:
                return jsonify({"d": json.dumps({"success": False, "error": error_msg})}), 400

            # Log the match result data for debugging
            logger.info(f"Received match result data: {json.dumps(result_data, indent=2)}")

            # Return success response
            return jsonify({"d": json.dumps({"success": True})})

        # Save match participant endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/SparaMatchdeltagare", methods=["POST"])
        def save_match_participant_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get participant data from request
            data = request.json or {}
            match_deltagare_id = data.get("matchdeltagareid")

            if not match_deltagare_id:
                return jsonify({"d": json.dumps({"error": "Missing matchdeltagareid"})}), 400

            # Generate a team roster with the updated player
            team_id = random.randint(10000, 99999)  # Generate a random team ID
            roster = MockDataFactory.generate_team_players(team_id)

            # Find or create the player with the specified matchdeltagareid
            updated_player = None
            for player in roster["spelare"]:
                if random.random() < 0.2:  # 20% chance to match this player
                    # Update this player to match the requested changes
                    player["matchdeltagareid"] = match_deltagare_id
                    player["trojnummer"] = data.get("trojnummer", player.get("tshirt", 0))
                    player["lagkapten"] = data.get("lagkapten", False)
                    player["ersattare"] = data.get("ersattare", False)
                    updated_player = player
                    break

            # If we didn't find a player to update, add one
            if not updated_player:
                new_player = {
                    "matchdeltagareid": match_deltagare_id,
                    "personid": MockDataFactory.generate_id(),
                    "fornamn": MockDataFactory.generate_name(True),
                    "efternamn": MockDataFactory.generate_name(False),
                    "trojnummer": data.get("trojnummer", random.randint(1, 99)),
                    "lagkapten": data.get("lagkapten", False),
                    "ersattare": data.get("ersattare", False),
                    "position": random.choice(["Målvakt", "Försvarare", "Mittfältare", "Anfallare"]),
                    "matchlagid": team_id,
                    "fodelsedatum": MockDataFactory.generate_date(False),
                    "licensnummer": f"LIC{random.randint(100000, 999999)}",
                    "spelarregistreringsstrang": "",
                    "spelareAntalAckumuleradeVarningar": random.randint(0, 2),
                    "spelareAvstangningBeskrivning": "",
                }
                roster["spelare"].append(new_player)

            return jsonify({"d": json.dumps(roster)})

        # Save team official action endpoint
        @self.app.route("/mdk/MatchWebMetoder.aspx/SparaMatchlagledare", methods=["POST"])
        def save_team_official_action_endpoint():
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Get team official data from request
            data = request.json or {}

            # Validate and log the request
            endpoint = "/MatchWebMetoder.aspx/SparaMatchlagledare"
            is_valid, error_msg = self._validate_and_log_request(endpoint, data)
            if not is_valid:
                return jsonify({"d": json.dumps({"success": False, "error": error_msg})}), 400

            # In a real implementation, we would save the team official action
            # For the mock server, we just return success

            # Return success response
            return jsonify({"d": json.dumps({"success": True})})

        # Main dashboard route after login
        @self.app.route("/mdk/", methods=["GET"])
        def dashboard():
            # Check if the user is authenticated
            auth_result = self._check_auth()
            if auth_result is not True:
                return auth_result

            # Return a simple dashboard page
            return "<html><body><h1>FOGIS Mock Dashboard</h1></body></html>"

        # Health check endpoint
        @self.app.route("/health", methods=["GET"])
        def health():
            # Include more detailed information for debugging
            return jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "server": {
                        "host": self.host,
                        "port": self.port,
                        "url": self.get_url(),
                    },
                    "version": "1.0.0",
                }
            )

        # Hello world endpoint (for testing)
        @self.app.route("/hello", methods=["GET"])
        def hello():
            return jsonify({"message": "Hello, brave new world!"})

        # Request history endpoint (for debugging and testing)
        @self.app.route("/request-history", methods=["GET"])
        def request_history():
            return jsonify(
                {
                    "history": self.request_history,
                    "count": len(self.request_history),
                }
            )

        # Clear request history endpoint (for debugging and testing)
        @self.app.route("/clear-request-history", methods=["POST"])
        def clear_request_history():
            self.clear_request_history()
            return jsonify({"success": True, "message": "Request history cleared"})

    def _check_auth(self):
        """Check if the request is authenticated."""
        # Check for OAuth Bearer token in Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            # Verify the token exists in our token store
            if token in self.oauth_tokens:
                return True

        # Check if the user is authenticated via session or cookies
        if session.get("authenticated") or request.cookies.get("FogisMobilDomarKlient.ASPXAUTH"):
            return True

        # For testing purposes, we'll also accept cookie-based authentication
        if "FogisMobilDomarKlient.ASPXAUTH" in request.cookies:
            return True

        # If we're here, the user is not authenticated
        return Response("Unauthorized", status=401)

    def _validate_and_log_request(self, endpoint: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate and log a request.

        Args:
            endpoint: The API endpoint
            data: The request data

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Store the request for later analysis
        request_record = {
            "endpoint": endpoint,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "headers": dict(request.headers),
        }
        self.request_history.append(request_record)

        # Log the request
        logger.info(f"Request to {endpoint}:")
        logger.info(json.dumps(data, indent=2, default=str))

        # Skip validation if disabled
        if not self.validate_requests:
            return True, None

        # Validate the request
        try:
            RequestValidator.validate_request(endpoint, data)
            return True, None
        except RequestValidationError as e:
            error_msg = str(e)
            logger.error(f"Request validation failed: {error_msg}")
            return False, error_msg

    def run(self, threaded=False):
        """Run the mock server.

        Args:
            threaded: If True, run the server in a separate thread
        """
        logger.info(f"Starting mock FOGIS server on {self.host}:{self.port}")

        # Set the running flag before registering routes
        self.is_running = True

        # Register CLI API routes
        try:
            self._register_cli_routes()
        except AttributeError:
            # The _register_cli_routes method might not exist in older versions
            logger.warning("CLI API routes not registered")

        if threaded:
            self.server_thread = threading.Thread(target=self._run_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            return self.server_thread
        else:
            self._run_server()

    def _run_server(self):
        """Run the Flask server."""
        self.app.run(host=self.host, port=self.port, threaded=True)

    def shutdown(self):
        """Shutdown the server."""
        self.is_running = False

        try:
            # Try to use the Werkzeug shutdown function
            func = request.environ.get("werkzeug.server.shutdown")
            if func is not None:
                func()
                return
        except Exception as e:
            logger.warning(f"Error shutting down server: {e}")

        # If we can't use the Werkzeug shutdown function, try to stop the thread
        if self.server_thread is not None and self.server_thread.is_alive():
            # We can't really stop the thread, but we can set the flag
            # and let it exit gracefully
            logger.info("Server thread is still running, setting shutdown flag")
            self.is_running = False

    def _track_request(self, endpoint: str):
        """Track a request in the request history.

        Args:
            endpoint: The endpoint that was requested
        """
        request_data = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "endpoint": endpoint,
            "path": request.path,
            "args": dict(request.args),
            "headers": dict(request.headers),
            "data": request.get_data(as_text=True) if request.data else None,
            "json": request.json if request.is_json else None,
            "form": dict(request.form) if request.form else None,
        }
        self.request_history.append(request_data)

    def get_url(self) -> str:
        """Get the URL of the mock server."""
        return f"http://{self.host}:{self.port}"

    def get_request_history(self) -> List[Dict[str, Any]]:
        """Get the request history.

        Returns:
            List[Dict[str, Any]]: The request history
        """
        return self.request_history

    def clear_request_history(self) -> None:
        """Clear the request history."""
        self.request_history = []

    def _register_cli_routes(self):
        """Register routes for the CLI API."""

        @self.app.route("/api/cli/status", methods=["GET"])
        def get_status():
            """Get the server status."""
            return jsonify(
                {
                    "status": "running" if self.is_running else "stopped",
                    "host": self.host,
                    "port": self.port,
                    "validation_enabled": self.validate_requests,
                    "request_count": len(self.request_history),
                }
            )

        @self.app.route("/api/cli/history", methods=["GET"])
        def get_history():
            """Get the request history."""
            return jsonify(
                {
                    "history": self.request_history,
                }
            )

        @self.app.route("/api/cli/history", methods=["DELETE"])
        def clear_history():
            """Clear the request history."""
            self.clear_request_history()
            return jsonify(
                {
                    "status": "success",
                    "message": "Request history cleared",
                }
            )

        @self.app.route("/api/cli/validation", methods=["GET"])
        def get_validation():
            """Get the validation status."""
            return jsonify(
                {
                    "validation_enabled": self.validate_requests,
                }
            )

        @self.app.route("/api/cli/validation", methods=["POST"])
        def set_validation():
            """Set the validation status."""
            data = request.json
            if data and "enabled" in data:
                self.validate_requests = data["enabled"]
                return jsonify(
                    {
                        "status": "success",
                        "message": f"Validation {'enabled' if self.validate_requests else 'disabled'}",
                        "validation_enabled": self.validate_requests,
                    }
                )
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing 'enabled' parameter",
                    }
                ),
                400,
            )

        @self.app.route("/api/cli/shutdown", methods=["POST"])
        def shutdown_server():
            """Shutdown the server."""
            self.shutdown()
            return jsonify(
                {
                    "status": "success",
                    "message": "Server shutting down",
                }
            )

    def _register_convenience_method_routes(self):
        """Register additional routes needed for convenience methods."""

        # OAuth 2.0 authorization endpoint (simulates auth.fogis.se)
        @self.app.route("/oauth/authorize", methods=["GET"])
        def oauth_authorize():
            """Show OAuth authorization login form."""
            # Extract OAuth parameters from query string
            client_id = request.args.get("client_id")
            redirect_uri = request.args.get("redirect_uri")
            state = request.args.get("state")
            nonce = request.args.get("nonce")
            code_challenge = request.args.get("code_challenge")

            # Store OAuth parameters in session for later use
            session["oauth_client_id"] = client_id
            session["oauth_redirect_uri"] = redirect_uri
            session["oauth_state"] = state
            session["oauth_nonce"] = nonce
            session["oauth_code_challenge"] = code_challenge

            # Return OAuth login form (simulates auth.fogis.se login page)
            return f"""
            <html>
            <head><title>FOGIS OAuth Login</title></head>
            <body>
                <h1>FOGIS OAuth Login</h1>
                <form method="post" action="/oauth/login">
                    <input type="hidden" name="client_id" value="{client_id or ''}" />
                    <input type="hidden" name="redirect_uri" value="{redirect_uri or ''}" />
                    <input type="hidden" name="state" value="{state or ''}" />
                    <input type="hidden" name="nonce" value="{nonce or ''}" />
                    <input type="hidden" name="code_challenge" value="{code_challenge or ''}" />
                    <label>Username: <input type="text" name="Username" /></label><br/>
                    <label>Password: <input type="password" name="Password" /></label><br/>
                    <input type="checkbox" name="RememberMe" value="false" /> Remember Me<br/>
                    <input type="submit" value="Login" />
                </form>
            </body>
            </html>
            """

        # OAuth login form submission endpoint
        @self.app.route("/oauth/login", methods=["POST"])
        def oauth_login():
            """Handle OAuth login form submission."""
            username = request.form.get("Username")
            password = request.form.get("Password")
            redirect_uri = request.form.get("redirect_uri") or session.get("oauth_redirect_uri")
            state = request.form.get("state") or session.get("oauth_state")

            # Validate credentials
            if username in self.users and self.users[username] == password:
                # Generate authorization code
                import secrets

                auth_code = f"mock_auth_code_{secrets.token_urlsafe(16)}"

                # Store the authorization code with username
                self.oauth_codes[auth_code] = username

                # Store username in session for hybrid auth
                session["authenticated"] = True
                session["username"] = username

                # Redirect back to FOGIS with authorization code
                # This simulates the OAuth callback redirect
                callback_url = f"{redirect_uri}?code={auth_code}&state={state}"
                return redirect(callback_url, code=302)
            else:
                # Login failed
                return (
                    """
                <html>
                <head><title>FOGIS OAuth Login Failed</title></head>
                <body>
                    <h1>Login Failed</h1>
                    <p>Invalid username or password</p>
                    <a href="/oauth/authorize">Try again</a>
                </body>
                </html>
                """,
                    401,
                )

        # OAuth callback endpoint (simulates fogis.svenskfotboll.se/mdk/signin-oidc)
        @self.app.route("/mdk/signin-oidc", methods=["GET"])
        def oauth_callback():
            """Receive authorization code and set session cookies."""
            code = request.args.get("code")
            # state parameter is received but not validated in mock
            # request.args.get("state")

            # Verify the authorization code exists
            if code not in self.oauth_codes:
                return "Invalid authorization code", 400

            # Get username from authorization code
            username = self.oauth_codes[code]

            # Set ASP.NET session cookies (hybrid OAuth + ASP.NET approach)
            # This matches the real FOGIS behavior
            resp = Response("OAuth authentication successful", status=302)
            resp.set_cookie("FogisMobilDomarKlient.ASPXAUTH", f"mock_oauth_cookie_{code[:16]}")
            resp.set_cookie("ASP.NET_SessionId", f"mock_session_{code[:16]}")
            resp.headers["Location"] = session.get("oauth_return_url", "/mdk/")

            # Mark session as authenticated
            session["authenticated"] = True
            session["username"] = username

            return resp

        # OAuth token exchange endpoint
        @self.app.route("/oauth/token", methods=["POST"])
        def oauth_token():
            """Exchange authorization code or refresh token for access tokens."""
            grant_type = request.form.get("grant_type")

            if grant_type == "authorization_code":
                # Exchange authorization code for tokens
                code = request.form.get("code")
                # code_verifier is received but not validated in mock
                # request.form.get("code_verifier")

                # Verify the authorization code exists
                if code not in self.oauth_codes:
                    return (
                        jsonify({"error": "invalid_grant", "error_description": "Invalid authorization code"}),
                        400,
                    )

                # Get username from authorization code
                username = self.oauth_codes[code]

                # Generate access and refresh tokens
                import secrets

                access_token = f"mock_access_token_{secrets.token_urlsafe(32)}"
                refresh_token = f"mock_refresh_token_{secrets.token_urlsafe(32)}"

                # Store the access token with username
                self.oauth_tokens[access_token] = username

                # Return tokens
                return jsonify(
                    {
                        "access_token": access_token,
                        "token_type": "Bearer",
                        "expires_in": 3600,
                        "refresh_token": refresh_token,
                        "scope": "openid fogis profile anvandare personid offline_access",
                    }
                )

            elif grant_type == "refresh_token":
                # Refresh access token
                refresh_token = request.form.get("refresh_token")

                # For mock purposes, just generate a new access token
                import secrets

                access_token = f"mock_access_token_{secrets.token_urlsafe(32)}"

                # Return new tokens
                return jsonify(
                    {
                        "access_token": access_token,
                        "token_type": "Bearer",
                        "expires_in": 3600,
                        "refresh_token": refresh_token,
                        "scope": "openid fogis profile anvandare personid offline_access",
                    }
                )

            else:
                return jsonify({"error": "unsupported_grant_type"}), 400


if __name__ == "__main__":
    # Run the mock server when executed directly
    server = MockFogisServer()
    server.run()
