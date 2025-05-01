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


def authenticate(session: requests.Session, username: str, password: str, base_url: str) -> InternalCookieDict:
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
    login_url = f"{base_url}/Login.aspx?ReturnUrl=%2fmdk%2f"
    logger.debug(f"Authenticating with {login_url}")

    # Get the login page to extract the request verification token
    response = session.get(login_url)
    response.raise_for_status()

    # Parse the HTML to extract the form tokens
    soup = BeautifulSoup(response.text, "html.parser")
    viewstate_input = soup.find("input", {"name": "__VIEWSTATE"})
    if not viewstate_input or not viewstate_input.get("value"):
        logger.error("Failed to extract VIEWSTATE token from login page")
        raise ValueError("Failed to extract VIEWSTATE token from login page")

    token = viewstate_input["value"]

    # Prepare the login payload
    login_payload = {
        "__VIEWSTATE": token,
        "__EVENTVALIDATION": token,  # Using the same token for simplicity
        "ctl00$MainContent$UserName": username,
        "ctl00$MainContent$Password": password,
        "ctl00$MainContent$LoginButton": "Logga in",
    }

    # Submit the login form
    response = session.post(login_url, data=login_payload, allow_redirects=True)
    response.raise_for_status()

    # Check if login was successful
    if "FogisMobilDomarKlient.ASPXAUTH" not in session.cookies:
        logger.error("Authentication failed: Invalid credentials")
        raise ValueError("Authentication failed: Invalid credentials")

    # Extract the cookies
    cookies = cast(
        InternalCookieDict,
        {
            "FogisMobilDomarKlient.ASPXAUTH": session.cookies.get("FogisMobilDomarKlient.ASPXAUTH"),
            "ASP.NET_SessionId": session.cookies.get("ASP.NET_SessionId"),
        },
    )

    logger.debug("Authentication successful")
    return cookies
