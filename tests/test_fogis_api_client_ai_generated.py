import io
import json
import logging
import unittest
from unittest.mock import Mock, patch

import requests
import jsonschema

from fogis_api_client.fogis_api_client import (
    FogisApiClient,
    FogisAPIRequestError,
    FogisDataError,
)


class TestFogisApiClient(unittest.TestCase):
    """Test cases for the FogisApiClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_client = FogisApiClient("testuser", "testpassword")

        # Set up logging capture
        self.log_capture = io.StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture)
        self.logger = logging.getLogger("fogis_api_client.api")
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.INFO)

    def tearDown(self):
        """Tear down test fixtures."""
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    @patch("requests.Session.post")
    @patch("requests.Session.get")
    def test_login_success(self, mock_get, mock_post):
        """Test successful login."""
        # Mock the get response
        mock_get_response = Mock()
        mock_get_response.text = (
            '<input name="__VIEWSTATE" value="viewstate_value" />'
            '<input name="__EVENTVALIDATION" value="eventvalidation_value" />'
        )
        mock_get.return_value = mock_get_response

        # Mock the post response
        mock_post_response = Mock()
        mock_post_response.status_code = 302
        mock_post_response.headers = {"Location": "/mdk/"}
        mock_post_response.cookies = {
            "FogisMobilDomarKlient.ASPXAUTH": "mock_auth_cookie"
        }
        mock_post.return_value = mock_post_response

        # Mock the redirect response
        mock_redirect_response = Mock()
        mock_get.side_effect = [mock_get_response, mock_redirect_response]

        # Mock the cookies
        self.api_client.session.cookies = {
            "FogisMobilDomarKlient.ASPXAUTH": "mock_auth_cookie"
        }

        # Call login
        cookies = self.api_client.login()

        # Verify the result
        self.assertIn("FogisMobilDomarKlient.ASPXAUTH", cookies)
        self.assertEqual(cookies["FogisMobilDomarKlient.ASPXAUTH"], "mock_auth_cookie")
        # We don't check for cookieconsent_status since it's an implementation detail

    @patch("requests.Session.post")
    @patch("requests.Session.get")
    def test_login_failure(self, mock_get, mock_post):
        """Test login failure."""
        # Mock the get response to raise an exception
        mock_get.side_effect = requests.exceptions.RequestException("Login failed")

        # Call login and expect an exception
        with self.assertRaises(FogisAPIRequestError):
            self.api_client.login()

        # Check the log message contains part of the error
        self.assertIn("Login request failed", self.log_capture.getvalue())

    @patch("requests.Session.post")
    def test_api_request_success(self, mock_post):
        """Test successful API request."""
        # Mock the post response
        mock_response = Mock()
        mock_response.json.return_value = {"d": '{"success": true}'}
        mock_post.return_value = mock_response

        # Set cookies to simulate being logged in
        self.api_client.cookies = {"FogisMobilDomarKlient.ASPXAUTH": "mock_auth_cookie"}

        # Call _api_request
        result = self.api_client._api_request(
            self.api_client.BASE_URL + "/MatchWebMetoder.aspx/SomeEndpoint", {}
        )

        # Verify the result
        self.assertEqual(result, {"success": True})

    @patch("requests.Session.post")
    def test_api_request_error_logging(self, mock_post):
        """Test API request error logging."""
        # Mock the post response to raise an exception
        mock_post.side_effect = requests.exceptions.RequestException(
            "API request failed"
        )

        # Set cookies to simulate being logged in
        self.api_client.cookies = {"FogisMobilDomarKlient.ASPXAUTH": "mock_auth_cookie"}

        # Create a valid payload for the endpoint
        valid_payload = {
            "matchid": 123456,
            "matchhandelsetypid": 1,
            "matchminut": 10,
            "matchlagid": 1,
            "period": 1
        }

        # Call _api_request and expect an exception
        with self.assertRaises(FogisAPIRequestError):
            self.api_client._api_request(
                self.api_client.BASE_URL + "/MatchWebMetoder.aspx/SparaMatchhandelse",
                valid_payload,
            )

        # Check the log message contains part of the error
        self.assertIn("API request failed", self.log_capture.getvalue())

    @patch("requests.Session.post")
    def test__api_request_invalid_method(self, mock_post):
        """Test invalid HTTP method."""
        # Set cookies to simulate being logged in
        self.api_client.cookies = {"FogisMobilDomarKlient.ASPXAUTH": "mock_auth_cookie"}

        # Call _api_request with an invalid method
        with self.assertRaises(ValueError) as context:
            self.api_client._api_request(
                self.api_client.BASE_URL + "/MatchWebMetoder.aspx/SparaMatchhandelse",
                {},
                method="PUT",
            )

        # Verify the error message
        self.assertEqual(str(context.exception), "Unsupported HTTP method: PUT")

    @patch("requests.Session.post")
    def test__api_request_invalid_json(self, mock_post):
        """Test invalid JSON response."""
        # Mock the post response to return invalid JSON
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_post.return_value = mock_response

        # Set cookies to simulate being logged in
        self.api_client.cookies = {"FogisMobilDomarKlient.ASPXAUTH": "mock_auth_cookie"}

        # Create a valid payload for the endpoint
        valid_payload = {
            "matchid": 123456,
            "matchhandelsetypid": 1,
            "matchminut": 10,
            "matchlagid": 1,
            "period": 1
        }

        # Temporarily disable validation for this test
        from fogis_api_client.api_contracts import ValidationConfig
        original_enable_validation = ValidationConfig.enable_validation
        ValidationConfig.enable_validation = False

        try:
            # Call _api_request and expect an exception
            with self.assertRaises(FogisDataError) as context:
                self.api_client._api_request(
                    self.api_client.BASE_URL + "/test__api_request_invalid_json",
                    valid_payload,
                )

            # Verify the error message
            self.assertIn("Failed to parse API response", str(context.exception))
        finally:
            # Restore validation setting
            ValidationConfig.enable_validation = original_enable_validation

    @patch("fogis_api_client.fogis_api_client.FogisApiClient._api_request")
    def test_fetch_matches_list_json_success(self, mock_api_request):
        """Test successful fetch_matches_list_json."""
        # Mock the _api_request method to return a valid response
        mock_api_request.return_value = {"matchlista": [{"id": "1"}, {"id": "2"}]}

        # Call the method
        result = self.api_client.fetch_matches_list_json()

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "1")
        self.assertEqual(result[1]["id"], "2")

        # Verify the API call was made with the correct endpoint
        self.assertEqual(mock_api_request.call_count, 1)
        call_args = mock_api_request.call_args[0]
        self.assertEqual(
            call_args[0],
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatcherAttRapportera",
        )

    @patch("fogis_api_client.fogis_api_client.FogisApiClient._api_request")
    def test_fetch_matches_list_json_empty_list(self, mock_api_request):
        """Test fetch_matches_list_json with empty list."""
        # Mock the _api_request method to return an empty list
        mock_api_request.return_value = {"matchlista": []}

        # Call the method
        result = self.api_client.fetch_matches_list_json()

        # Verify the result
        self.assertEqual(len(result), 0)

        # Verify the API call was made with the correct endpoint
        self.assertEqual(mock_api_request.call_count, 1)
        call_args = mock_api_request.call_args[0]
        self.assertEqual(
            call_args[0],
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatcherAttRapportera",
        )

    @patch("fogis_api_client.fogis_api_client.FogisApiClient._api_request")
    def test_fetch_team_players_json_success(self, mock_api_request):
        """Test successful fetch_team_players_json."""
        # Mock the _api_request method to return a valid response
        mock_api_request.return_value = {"spelare": [{"id": "1"}, {"id": "2"}]}

        # Call the method
        result = self.api_client.fetch_team_players_json(team_id=123)

        # Verify the result
        self.assertEqual(result["spelare"][0]["id"], "1")
        self.assertEqual(result["spelare"][1]["id"], "2")

        # Verify the API call used the correct parameter name (matchlagid)
        mock_api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatchdeltagareListaForMatchlag",
            {"matchlagid": 123},
        )

    @patch("fogis_api_client.fogis_api_client.FogisApiClient._api_request")
    def test_fetch_team_officials_json_failure(self, mock_api_request):
        """Test fetch_team_officials_json failure."""
        # Mock the _api_request method to raise an exception
        mock_api_request.side_effect = FogisAPIRequestError("API request failed")

        # Call the method and expect an exception
        with self.assertRaises(FogisAPIRequestError):
            self.api_client.fetch_team_officials_json(team_id=123)

        # Verify the API call attempted to use the correct parameter name (matchlagid)
        mock_api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatchlagledareListaForMatchlag",
            {"matchlagid": 123},
        )

    @patch("fogis_api_client.fogis_api_client.FogisApiClient._api_request")
    def test_fetch_team_officials_json_success(self, mock_api_request):
        """Test successful fetch_team_officials_json."""
        # Mock the _api_request method to return a valid response
        mock_api_request.return_value = [
            {"personid": 1, "fornamn": "John", "efternamn": "Doe", "roll": "Tränare"},
            {
                "personid": 2,
                "fornamn": "Jane",
                "efternamn": "Smith",
                "roll": "Assisterande tränare",
            },
        ]

        # Call the method
        result = self.api_client.fetch_team_officials_json(team_id=123)

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["personid"], 1)
        self.assertEqual(result[0]["roll"], "Tränare")

        # Verify the API call used the correct parameter name (matchlagid)
        mock_api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatchlagledareListaForMatchlag",
            {"matchlagid": 123},
        )

    @patch("fogis_api_client.fogis_api_client.FogisApiClient._api_request")
    def test_report_match_event_success(self, mock_api_request):
        """Test successful report_match_event."""
        # Create event data
        event_data = {
            "matchid": 123,  # Integer instead of string
            "matchhandelsetypid": 6,  # Regular goal
            "matchlagid": 789,  # Integer instead of string
            "matchminut": 35,
            "spelareid": 456,  # Integer instead of string
            "period": 1  # Add required period field
        }

        # Mock the _api_request method to return a valid response
        mock_api_request.return_value = {"success": True, "id": 12345}

        # Call the method
        result = self.api_client.report_match_event(event_data)

        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["id"], 12345)

    @patch("fogis_api_client.fogis_api_client.FogisApiClient._api_request")
    def test_report_match_event_invalid_event_data(self, mock_api_request):
        """Test report_match_event with invalid data."""
        # Create invalid event data (missing required fields)
        event_data = {"matchid": 123}  # Missing other required fields

        # Mock the _api_request method to raise a validation error
        mock_api_request.side_effect = ValueError("Invalid event data")

        # Call the method and expect an exception
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            self.api_client.report_match_event(event_data)

    @patch("fogis_api_client.fogis_api_client.FogisApiClient._api_request")
    def test_delete_match_event_success(self, mock_api_request):
        """Test successful delete_match_event."""
        # Mock the _api_request method to return success
        mock_api_request.return_value = {"success": True}

        # Call the method
        result = self.api_client.delete_match_event(event_id=123)

        # Verify the result
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
