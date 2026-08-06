import unittest
from unittest.mock import MagicMock, Mock

from fogis_api_client import FogisApiClient


class TestAISafeMarkers(unittest.TestCase):
    """Test case for verifying that AI-safe markers don't affect functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = FogisApiClient(username="test", password="test")
        self.mock_response = Mock()
        self.mock_response.status_code = 200
        self.mock_response.json = MagicMock(return_value={"d": '{"success": true}'})
        self.client._make_authenticated_request = MagicMock(return_value=self.mock_response)

    def test_report_match_result_with_ai_markers(self):
        """Test that report_match_result works correctly with AI-safe markers."""
        # Flat format
        flat_result_data = {
            "matchid": 12345,
            "hemmamal": 2,
            "bortamal": 1,
            "halvtidHemmamal": 1,
            "halvtidBortamal": 0,
        }

        response = self.client.report_match_result(flat_result_data)

        # Verify the result
        self.assertEqual(response, {"success": True})

        # Verify the API was called with the correct nested structure
        self.client._make_authenticated_request.assert_called_once()

        # Get the call arguments
        call_args = self.client._make_authenticated_request.call_args

        # Extract HTTP method, URL, and payload from call_args
        method = call_args.args[0]
        url = call_args.args[1]
        kwargs = call_args.kwargs
        actual_payload = kwargs.get("json")

        self.assertEqual(method, "POST")
        self.assertEqual(url, f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchresultatLista")
        self.assertIn("matchresultatListaJSON", actual_payload)
        self.assertEqual(len(actual_payload["matchresultatListaJSON"]), 2)

        # Check full-time result
        fulltime = actual_payload["matchresultatListaJSON"][0]
        self.assertEqual(fulltime["matchid"], 12345)
        self.assertEqual(fulltime["matchresultattypid"], 1)
        self.assertEqual(fulltime["matchlag1mal"], 2)
        self.assertEqual(fulltime["matchlag2mal"], 1)

        # Check half-time result
        halftime = actual_payload["matchresultatListaJSON"][1]
        self.assertEqual(halftime["matchid"], 12345)
        self.assertEqual(halftime["matchresultattypid"], 2)
        self.assertEqual(halftime["matchlag1mal"], 1)
        self.assertEqual(halftime["matchlag2mal"], 0)

    def test_report_match_event_with_ai_markers(self):
        """Test that report_match_event (mapped to save_match_event) works correctly with AI-safe markers."""
        # Create event data for a goal
        event_data = {
            "matchid": 12345,
            "matchhandelsetypid": 6,  # Regular goal
            "matchminut": 35,
            "matchlagid": 78910,  # Team ID
            "spelareid": 12345,  # Player ID
            "period": 1,
            "hemmamal": 1,
            "bortamal": 0,
        }

        response = self.client.save_match_event(event_data)

        # Verify the result
        self.assertEqual(response, {"success": True})

        # Verify the API was called with the correct data
        self.client._make_authenticated_request.assert_called_once()

        # Get the call arguments
        call_args = self.client._make_authenticated_request.call_args

        # Extract HTTP method, URL, and payload
        method = call_args.args[0]
        url = call_args.args[1]
        kwargs = call_args.kwargs
        actual_payload = kwargs.get("json")

        self.assertEqual(method, "POST")
        self.assertEqual(url, f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchhandelse")
        self.assertEqual(actual_payload["matchid"], 12345)
        self.assertEqual(actual_payload["matchhandelsetypid"], 6)
        self.assertEqual(actual_payload["matchminut"], 35)
        self.assertEqual(actual_payload["matchlagid"], 78910)
        self.assertEqual(actual_payload["spelareid"], 12345)
        self.assertEqual(actual_payload["period"], 1)
        self.assertEqual(actual_payload["hemmamal"], 1)
        self.assertEqual(actual_payload["bortamal"], 0)

    def test_mark_reporting_finished_with_ai_markers(self):
        """Test that mark_reporting_finished works correctly with AI-safe markers."""
        match_id = 12345

        # Reset the mock to ensure it's clean
        self.client._make_authenticated_request.reset_mock()

        response = self.client.mark_reporting_finished(match_id)

        # Verify the result
        self.assertEqual(response, {"success": True})

        # Verify the API was called with the correct data
        self.client._make_authenticated_request.assert_called_once()

        # Get the call arguments
        call_args = self.client._make_authenticated_request.call_args

        # Extract HTTP method, URL, and payload
        method = call_args.args[0]
        url = call_args.args[1]
        kwargs = call_args.kwargs
        payload = kwargs.get("json")

        self.assertEqual(method, "POST")
        self.assertEqual(url, f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchGodkannDomarrapport")
        self.assertEqual(payload["matchid"], 12345)


if __name__ == "__main__":
    unittest.main()
