"""
Authentication routes for the FOGIS API Gateway.

This module provides endpoints for credential management:
- /auth/login: Generate and return tokens based on credentials
- /auth/validate: Check if a token is valid
- /auth/refresh: Refresh an existing token (not implemented yet)
- /auth/logout: Revoke a token
"""

import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Union

from flask import Blueprint, current_app, jsonify, request

from fogis_api_client.fogis_api_client import FogisApiClient, FogisLoginError

# Configure logging
logger = logging.getLogger(__name__)

# Create a Blueprint for authentication routes
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def get_client_from_app() -> Optional[FogisApiClient]:
    """
    Get the FogisApiClient instance from the Flask app.

    Returns:
        Optional[FogisApiClient]: The client instance or None if not available
    """
    return current_app.config.get("FOGIS_CLIENT")


def require_json(f: Callable) -> Callable:
    """
    Decorator to require JSON content type for requests.

    Args:
        f: The function to decorate

    Returns:
        Callable: The decorated function
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 415
        return f(*args, **kwargs)

    return decorated_function


@auth_bp.route("/login", methods=["POST"])
@require_json
def login() -> Union[Dict[str, Any], Tuple[Dict[str, Any], int]]:
    """
    Login endpoint to authenticate with FOGIS and get session cookies.

    Request body:
        {
            "username": "your_username",
            "password": "your_password"
        }

    Returns:
        JSON response with authentication status and cookies if successful
    """
    data = request.json

    # Validate request data
    if not data or "username" not in data or "password" not in data:
        return (
            jsonify({"success": False, "error": "Missing required fields: username and password"}),
            400,
        )

    username = data["username"]
    password = data["password"]

    try:
        # Create a new client instance with the provided credentials
        client = FogisApiClient(username=username, password=password)

        # Perform login
        cookies = client.login()

        if not cookies:
            return jsonify({"success": False, "error": "Login failed: No cookies returned"}), 401

        # Return the cookies as the authentication token
        return jsonify({"success": True, "message": "Login successful", "token": cookies})

    except FogisLoginError as e:
        logger.error(f"Login failed: {e}")
        return jsonify({"success": False, "error": f"Login failed: {str(e)}"}), 401

    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500


@auth_bp.route("/validate", methods=["POST"])
@require_json
def validate() -> Union[Dict[str, Any], Tuple[Dict[str, Any], int]]:
    """
    Validate endpoint to check if a token (cookies) is still valid.

    Request body:
        {
            "token": {
                "cookie_name1": "cookie_value1",
                "cookie_name2": "cookie_value2",
                ...
            }
        }

    Returns:
        JSON response with validation status
    """
    data = request.json

    # Validate request data
    if not data or "token" not in data:
        return jsonify({"success": False, "error": "Missing required field: token"}), 400

    token = data["token"]

    try:
        # Create a new client instance with the provided token (cookies)
        client = FogisApiClient(cookies=token)

        # Validate the cookies
        is_valid = client.validate_cookies()

        if is_valid:
            return jsonify({"success": True, "valid": True, "message": "Token is valid"})
        else:
            return jsonify({"success": True, "valid": False, "message": "Token is invalid or expired"})

    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500


@auth_bp.route("/logout", methods=["POST"])
@require_json
def logout() -> Union[Dict[str, Any], Tuple[Dict[str, Any], int]]:
    """
    Logout endpoint to invalidate a token (cookies).

    This is a client-side operation as the FOGIS API doesn't provide a logout endpoint.
    The client should discard the token after calling this endpoint.

    Request body:
        {
            "token": {
                "cookie_name1": "cookie_value1",
                "cookie_name2": "cookie_value2",
                ...
            }
        }

    Returns:
        JSON response with logout status
    """
    data = request.json

    # Validate request data
    if not data or "token" not in data:
        return jsonify({"success": False, "error": "Missing required field: token"}), 400

    # No server-side action is needed as the token should be discarded by the client
    return jsonify(
        {
            "success": True,
            "message": "Logout successful. Please discard the token on the client side.",
        }
    )


@auth_bp.route("/refresh", methods=["POST"])
@require_json
def refresh() -> Union[Dict[str, Any], Tuple[Dict[str, Any], int]]:
    """
    Refresh endpoint to get a new token (cookies) using an existing token.

    This is not fully implemented yet as the FOGIS API doesn't provide a refresh mechanism.
    For now, it just validates the token and returns it if it's still valid.

    Request body:
        {
            "token": {
                "cookie_name1": "cookie_value1",
                "cookie_name2": "cookie_value2",
                ...
            }
        }

    Returns:
        JSON response with refresh status and new token if successful
    """
    data = request.json

    # Validate request data
    if not data or "token" not in data:
        return jsonify({"success": False, "error": "Missing required field: token"}), 400

    token = data["token"]

    try:
        # Create a new client instance with the provided token (cookies)
        client = FogisApiClient(cookies=token)

        # Validate the cookies
        is_valid = client.validate_cookies()

        if is_valid:
            # For now, just return the same token as it's still valid
            # In the future, we could implement a proper refresh mechanism
            return jsonify({"success": True, "message": "Token is still valid", "token": token})
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Token is invalid or expired. Please login again.",
                        "valid": False,
                    }
                ),
                401,
            )

    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500


def register_auth_routes(app):
    """
    Register the authentication routes with the Flask app.

    Args:
        app: The Flask application instance
    """
    app.register_blueprint(auth_bp)
    logger.info("Registered authentication routes")
