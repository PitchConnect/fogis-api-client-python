import unittest
from unittest.mock import MagicMock, Mock

from fogis_api_client import FogisApiClient


class TestParameterNames(unittest.TestCase):
    """Test cases for parameter names in the PublicApiClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = FogisApiClient(username="testuser", password="testpassword")
        self.client.cookies = {"FogisMobilDomarKlient_ASPXAUTH": "mock_auth_cookie"}
        self.client.authentication_method = "aspnet"
        
        self.mock_response = Mock()
        self.mock_response.status_code = 200
        self.client._make_authenticated_request = MagicMock(return_value=self.mock_response)

    def test_fetch_team_players_json_parameter_name(self):
        """Test that fetch_team_players_json uses the correct parameter name (matchlagid)."""
        self.mock_response.json = MagicMock(return_value={"d": '{"spelare": []}'})

        # Call the method
        self.client.fetch_team_players_json(team_id=123)

        # Verify the parameter name in the API call
        self.client._make_authenticated_request.assert_called_once()
        call_args = self.client._make_authenticated_request.call_args
        
        self.assertEqual(call_args.args[0], "POST")
        self.assertEqual(call_args.args[1], f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatchdeltagareListaForMatchlag")
        self.assertEqual(call_args.kwargs.get("json"), {"matchlagid": 123})

    def test_fetch_team_officials_json_parameter_name(self):
        """Test that fetch_team_officials_json uses the correct parameter name (matchlagid)."""
        self.mock_response.json = MagicMock(return_value={"d": "[]"})

        # Call the method
        self.client.fetch_team_officials_json(team_id=123)

        # Verify the parameter name in the API call
        self.client._make_authenticated_request.assert_called_once()
        call_args = self.client._make_authenticated_request.call_args
        
        self.assertEqual(call_args.args[0], "POST")
        self.assertEqual(call_args.args[1], f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatchlagledareListaForMatchlag")
        self.assertEqual(call_args.kwargs.get("json"), {"matchlagid": 123})

    def test_save_team_official_parameter_name(self):
        """Test that save_team_official uses the correct parameter name (lagid)."""
        self.mock_response.json = MagicMock(return_value={"d": '{"success": true}'})

        # Call the method
        action_data = {
            "matchid": "12345",
            "lagid": "67890",
            "personid": "54321",
            "matchlagledaretypid": "2",
        }
        self.client.save_team_official(action_data)

        # Verify the parameter name in the API call
        self.client._make_authenticated_request.assert_called_once()
        call_args = self.client._make_authenticated_request.call_args
        
        self.assertEqual(call_args.args[0], "POST")
        self.assertEqual(call_args.args[1], f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchlagledare")
        self.assertEqual(call_args.kwargs.get("json"), {
            "matchid": 12345,
            "lagid": 67890,
            "personid": 54321,
            "matchlagledaretypid": 2,
        })


if __name__ == "__main__":
    unittest.main()
