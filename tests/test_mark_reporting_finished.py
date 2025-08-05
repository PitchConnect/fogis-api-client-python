import unittest
from unittest.mock import MagicMock, Mock

import requests

from fogis_api_client.fogis_api_client import FogisApiClient, FogisAPIRequestError


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


class TestMarkReportingFinished(unittest.TestCase):
    """Test cases for the mark_reporting_finished functionality."""

    def setUp(self):
        self.client = FogisApiClient("testuser", "testpassword")

        # Create a mock session
        mock_session = Mock()
        mock_session.get = MagicMock()
        mock_session.post = MagicMock()
        mock_session.cookies = MagicMock(spec=dict)
        mock_session.cookies.set = MagicMock()

        self.client.session = mock_session
        self.client.cookies = {"FogisMobilDomarKlient.ASPXAUTH": "mock_auth_cookie"}  # Simulate being logged in

    def test_mark_reporting_finished_success(self):
        """Test that mark_reporting_finished works correctly with a valid match ID."""
        # Mock the API response
        mock_api_response = MockResponse(json_data={"d": {"success": True}}, status_code=200)
        self.client.session.post.return_value = mock_api_response

        # Call mark_reporting_finished
        match_id = "123456"
        response_data = self.client.mark_reporting_finished(match_id)

        # Verify the API request was made
        self.client.session.post.assert_called_once()

        # Check the URL and payload
        args, kwargs = self.client.session.post.call_args
        url = args[0]  # The URL is the first positional argument
        self.assertIn("SparaMatchGodkannDomarrapport", url)
        self.assertEqual({"matchid": int(match_id)}, kwargs["json"])

        # Verify the response data
        self.assertTrue(response_data["success"])

    def test_mark_reporting_finished_empty_match_id(self):
        """Test that mark_reporting_finished raises ValueError with an empty match ID."""
        # Call mark_reporting_finished with an empty match ID
        with self.assertRaises(ValueError) as context:
            self.client.mark_reporting_finished("")

        self.assertIn("match_id cannot be empty", str(context.exception))

        # Verify the API request was not made
        self.client.session.post.assert_not_called()

    def test_mark_reporting_finished_api_error(self):
        """Test that mark_reporting_finished handles API errors correctly."""
        # Mock the API response to simulate an error
        mock_api_response = MockResponse(json_data={"d": {"error": "Some API error"}}, status_code=400)
        self.client.session.post.return_value = mock_api_response
        mock_api_response.raise_for_status = MagicMock(side_effect=requests.exceptions.HTTPError("Mocked HTTP Error: 400"))

        # Call mark_reporting_finished
        match_id = "123456"

        # Verify that FogisAPIRequestError is raised
        with self.assertRaises(FogisAPIRequestError):
            self.client.mark_reporting_finished(match_id)

        # Verify the API request was made
        self.client.session.post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
