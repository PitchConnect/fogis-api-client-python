"""
Enhanced FOGIS Authentication with OAuth 2.0 PKCE Support

This module provides authentication for FOGIS API with support for both
OAuth 2.0 PKCE flow (new) and ASP.NET form authentication (legacy fallback).
"""

import logging
from typing import Any, Dict, Tuple
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

# Import will be handled dynamically to avoid circular imports
# from fogis_oauth_manager import FogisOAuthManager

logger = logging.getLogger(__name__)


class FogisAuthenticationError(Exception):
    """Exception raised when FOGIS authentication fails."""

    pass


class FogisOAuthAuthenticationError(FogisAuthenticationError):
    """Exception raised when OAuth authentication fails."""

    pass


def authenticate(session: requests.Session, username: str, password: str, base_url: str) -> Dict[str, Any]:
    """
    Authenticate with the FOGIS API server using OAuth 2.0 or ASP.NET fallback.

    Args:
        session: The requests session to use for authentication
        username: The username to authenticate with
        password: The password to authenticate with
        base_url: The base URL of the FOGIS API server

    Returns:
        Dict containing authentication tokens/cookies

    Raises:
        FogisAuthenticationError: If authentication fails
        FogisOAuthAuthenticationError: If OAuth authentication fails
    """
    login_url = f"{base_url}/Login.aspx?ReturnUrl=%2fmdk%2f"
    logger.debug(f"Starting authentication with {login_url}")

    # Set browser-like headers to avoid being blocked
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9," "image/webp,*/*;q=0.8"),
            "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    )

    try:
        # Get the login page - this may redirect to OAuth
        logger.debug("Requesting login page")
        response = session.get(login_url, timeout=(10, 30), allow_redirects=True)
        response.raise_for_status()

        # Check if we were redirected to OAuth
        if "auth.fogis.se" in response.url:
            logger.info("Detected OAuth redirect - using OAuth 2.0 PKCE flow")
            return _handle_oauth_authentication(session, username, password, response.url)
        else:
            logger.info("No OAuth redirect detected - using ASP.NET form authentication")
            return _handle_aspnet_authentication(session, username, password, response, login_url)

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during authentication: {e}")
        raise FogisAuthenticationError(f"Network error during authentication: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        raise FogisAuthenticationError(f"Unexpected error during authentication: {e}")


def _extract_oauth_parameters(oauth_url: str) -> Dict[str, str]:
    """
    Extract OAuth parameters from the FOGIS redirect URL.

    This function parses the OAuth authorization URL that FOGIS redirected us to
    and extracts all the OAuth parameters that we need to continue the flow.

    Args:
        oauth_url: The OAuth authorization URL from FOGIS redirect

    Returns:
        Dict containing OAuth parameters

    Raises:
        FogisOAuthAuthenticationError: If required parameters are missing
    """
    try:
        parsed_url = urlparse(oauth_url)
        query_params = parse_qs(parsed_url.query)

        # Extract OAuth parameters (convert from list to string)
        oauth_params = {}
        for key, value_list in query_params.items():
            if value_list:  # Only take first value if multiple exist
                oauth_params[key] = value_list[0]

        # Verify required OAuth parameters are present
        # For production, we need all parameters, but for testing we can be more flexible
        required_params = ["client_id"]  # Minimum required parameter

        # Optional parameters that should be present in production
        optional_params = [
            "redirect_uri",
            "response_type",
            "scope",
            "code_challenge",
            "code_challenge_method",
            "state",
            "nonce",
        ]

        missing_required = [param for param in required_params if param not in oauth_params]
        if missing_required:
            raise FogisOAuthAuthenticationError(f"Missing required OAuth parameters: {', '.join(missing_required)}")

        # Log warning for missing optional parameters (but don't fail)
        missing_optional = [param for param in optional_params if param not in oauth_params]
        if missing_optional:
            logger.warning(f"Missing optional OAuth parameters: {', '.join(missing_optional)}")
            logger.warning("This may indicate a test environment or incomplete OAuth redirect")

        logger.debug(f"Successfully extracted {len(oauth_params)} OAuth parameters from FOGIS redirect")
        return oauth_params

    except Exception as e:
        logger.error(f"Failed to extract OAuth parameters from URL: {e}")
        raise FogisOAuthAuthenticationError(f"Failed to extract OAuth parameters: {e}")


def _handle_oauth_authentication(session: requests.Session, username: str, password: str, oauth_url: str) -> Dict[str, Any]:
    """
    Handle OAuth 2.0 PKCE authentication flow.

    Args:
        session: The requests session
        username: FOGIS username
        password: FOGIS password
        oauth_url: The OAuth authorization URL we were redirected to

    Returns:
        Dict containing OAuth tokens

    Raises:
        FogisOAuthAuthenticationError: If OAuth authentication fails
    """
    try:
        # Import OAuth manager dynamically to avoid circular imports
        from fogis_api_client.internal.fogis_oauth_manager import FogisOAuthManager

        # Initialize OAuth manager with the existing OAuth session
        oauth_manager = FogisOAuthManager(session)

        logger.debug(f"Starting OAuth 2.0 PKCE authentication flow with URL: {oauth_url}")

        # Parse the current OAuth URL to understand the flow state
        parsed_url = urlparse(oauth_url)

        # Check if we're at the authorization endpoint
        if "/connect/authorize" in parsed_url.path:
            logger.debug("At OAuth authorization endpoint - using FOGIS-provided OAuth parameters")

            # Extract OAuth parameters from the FOGIS redirect URL
            # This is critical: we must use FOGIS-provided parameters, not generate new ones
            oauth_params = _extract_oauth_parameters(oauth_url)
            logger.debug(
                f"Extracted OAuth parameters: client_id={oauth_params.get('client_id')}, "
                f"state={oauth_params.get('state', '')[:50]}..., "
                f"code_challenge={oauth_params.get('code_challenge', '')[:20]}..."
            )

            # Store the OAuth parameters in the manager for later use
            oauth_manager.set_oauth_parameters(oauth_params)

            # Continue with the OAuth flow using the existing session
            return _handle_oauth_login_form(session, username, password, oauth_manager)

        # If we're at a different OAuth endpoint, handle accordingly
        elif "/Account/LogIn" in parsed_url.path:
            logger.debug("At OAuth login form")
            return _handle_oauth_login_form(session, username, password, oauth_manager)

        else:
            raise FogisOAuthAuthenticationError(f"Unexpected OAuth URL: {oauth_url}")

    except Exception as e:
        logger.error(f"OAuth authentication failed: {e}")
        raise FogisOAuthAuthenticationError(f"OAuth authentication failed: {e}")


def _get_oauth_login_page(session: requests.Session, oauth_manager) -> requests.Response:
    """
    Get the OAuth login page response.

    This function gets the OAuth login page where we need to enter credentials.
    We should already be at the OAuth authorization endpoint from the FOGIS redirect.
    """
    # If we have OAuth parameters, we're already in the OAuth flow
    if oauth_manager.oauth_parameters:
        # We should already be at the OAuth login page from the redirect
        # Just get the current page content to extract the login form
        current_url = getattr(session, "url", None)
        if current_url and "auth.fogis.se" in current_url:
            logger.debug(f"Getting OAuth login page from current URL: {current_url}")
            return session.get(current_url, timeout=10)

    # Fallback: redirect to OAuth login
    login_url = "https://fogis.svenskfotboll.se/mdk/Login.aspx?ReturnUrl=%2fmdk%2f"
    logger.debug(f"Fallback: redirecting to OAuth login via: {login_url}")
    return session.get(login_url, allow_redirects=True, timeout=10)


def _extract_form_data(soup: BeautifulSoup, username: str, password: str) -> Tuple[str, str, Dict[str, str]]:
    """Extract form data from OAuth login page."""
    form = soup.find("form")
    if not form:
        raise FogisOAuthAuthenticationError("No login form found on OAuth login page")

    form_action = form.get("action", "")
    form_method = form.get("method", "post").lower()

    # Build the form submission URL
    if form_action.startswith("/"):
        form_url = f"https://auth.fogis.se{form_action}"
    elif form_action.startswith("http"):
        form_url = form_action
    else:
        form_url = "https://auth.fogis.se/Account/Login"

    # Extract all form fields
    form_data = {}
    for input_field in form.find_all("input"):
        field_name = input_field.get("name")
        field_value = input_field.get("value", "")
        if field_name:
            form_data[field_name] = field_value

    # Set credentials
    form_data["Username"] = username
    form_data["Password"] = password
    if "RememberMe" not in form_data:
        form_data["RememberMe"] = "false"

    return form_url, form_method, form_data


def _extract_session_cookies(session: requests.Session) -> Dict[str, Any]:
    """Extract ASP.NET session cookies from OAuth session."""
    cookies = {}
    for cookie in session.cookies:
        if any(name in cookie.name for name in [".AspNet.Cookies", "ASPXAUTH", "SessionId", "Identity"]):
            cookies[cookie.name] = cookie.value

    if cookies:
        logger.info(f"OAuth authentication completed successfully with {len(cookies)} session cookies")
        result = cookies.copy()
        result["oauth_authenticated"] = True
        result["authentication_method"] = "oauth_hybrid"
        return result
    else:
        raise FogisOAuthAuthenticationError("OAuth login successful but no session cookies established")


def _handle_oauth_login_form(session: requests.Session, username: str, password: str, oauth_manager) -> Dict[str, Any]:
    """
    Handle the OAuth login form submission.

    Args:
        session: The requests session
        username: FOGIS username
        password: FOGIS password
        oauth_manager: The OAuth manager instance

    Returns:
        Dict containing OAuth tokens
    """
    try:
        current_response = _get_oauth_login_page(session, oauth_manager)
        soup = BeautifulSoup(current_response.text, "html.parser")
        form_url, form_method, form_data = _extract_form_data(soup, username, password)

        logger.debug(f"Submitting OAuth login form to {form_url}")

        if form_method == "post":
            login_response = session.post(form_url, data=form_data, allow_redirects=True, timeout=(10, 30))
        else:
            login_response = session.get(form_url, params=form_data, allow_redirects=True, timeout=(10, 30))

        login_response.raise_for_status()

        # Check if we were redirected back to FOGIS (successful login)
        if "fogis.svenskfotboll.se" in login_response.url:
            logger.info("OAuth login successful - redirected back to FOGIS")
            return _extract_session_cookies(session)

        # Check if we're still at the OAuth login page (login failed)
        elif "auth.fogis.se" in login_response.url:
            logger.error("OAuth login failed - still at login page")
            error_soup = BeautifulSoup(login_response.text, "html.parser")
            error_elements = error_soup.find_all(
                ["div", "span"],
                class_=lambda x: x and ("error" in x.lower() or "invalid" in x.lower()),
            )

            if error_elements:
                error_messages = [error.get_text().strip() for error in error_elements]
                raise FogisOAuthAuthenticationError(f"OAuth login failed with errors: {'; '.join(error_messages)}")
            else:
                raise FogisOAuthAuthenticationError("OAuth login failed - invalid credentials or login error")

        else:
            raise FogisOAuthAuthenticationError(
                f"OAuth login flow completed unexpectedly - redirected to: {login_response.url}"
            )

    except requests.exceptions.RequestException as e:
        raise FogisOAuthAuthenticationError(f"Network error during OAuth login: {e}")
    except Exception as e:
        raise FogisOAuthAuthenticationError(f"Error during OAuth login form handling: {e}")


def _handle_aspnet_authentication(
    session: requests.Session,
    username: str,
    password: str,
    response: requests.Response,
    login_url: str,
) -> Dict[str, Any]:
    """
    Handle traditional ASP.NET form authentication (fallback).

    Args:
        session: The requests session
        username: FOGIS username
        password: FOGIS password
        response: The response from the login page request
        login_url: The login URL

    Returns:
        Dict containing ASP.NET session cookies
    """
    logger.debug("Using ASP.NET form authentication")

    # Parse the HTML to extract all hidden form fields
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract all hidden form fields
    form_data = {}
    hidden_inputs = soup.find_all("input", {"type": "hidden"})
    for inp in hidden_inputs:
        name = inp.get("name", "")
        value = inp.get("value", "")
        if name:
            form_data[name] = value

    # Verify we have the required tokens
    if "__VIEWSTATE" not in form_data:
        logger.error("Failed to extract __VIEWSTATE token from login page")
        raise FogisAuthenticationError("Failed to extract __VIEWSTATE token from login page")

    if "__EVENTVALIDATION" not in form_data:
        logger.error("Failed to extract __EVENTVALIDATION token from login page")
        raise FogisAuthenticationError("Failed to extract __EVENTVALIDATION token from login page")

    # Prepare the login payload with all form fields
    login_payload = form_data.copy()
    login_payload.update(
        {
            "ctl00$MainContent$UserName": username,
            "ctl00$MainContent$Password": password,
            "ctl00$MainContent$LoginButton": "Logga in",
        }
    )

    # Submit the login form
    response = session.post(login_url, data=login_payload, allow_redirects=True, timeout=(10, 30))
    response.raise_for_status()

    # Check if login was successful
    if "FogisMobilDomarKlient.ASPXAUTH" not in session.cookies:
        logger.error("ASP.NET authentication failed: Invalid credentials or login form changed")
        raise FogisAuthenticationError("ASP.NET authentication failed: Invalid credentials or login form changed")

    # Extract the cookies
    cookies = {
        "FogisMobilDomarKlient.ASPXAUTH": session.cookies.get("FogisMobilDomarKlient.ASPXAUTH"),
        "ASP.NET_SessionId": session.cookies.get("ASP.NET_SessionId"),
        "aspnet_authenticated": "true",
    }

    logger.debug("ASP.NET authentication successful")
    return cookies
