import unittest
from unittest.mock import MagicMock, Mock

import pytest
import requests

from fogis_api_client import FogisApiClient, FogisLoginError


class TestLazyLogin(unittest.TestCase):
    """Test cases for the lazy login functionality in PublicApiClient."""

    def setUp(self):
        self.client = FogisApiClient(username="testuser", password="testpassword")

        # Create a mock session
        mock_session = Mock()
        mock_session.request = MagicMock()
        mock_session.cookies = MagicMock(spec=dict)
        mock_session.cookies.set = MagicMock()

        self.client.session = mock_session
        self.client.cookies = None  # Ensure no cookies to test lazy login
        self.client.authentication_method = None

    def test_lazy_login_on_api_request(self):
        """Test that _make_authenticated_request automatically calls login when not authenticated."""
        # Mock the login method
        original_login = self.client.login
        self.client.login = MagicMock()

        # Set up login to set cookies when called
        def mock_login():
            self.client.cookies = {"FogisMobilDomarKlient_ASPXAUTH": "mock_auth_cookie"}
            self.client.authentication_method = "aspnet"
            return self.client.cookies

        self.client.login.side_effect = mock_login

        # Mock the API response
        mock_response = Mock()
        mock_response.status_code = 200
        self.client.session.request.return_value = mock_response

        # Call _make_authenticated_request
        url = "https://fogis.svenskfotboll.se/mdk/MatchWebMetoder.aspx/SomeEndpoint"
        self.client._make_authenticated_request("POST", url)

        # Verify login was called
        self.client.login.assert_called_once()

        # Verify the request was made
        self.client.session.request.assert_called_once()

        # Restore
        self.client.login = original_login

    def test_lazy_login_failure(self):
        """Test that automatic login failures are handled correctly."""
        # Mock the login method to fail
        original_login = self.client.login
        self.client.login = MagicMock()
        self.client.login.side_effect = FogisLoginError("Automatic login failed")

        url = "https://fogis.svenskfotboll.se/mdk/MatchWebMetoder.aspx/SomeEndpoint"

        # Verify that FogisLoginError is raised
        with self.assertRaises(FogisLoginError) as context:
            self.client._make_authenticated_request("POST", url)

        self.assertIn("Automatic login failed", str(context.exception))

        # Verify login was called
        self.client.login.assert_called_once()

        # Restore
        self.client.login = original_login

    def test_no_lazy_login_when_already_logged_in(self):
        """Test that _make_authenticated_request doesn't call login when already authenticated."""
        # Set cookies and auth method to simulate already being logged in
        self.client.cookies = {"FogisMobilDomarKlient_ASPXAUTH": "mock_auth_cookie"}
        self.client.authentication_method = "aspnet"

        # Mock the login method
        original_login = self.client.login
        self.client.login = MagicMock()

        # Mock the API response
        mock_response = Mock()
        mock_response.status_code = 200
        self.client.session.request.return_value = mock_response

        # Call _make_authenticated_request
        url = "https://fogis.svenskfotboll.se/mdk/MatchWebMetoder.aspx/SomeEndpoint"
        self.client._make_authenticated_request("POST", url)

        # Verify login was NOT called
        self.client.login.assert_not_called()

        # Verify the request was made
        self.client.session.request.assert_called_once()

        # Restore
        self.client.login = original_login


if __name__ == "__main__":
    unittest.main()
