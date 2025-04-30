"""
Authentication module for the FOGIS API client.

This module handles authentication with the FOGIS API server.
"""
import logging
import re
from typing import Dict, Optional, Tuple, cast

import requests
from bs4 import BeautifulSoup

from fogis_api_client.internal.types import InternalCookieDict

logger = logging.getLogger(__name__)


def authenticate(
    session: requests.Session, username: str, password: str, base_url: str
) -> InternalCookieDict:
    """
    Authenticate with the FOGIS API server.

    Args:
        session: The requests session to use for authentication
        username: The username to authenticate with
        password: The password to authenticate with
        base_url: The base URL of the FOGIS API server

    Returns:
        InternalCookieDict: The session cookies for authentication

    Raises:
        requests.exceptions.RequestException: If the authentication request fails
        ValueError: If the authentication fails due to invalid credentials
    """
    login_url = f"{base_url}/Account/Login"
    logger.debug(f"Authenticating with {login_url}")

    # Get the login page to extract the request verification token
    response = session.get(login_url)
    response.raise_for_status()

    # Parse the HTML to extract the request verification token
    soup = BeautifulSoup(response.text, "html.parser")
    token_input = soup.find("input", {"name": "__RequestVerificationToken"})
    if not token_input or not token_input.get("value"):
        logger.error("Failed to extract request verification token from login page")
        raise ValueError("Failed to extract request verification token from login page")

    token = token_input["value"]

    # Prepare the login payload
    login_payload = {
        "__RequestVerificationToken": token,
        "UserName": username,
        "Password": password,
    }

    # Submit the login form
    response = session.post(login_url, data=login_payload, allow_redirects=True)
    response.raise_for_status()

    # Check if login was successful
    if "FogisMobilDomarKlient_ASPXAUTH" not in session.cookies:
        logger.error("Authentication failed: Invalid credentials")
        raise ValueError("Authentication failed: Invalid credentials")

    # Extract the cookies
    cookies = cast(
        InternalCookieDict,
        {
            "FogisMobilDomarKlient_ASPXAUTH": session.cookies.get(
                "FogisMobilDomarKlient_ASPXAUTH"
            ),
            "ASP_NET_SessionId": session.cookies.get("ASP_NET_SessionId"),
        },
    )

    logger.debug("Authentication successful")
    return cookies
