import os
import signal
import sys
from flask import Flask, jsonify, request

try:
    from flask_cors import CORS  # Import CORS for development
except ImportError:
    # CORS is optional, only needed for development
    CORS = None

from fogis_api_client.fogis_api_client import FogisApiClient
from fogis_api_client.match_list_filter import MatchListFilter

# Get environment variables
fogis_username = os.environ.get("FOGIS_USERNAME", "test_user")
fogis_password = os.environ.get("FOGIS_PASSWORD", "test_pass")
debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"

# Initialize the Fogis API client but don't login yet
# Login will happen automatically when needed (lazy login)
client = FogisApiClient(fogis_username, fogis_password)

# Initialize the Flask app
app = Flask(__name__)
if CORS:
    CORS(app)  # Enable CORS for all routes if available


@app.route("/")
def index():
    """
    Test endpoint to verify the API is running.
    """
    return jsonify({"status": "ok", "message": "Fogis API Client HTTP Wrapper"})


@app.route("/hello")
def hello():
    """
    Test endpoint that calls the hello_world method of the Fogis API Client.
    """
    return jsonify({"message": client.hello_world()})


@app.route("/matches")
def matches():
    """
    Endpoint to fetch matches list from Fogis API Client.

    Query Parameters:
    - from_date (str): Start date for filtering matches (format: YYYY-MM-DD)
    - to_date (str): End date for filtering matches (format: YYYY-MM-DD)
    - limit (int): Maximum number of matches to return (default: all)
    - offset (int): Number of matches to skip (for pagination, default: 0)
    - sort_by (str): Field to sort by (default: date)
    - order (str): Sort order, 'asc' or 'desc' (default: asc)
    """
    try:
        # Parse query parameters
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        limit = request.args.get('limit')
        offset = request.args.get('offset', 0, type=int)
        sort_by = request.args.get('sort_by', 'datum')
        order = request.args.get('order', 'asc')

        # Create filter for server-side filtering
        filter_data = {}
        if from_date:
            filter_data['datumFran'] = from_date
        if to_date:
            filter_data['datumTill'] = to_date

        # Fetch matches with server-side filtering
        matches_list = client.fetch_matches_list_json(filter=filter_data)

        # Apply client-side sorting
        if sort_by and sort_by in ['datum', 'hemmalag', 'bortalag', 'tavling']:
            reverse = order.lower() == 'desc'
            matches_list = sorted(
                matches_list,
                key=lambda x: x.get(sort_by, ''),
                reverse=reverse
            )

        # Apply client-side pagination
        if limit:
            try:
                limit = int(limit)
                matches_list = matches_list[offset:offset+limit]
            except ValueError:
                pass  # Ignore invalid limit values
        elif offset > 0:
            matches_list = matches_list[offset:]

        return jsonify(matches_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/match/<match_id>")
def match(match_id):
    """
    Endpoint to fetch match details from Fogis API Client.

    Query Parameters:
    - include_events (bool): Whether to include events in the response (default: true)
    - include_players (bool): Whether to include players in the response (default: false)
    - include_officials (bool): Whether to include officials in the response (default: false)
    """
    try:
        # Parse query parameters
        include_events = request.args.get('include_events', 'true').lower() == 'true'
        include_players = request.args.get('include_players', 'false').lower() == 'true'
        include_officials = request.args.get('include_officials', 'false').lower() == 'true'

        # Fetch basic match data
        match_data = client.fetch_match_json(match_id)

        # Fetch additional data based on query parameters
        if include_players:
            try:
                players_data = client.fetch_match_players_json(match_id)
                match_data['players'] = players_data
            except Exception as e:
                # Don't fail the whole request if just this part fails
                match_data['players'] = {'error': str(e)}

        if include_officials:
            try:
                officials_data = client.fetch_match_officials_json(match_id)
                match_data['officials'] = officials_data
            except Exception as e:
                # Don't fail the whole request if just this part fails
                match_data['officials'] = {'error': str(e)}

        # If include_events is false, remove events from the response
        if not include_events and 'events' in match_data:
            del match_data['events']

        return jsonify(match_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/match/<match_id>/result")
def match_result(match_id):
    """
    Endpoint to fetch result information for a specific match.
    """
    try:
        result_data = client.fetch_match_result_json(match_id)
        return jsonify(result_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/match/<match_id>/events", methods=["GET"])
def match_events(match_id):
    """
    Endpoint to fetch events for a specific match.

    Query Parameters:
    - type (str): Filter events by type (e.g., 'goal', 'card', 'substitution')
    - player (str): Filter events by player name
    - team (str): Filter events by team name
    - limit (int): Maximum number of events to return (default: all)
    - offset (int): Number of events to skip (for pagination, default: 0)
    - sort_by (str): Field to sort by (default: time)
    - order (str): Sort order, 'asc' or 'desc' (default: asc)
    """
    try:
        # Parse query parameters
        event_type = request.args.get('type')
        player = request.args.get('player')
        team = request.args.get('team')
        limit = request.args.get('limit')
        offset = request.args.get('offset', 0, type=int)
        sort_by = request.args.get('sort_by', 'time')
        order = request.args.get('order', 'asc')

        # Use the dedicated method for fetching match events
        events_data = client.fetch_match_events_json(match_id)

        # Apply client-side filtering
        if event_type:
            events_data = [e for e in events_data if e.get('type', '').lower() == event_type.lower()]
        if player:
            events_data = [e for e in events_data if player.lower() in e.get('player', '').lower()]
        if team:
            events_data = [e for e in events_data if team.lower() in e.get('team', '').lower()]

        # Apply client-side sorting
        if sort_by and sort_by in ['time', 'type', 'player', 'team']:
            reverse = order.lower() == 'desc'
            events_data = sorted(
                events_data,
                key=lambda x: x.get(sort_by, ''),
                reverse=reverse
            )

        # Apply client-side pagination
        if limit:
            try:
                limit = int(limit)
                events_data = events_data[offset:offset+limit]
            except ValueError:
                pass  # Ignore invalid limit values
        elif offset > 0:
            events_data = events_data[offset:]

        return jsonify(events_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/match/<match_id>/events", methods=["POST"])
def report_match_event(match_id):
    """
    Endpoint to report a new event for a match.
    """
    # Check if JSON data was provided
    if not request.is_json or not request.json:
        return jsonify({"error": "No event data provided"}), 400

    try:
        event_data = request.json

        # Add match_id to the event data if not already present
        if "matchid" not in event_data:
            event_data["matchid"] = match_id

        result = client.report_match_event(event_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/match/<match_id>/events/clear", methods=["POST"])
def clear_match_events(match_id):
    """
    Endpoint to clear all events for a match.
    """
    try:
        result = client.clear_match_events(match_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/match/<match_id>/officials")
def match_officials(match_id):
    """
    Endpoint to fetch officials information for a specific match.
    """
    try:
        officials_data = client.fetch_match_officials_json(match_id)
        return jsonify(officials_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/team/<team_id>/players")
def team_players(team_id):
    """
    Endpoint to fetch player information for a specific team.

    Query Parameters:
    - name (str): Filter players by name
    - position (str): Filter players by position
    - number (str): Filter players by jersey number
    - limit (int): Maximum number of players to return (default: all)
    - offset (int): Number of players to skip (for pagination, default: 0)
    - sort_by (str): Field to sort by (default: name)
    - order (str): Sort order, 'asc' or 'desc' (default: asc)
    """
    try:
        # Parse query parameters
        name = request.args.get('name')
        position = request.args.get('position')
        number = request.args.get('number')
        limit = request.args.get('limit')
        offset = request.args.get('offset', 0, type=int)
        sort_by = request.args.get('sort_by', 'name')
        order = request.args.get('order', 'asc')

        # Fetch players data
        players_data = client.fetch_team_players_json(team_id)

        # Apply client-side filtering
        if name:
            players_data = [p for p in players_data if name.lower() in p.get('name', '').lower()]
        if position:
            players_data = [p for p in players_data if position.lower() in p.get('position', '').lower()]
        if number:
            players_data = [p for p in players_data if p.get('number') == number]

        # Apply client-side sorting
        if sort_by and sort_by in ['name', 'position', 'number']:
            reverse = order.lower() == 'desc'
            players_data = sorted(
                players_data,
                key=lambda x: x.get(sort_by, ''),
                reverse=reverse
            )

        # Apply client-side pagination
        if limit:
            try:
                limit = int(limit)
                players_data = players_data[offset:offset+limit]
            except ValueError:
                pass  # Ignore invalid limit values
        elif offset > 0:
            players_data = players_data[offset:]

        return jsonify(players_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/team/<team_id>/officials")
def team_officials(team_id):
    """
    Endpoint to fetch officials information for a specific team.

    Query Parameters:
    - name (str): Filter officials by name
    - role (str): Filter officials by role
    - limit (int): Maximum number of officials to return (default: all)
    - offset (int): Number of officials to skip (for pagination, default: 0)
    - sort_by (str): Field to sort by (default: name)
    - order (str): Sort order, 'asc' or 'desc' (default: asc)
    """
    try:
        # Parse query parameters
        name = request.args.get('name')
        role = request.args.get('role')
        limit = request.args.get('limit')
        offset = request.args.get('offset', 0, type=int)
        sort_by = request.args.get('sort_by', 'name')
        order = request.args.get('order', 'asc')

        # Fetch officials data
        officials_data = client.fetch_team_officials_json(team_id)

        # Apply client-side filtering
        if name:
            officials_data = [o for o in officials_data if name.lower() in o.get('name', '').lower()]
        if role:
            officials_data = [o for o in officials_data if role.lower() in o.get('role', '').lower()]

        # Apply client-side sorting
        if sort_by and sort_by in ['name', 'role']:
            reverse = order.lower() == 'desc'
            officials_data = sorted(
                officials_data,
                key=lambda x: x.get(sort_by, ''),
                reverse=reverse
            )

        # Apply client-side pagination
        if limit:
            try:
                limit = int(limit)
                officials_data = officials_data[offset:offset+limit]
            except ValueError:
                pass  # Ignore invalid limit values
        elif offset > 0:
            officials_data = officials_data[offset:]

        return jsonify(officials_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/match/<match_id>/finish", methods=["POST"])
def finish_match_report(match_id):
    """
    Endpoint to mark a match report as completed/finished.
    """
    try:
        result = client.mark_reporting_finished(match_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/matches/filter", methods=["POST"])
def filtered_matches():
    """
    Endpoint to fetch matches with specific filters.
    """
    try:
        filter_data = request.json or {}

        # Create a MatchListFilter with the provided filter data
        match_filter = MatchListFilter()

        # Apply filter parameters if they exist
        if "from_date" in filter_data:
            match_filter.from_date = filter_data["from_date"]
        if "to_date" in filter_data:
            match_filter.to_date = filter_data["to_date"]
        if "status" in filter_data:
            match_filter.status = filter_data["status"]
        if "age_category" in filter_data:
            match_filter.age_category = filter_data["age_category"]
        if "gender" in filter_data:
            match_filter.gender = filter_data["gender"]
        if "football_type" in filter_data:
            match_filter.football_type = filter_data["football_type"]

        # Fetch filtered matches
        matches_list = match_filter.fetch_filtered_matches(client)
        return jsonify(matches_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def signal_handler(sig, frame):
    """
    Handle SIGTERM and SIGINT signals to gracefully shut down the server.
    """
    print("Shutting down...")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Start the Flask app
    app.run(host="0.0.0.0", port=8080, debug=debug_mode)
