import unittest
from unittest.mock import MagicMock, Mock

import requests

from fogis_api_client.fogis_api_client import FogisApiClient, FogisLoginError


class MockResponse:
    """
    A mock class to simulate requests.Response for testing.
    """

    def __init__(self, json_data, status_code):
        self._json_data = MagicMock(return_value=json_data)
        self.status_code = status_code

    def json(self):
        returned_json_data = self._json_data()
        return returned_json_data

    def raise_for_status(self):
        if 400 <= self.status_code < 600:
            raise requests.exceptions.HTTPError(f"Mocked HTTP Error: {self.status_code}", response=None)


class TestLazyLogin(unittest.TestCase):
    """Test cases for the lazy login functionality."""

    def setUp(self):
        self.client = FogisApiClient("testuser", "testpassword")

        # Create a mock session
        mock_session = Mock()
        mock_session.get = MagicMock()
        mock_session.post = MagicMock()
        mock_session.cookies = MagicMock(spec=dict)
        mock_session.cookies.set = MagicMock()

        self.client.session = mock_session
        self.client.cookies = None  # Ensure no cookies to test lazy login

    def test_lazy_login_on_api_request(self):
        """Test that _api_request automatically calls login when cookies are not set."""
        # Mock the login method
        original_login = self.client.login
        self.client.login = MagicMock()

        # Set up login to set cookies when called
        def mock_login():
            self.client.cookies = {"FogisMobilDomarKlient.ASPXAUTH": "mock_auth_cookie"}
            return self.client.cookies

        self.client.login.side_effect = mock_login

        # Mock the API response
        mock_api_response = MockResponse(json_data={"d": {"key": "value"}}, status_code=200)
        self.client.session.post.return_value = mock_api_response

        # Call _api_request
        url = "https://fogis.svenskfotboll.se/mdk/MatchWebMetoder.aspx/SomeEndpoint"
        payload = {"param1": "value1"}
        self.client._api_request(url, payload, method="POST")

        # Verify login was called
        self.client.login.assert_called_once()

        # Verify the API request was made with the correct parameters
        self.client.session.post.assert_called_once()

        # Restore the original login method
        self.client.login = original_login

    def test_lazy_login_failure(self):
        """Test that _api_request handles login failures correctly."""
        # Mock the login method to fail
        original_login = self.client.login
        self.client.login = MagicMock()
        self.client.login.return_value = None
        self.client.cookies = None  # Login failed, no cookies

        # Call _api_request
        url = "https://fogis.svenskfotboll.se/mdk/MatchWebMetoder.aspx/SomeEndpoint"
        payload = {"param1": "value1"}

        # Verify that FogisLoginError is raised
        with self.assertRaises(FogisLoginError) as context:
            self.client._api_request(url, payload, method="POST")

        self.assertIn("Automatic login failed", str(context.exception))

        # Verify login was called
        self.client.login.assert_called_once()

        # Restore the original login method
        self.client.login = original_login

    def test_no_lazy_login_when_already_logged_in(self):
        """Test that _api_request doesn't call login when cookies are already set."""
        # Set cookies to simulate already being logged in
        self.client.cookies = {"FogisMobilDomarKlient.ASPXAUTH": "mock_auth_cookie"}

        # Mock the login method
        original_login = self.client.login
        self.client.login = MagicMock()

        # Mock the API response
        mock_api_response = MockResponse(json_data={"d": {"key": "value"}}, status_code=200)
        self.client.session.post.return_value = mock_api_response

        # Call _api_request
        url = "https://fogis.svenskfotboll.se/mdk/MatchWebMetoder.aspx/SomeEndpoint"
        payload = {"param1": "value1"}
        self.client._api_request(url, payload, method="POST")

        # Verify login was NOT called
        self.client.login.assert_not_called()

        # Verify the API request was made with the correct parameters
        self.client.session.post.assert_called_once()

        # Restore the original login method
        self.client.login = original_login


if __name__ == "__main__":
    unittest.main()
