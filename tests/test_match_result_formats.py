import unittest
from unittest.mock import MagicMock, Mock

from fogis_api_client import FogisApiClient


class TestMatchResultFormats(unittest.TestCase):
    """Test case for verifying both match result formats work in PublicApiClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = FogisApiClient(username="test", password="test")
        self.mock_response = Mock()
        self.mock_response.status_code = 200
        self.mock_response.json = MagicMock(return_value={"d": '{"success": true}'})
        self.client._make_authenticated_request = MagicMock(return_value=self.mock_response)

    def test_flat_format(self):
        """Test that the flat format works correctly."""
        # Flat format (new style)
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
        call_args = self.client._make_authenticated_request.call_args
        
        # Verify method and URL
        self.assertEqual(call_args.args[0], "POST")
        self.assertEqual(call_args.args[1], f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchresultatLista")

        # Check that the structure matches what we expect
        actual_payload = call_args.kwargs.get("json")
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

    def test_nested_format(self):
        """Test that the nested format works correctly."""
        # Nested format (old style from v0.0.5)
        nested_result_data = {
            "matchresultatListaJSON": [
                {
                    "matchid": 12345,
                    "matchresultattypid": 1,  # Full time
                    "matchlag1mal": 2,
                    "matchlag2mal": 1,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                },
                {
                    "matchid": 12345,
                    "matchresultattypid": 2,  # Half-time
                    "matchlag1mal": 1,
                    "matchlag2mal": 0,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                },
            ]
        }

        response = self.client.report_match_result(nested_result_data)

        # Verify the result
        self.assertEqual(response, {"success": True})

        # Verify the API was called with the correct nested structure (should be unchanged)
        self.client._make_authenticated_request.assert_called_once()
        call_args = self.client._make_authenticated_request.call_args
        
        # Verify method and URL
        self.assertEqual(call_args.args[0], "POST")
        self.assertEqual(call_args.args[1], f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchresultatLista")

        # Check that the structure matches what we expect
        actual_payload = call_args.kwargs.get("json")
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


if __name__ == "__main__":
    unittest.main()
