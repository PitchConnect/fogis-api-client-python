import unittest
from unittest.mock import MagicMock, Mock

import pytest
import requests

from fogis_api_client import FogisApiClient, FogisAPIRequestError


class TestMarkReportingFinished(unittest.TestCase):
    """Test cases for the mark_reporting_finished functionality in PublicApiClient."""

    def setUp(self):
        self.client = FogisApiClient(username="testuser", password="testpassword")

        # Create a mock session
        mock_session = Mock()
        mock_session.request = MagicMock()
        mock_session.cookies = MagicMock(spec=dict)
        mock_session.cookies.set = MagicMock()

        self.client.session = mock_session
        self.client.cookies = {"FogisMobilDomarKlient_ASPXAUTH": "mock_auth_cookie"}  # Simulate being logged in
        self.client.authentication_method = "aspnet"

    def test_mark_reporting_finished_success(self):
        """Test that mark_reporting_finished works correctly with a valid match ID."""
        # Mock the API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"d": {"success": True}})
        self.client.session.request.return_value = mock_response

        # Call mark_reporting_finished
        match_id = "123456"
        response_data = self.client.mark_reporting_finished(match_id)

        # Verify the API request was made
        self.client.session.request.assert_called_once()

        # Check the URL and payload
        args, kwargs = self.client.session.request.call_args
        url = args[1]
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
        self.client.session.request.assert_not_called()

    def test_mark_reporting_finished_api_error(self):
        """Test that mark_reporting_finished handles API errors correctly."""
        # Mock the API response to simulate an error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status = MagicMock(side_effect=requests.exceptions.HTTPError("Mocked HTTP Error: 400"))
        self.client.session.request.return_value = mock_response

        # Call mark_reporting_finished
        match_id = "123456"

        # Verify that FogisAPIRequestError is raised
        with self.assertRaises(FogisAPIRequestError):
            self.client.mark_reporting_finished(match_id)

        # Verify the API request was made
        self.client.session.request.assert_called_once()


if __name__ == "__main__":
    unittest.main()
