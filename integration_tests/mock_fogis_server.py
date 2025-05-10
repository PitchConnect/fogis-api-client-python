"""
Mock FOGIS API Server for integration testing.

This module provides a Flask-based mock server that simulates the FOGIS API endpoints
for integration testing without requiring real credentials or internet access.
"""

import json
import logging
import random
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional, Union

from flask import Flask, Response, jsonify, request, session

# Import data factory for the mock server
from integration_tests.sample_data_factory import MockDataFactory
# Import request validator
from integration_tests.request_validator import RequestValidator, RequestValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockFogisServer:
    """
    A Flask-based mock server that simulates the FOGIS API endpoints.
    """

    def __init__(self, host: str = "localhost", port: int = 5001):
        """
        Initialize the mock server.

        Args:
            host: The host to run the server on
            port: The port to run the server on
        """
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.app.secret_key = "mock_fogis_server_secret_key"

        # Store registered users
        self.users = {
            "test_user": "test_password",
        }

        # Store session data
        self.sessions: Dict[str, Dict] = {}

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

        # Register routes
        self._register_routes()

        # Register before_request handler to track all requests
        @self.app.before_request
        def track_request():
            """Track all requests to the server."""
            self._track_request(request.path)

    def _register_routes(self):
        """Register the API routes."""

        # Login route
        @self.app.route("/mdk/Login.aspx", methods=["GET", "POST"])
        def login():
            if request.method == "POST":
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
            else:
                # Return a mock login page with form fields
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
            filter_params = data.get("filter", {})

            # Generate a fresh match list using the factory
            match_list = MockDataFactory.generate_match_list()

            # Extract the match list from the response and format it for the new API
            # The match_list["d"] is already a JSON string, so we need to parse it
            matches_data = json.loads(match_list["d"]) if isinstance(match_list["d"], str) else match_list["d"]

            # Create a response in the format expected by the client
            # The client expects a response with a matchlista field
            response_data = {
                "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatcherAttRapportera",
                "anvandare": None,
                "anvandareforeningid": 0,
                "anvandartyp": "Domare",
                "matchlista": matches_data["matchlista"],  # This is what the client expects
                "success": True
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

            # Generate match details using the factory
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
            officials_data = MockDataFactory.generate_match_officials(match_id)

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
            match_id = data.get("matchid")

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
                        "matchlagid": 12345
                    }
                ],
                "bortalag": [
                    {
                        "personid": 22222,
                        "fornamn": "Jane",
                        "efternamn": "Smith",
                        "roll": "Assisterande tränare",
                        "rollid": 2,
                        "matchlagid": 67890
                    }
                ]
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
            event_id = data.get("matchhandelseid")

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
            return jsonify({
                "history": self.request_history,
                "count": len(self.request_history),
            })

        # Clear request history endpoint (for debugging and testing)
        @self.app.route("/clear-request-history", methods=["POST"])
        def clear_request_history():
            self.clear_request_history()
            return jsonify({"success": True, "message": "Request history cleared"})

    def _check_auth(self):
        """Check if the request is authenticated."""
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
            func = request.environ.get('werkzeug.server.shutdown')
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
            return jsonify({
                "status": "running" if self.is_running else "stopped",
                "host": self.host,
                "port": self.port,
                "validation_enabled": self.validate_requests,
                "request_count": len(self.request_history),
            })

        @self.app.route("/api/cli/history", methods=["GET"])
        def get_history():
            """Get the request history."""
            return jsonify({
                "history": self.request_history,
            })

        @self.app.route("/api/cli/history", methods=["DELETE"])
        def clear_history():
            """Clear the request history."""
            self.clear_request_history()
            return jsonify({
                "status": "success",
                "message": "Request history cleared",
            })

        @self.app.route("/api/cli/validation", methods=["GET"])
        def get_validation():
            """Get the validation status."""
            return jsonify({
                "validation_enabled": self.validate_requests,
            })

        @self.app.route("/api/cli/validation", methods=["POST"])
        def set_validation():
            """Set the validation status."""
            data = request.json
            if data and "enabled" in data:
                self.validate_requests = data["enabled"]
                return jsonify({
                    "status": "success",
                    "message": f"Validation {'enabled' if self.validate_requests else 'disabled'}",
                    "validation_enabled": self.validate_requests,
                })
            return jsonify({
                "status": "error",
                "message": "Missing 'enabled' parameter",
            }), 400

        @self.app.route("/api/cli/shutdown", methods=["POST"])
        def shutdown_server():
            """Shutdown the server."""
            self.shutdown()
            return jsonify({
                "status": "success",
                "message": "Server shutting down",
            })


if __name__ == "__main__":
    # Run the mock server when executed directly
    server = MockFogisServer()
    server.run()
