import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Optional

from flask import Flask, jsonify, request

try:
    from flask_cors import CORS  # Import CORS for development
except ImportError:
    # CORS is optional, only needed for development
    CORS = None

from auth_routes import register_auth_routes
from fogis_api_client.fogis_api_client import FogisApiClient
from fogis_api_client.match_list_filter import MatchListFilter
from fogis_api_client_swagger import get_swagger_blueprint, spec

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Get environment variables
fogis_username = os.environ.get("FOGIS_USERNAME", "test_user")
fogis_password = os.environ.get("FOGIS_PASSWORD", "test_pass")
debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"

# Initialize the Fogis API client but don't login yet
# Login will happen automatically when needed (lazy login)
client: Optional[FogisApiClient] = None
client_initialized = False

try:
    client = FogisApiClient(fogis_username, fogis_password)
    client_initialized = True
except Exception as e:
    logger.error(f"Failed to initialize FogisApiClient: {e}")
    client_initialized = False

# Log startup information
logger.info("Starting FOGIS API Gateway...")
logger.info(f"FOGIS_USERNAME: {fogis_username}")
logger.info(f"Debug mode: {debug_mode}")
logger.info(f"Python version: {sys.version}")

# Initialize the Flask app
app = Flask(__name__)
if CORS:
    CORS(app)  # Enable CORS for all routes if available

# Register Swagger UI blueprint
swagger_ui_blueprint, SWAGGER_URL, API_URL = get_swagger_blueprint()
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

# Register authentication routes
register_auth_routes(app)


# Add endpoint to serve the OpenAPI specification
@app.route("/api/swagger.json")
def get_swagger():
    return jsonify(spec.to_dict())


@app.route("/")
def index():
    """
    Test endpoint to verify the API is running.
    """
    logger.info(f"Root endpoint requested from {request.remote_addr}")
    return jsonify({"status": "ok", "message": "FOGIS API Gateway"})


@app.route("/debug")
def debug():
    """
    Debug endpoint to help diagnose health check issues.
    This endpoint provides detailed information about the service and its environment.
    """
    import os
    import platform
    import socket
    import sys

    import psutil

    # Log request details
    logger.info(f"Debug endpoint requested from {request.remote_addr}")

    # Get network information
    hostname = socket.gethostname()
    ip_addresses = {}
    try:
        # Get all network interfaces
        for interface, addrs in psutil.net_if_addrs().items():
            ip_addresses[interface] = [addr.address for addr in addrs if addr.family == socket.AF_INET]
    except Exception as net_err:
        ip_addresses = {"error": str(net_err)}

    # Get environment variables (excluding sensitive ones)
    env_vars = {}
    for key, value in os.environ.items():
        if "password" not in key.lower() and "secret" not in key.lower() and "key" not in key.lower():
            env_vars[key] = value

    # Get Docker-specific information
    docker_info = {}
    try:
        # Check if running in Docker
        in_docker = os.path.exists("/.dockerenv")
        docker_info["in_docker"] = in_docker

        # Get container ID if in Docker
        if in_docker:
            try:
                with open("/proc/self/cgroup", "r") as f:
                    docker_info["container_id"] = f.read()
            except Exception as e:
                docker_info["container_id_error"] = str(e)
    except Exception as docker_err:
        docker_info["error"] = str(docker_err)

    # Build debug response
    debug_data = {
        "timestamp": datetime.now().isoformat(),
        "service": "fogis-api-client",
        "client_initialized": client_initialized,
        "network": {
            "hostname": hostname,
            "ip_addresses": ip_addresses,
            "request_remote_addr": request.remote_addr,
            "request_host": request.host,
        },
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory": dict(psutil.virtual_memory()._asdict()),
        },
        "process": {
            "pid": os.getpid(),
            "cwd": os.getcwd(),
            "memory_usage_mb": psutil.Process().memory_info().rss / (1024 * 1024),
        },
        "docker": docker_info,
        "environment": env_vars,
        "python_path": sys.path,
    }

    # Log the response
    logger.info("Debug endpoint response generated")

    return jsonify(debug_data)


@app.route("/health")
def health():
    """
    Optimized health check endpoint with minimal logging.
    This endpoint provides essential health information with reduced log verbosity.
    """
    start_time = time.time()

    try:
        # Get current timestamp
        current_time = datetime.now().isoformat()

        # Check if the client is initialized
        client_status = "available" if client_initialized else "unavailable"

        # Build minimal health response
        health_data = {
            "status": "healthy" if client_initialized else "degraded",
            "timestamp": current_time,
            "service": "fogis-api-client",
            "version": "1.0.0",
            "dependencies": {
                "fogis_client": client_status,
            },
        }

        # Single optimized log entry
        duration = time.time() - start_time
        logger.info(f"✅ Health check OK ({duration:.3f}s)")

        return jsonify(health_data)
    except Exception as e:
        # Single optimized error log entry
        duration = time.time() - start_time
        logger.error(f"❌ Health check FAILED ({duration:.3f}s): {str(e)}")

        # Return a simple response with the error
        return jsonify(
            {
                "status": "warning",
                "message": "Health check encountered an error but service is still responding",
                "timestamp": time.time(),
                "error": str(e),
            }
        )


@app.route("/matches")
def matches():
    """
    Endpoint to fetch matches list from Fogis API Client.
    """
    try:
        matches_list = client.fetch_matches_list_json()
        return jsonify(matches_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/match/<match_id>")
def match(match_id):
    """
    Endpoint to fetch match details from Fogis API Client.
    """
    try:
        match_data = client.fetch_match_json(int(match_id))
        return jsonify(match_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/match/<match_id>/result")
def match_result(match_id):
    """
    Endpoint to fetch result information for a specific match.
    """
    try:
        result_data = client.fetch_match_result_json(int(match_id))
        return jsonify(result_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/match/<match_id>/events", methods=["GET"])
def match_events(match_id):
    """
    Endpoint to fetch events for a specific match.
    """
    try:
        # Use the dedicated method for fetching match events
        events_data = client.fetch_match_events_json(int(match_id))
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
            event_data["matchid"] = int(match_id)

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
        result = client.clear_match_events(int(match_id))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/match/<match_id>/officials")
def match_officials(match_id):
    """
    Endpoint to fetch officials information for a specific match.
    """
    try:
        officials_data = client.fetch_match_officials_json(int(match_id))
        return jsonify(officials_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/team/<team_id>/players")
def team_players(team_id):
    """
    Endpoint to fetch player information for a specific team.
    """
    try:
        players_data = client.fetch_team_players_json(int(team_id))
        return jsonify(players_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/team/<team_id>/officials")
def team_officials(team_id):
    """
    Endpoint to fetch officials information for a specific team.
    """
    try:
        officials_data = client.fetch_team_officials_json(int(team_id))
        return jsonify(officials_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/match/<match_id>/finish", methods=["POST"])
def finish_match_report(match_id):
    """
    Endpoint to mark a match report as completed/finished.
    """
    try:
        result = client.mark_reporting_finished(int(match_id))
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

    # Log that we're about to start the Flask app
    logger.info("Starting Flask app on 0.0.0.0:8080")
    logger.info(f"Debug mode: {debug_mode}")

    try:
        # Start the Flask app
        app.run(host="0.0.0.0", port=8080, debug=debug_mode)
    except Exception as e:
        logger.error(f"Error starting Flask app: {e}")
        raise
