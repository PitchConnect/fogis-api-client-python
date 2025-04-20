"""
Regression tests for parameter names in the FOGIS API client.

These tests ensure that the parameter names used in the API calls match
what the FOGIS API expects, preventing regressions in future changes.
"""
import unittest
from unittest.mock import MagicMock

from fogis_api_client.fogis_api_client import FogisApiClient


class TestParameterNames(unittest.TestCase):
    """Test cases for parameter names in the FOGIS API client."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = FogisApiClient("testuser", "testpassword")
        self.client.cookies = {"FogisMobilDomarKlient.ASPXAUTH": "mock_auth_cookie"}

    def test_fetch_team_players_json_parameter_name(self):
        """Test that fetch_team_players_json uses the correct parameter name (matchlagid)."""
        # Mock the _api_request method
        self.client._api_request = MagicMock(return_value={"spelare": []})

        # Call the method
        self.client.fetch_team_players_json(team_id=123)

        # Verify the parameter name in the API call
        self.client._api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatchdeltagareListaForMatchlag",
            {"matchlagid": 123},
        )

    def test_fetch_team_officials_json_parameter_name(self):
        """Test that fetch_team_officials_json uses the correct parameter name (matchlagid)."""
        # Mock the _api_request method
        self.client._api_request = MagicMock(return_value=[])

        # Call the method
        self.client.fetch_team_officials_json(team_id=123)

        # Verify the parameter name in the API call
        self.client._api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatchlagledareListaForMatchlag",
            {"matchlagid": 123},
        )

    def test_report_team_official_action_parameter_name(self):
        """Test that report_team_official_action uses the correct parameter name (lagid)."""
        # Mock the _api_request method
        self.client._api_request = MagicMock(return_value={"success": True})

        # Call the method
        action_data = {
            "matchid": "12345",
            "lagid": "67890",  # This parameter name is still 'lagid' in this method
            "personid": "54321",
            "matchlagledaretypid": "2",
        }
        self.client.report_team_official_action(action_data)

        # Verify the parameter name in the API call
        self.client._api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchlagledare",
            {
                "matchid": 12345,
                "lagid": 67890,  # Should still be 'lagid' for this method
                "personid": 54321,
                "matchlagledaretypid": 2,
            },
        )


if __name__ == "__main__":
    unittest.main()
