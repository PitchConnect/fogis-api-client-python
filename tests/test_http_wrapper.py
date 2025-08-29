import unittest
from unittest.mock import Mock, patch

# Import the Flask app from the API Gateway
import fogis_api_client_http_wrapper


class TestHttpWrapper(unittest.TestCase):
    """Test cases for the API Gateway."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test client
        self.app = fogis_api_client_http_wrapper.app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Mock the FogisApiClient
        self.mock_fogis_client = Mock()
        fogis_api_client_http_wrapper.client = self.mock_fogis_client

        # Set up mock responses
        self.mock_fogis_client.hello_world.return_value = "Hello, brave new world!"
        self.mock_fogis_client.fetch_matches_list_json.return_value = [
            {"id": "1", "home_team": "Team A", "away_team": "Team B"}
        ]
        self.mock_fogis_client.fetch_match_json.return_value = {
            "id": "123",
            "home_team": "Team A",
            "away_team": "Team B",
            "events": [{"id": "1", "type": "goal"}],
        }
        self.mock_fogis_client.fetch_match_result_json.return_value = {
            "id": "123",
            "home_score": 2,
            "away_score": 1,
        }
        self.mock_fogis_client.fetch_match_events_json.return_value = [{"id": "1", "type": "goal", "player": "John Doe"}]
        self.mock_fogis_client.fetch_match_officials_json.return_value = [{"id": "1", "name": "Jane Smith", "role": "Referee"}]
        self.mock_fogis_client.fetch_team_players_json.return_value = [{"id": "1", "name": "John Doe", "position": "Forward"}]
        self.mock_fogis_client.fetch_team_officials_json.return_value = [{"id": "1", "name": "Coach Smith", "role": "Coach"}]
        self.mock_fogis_client.report_match_event.return_value = {"status": "success"}
        self.mock_fogis_client.clear_match_events.return_value = {"status": "success"}
        self.mock_fogis_client.mark_reporting_finished.return_value = {"success": True}

    def test_hello_endpoint(self):
        """Test the /hello endpoint."""
        response = self.client.get("/hello")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"message": "Hello, brave new world!"})

    def test_index_endpoint(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, dict)
        self.assertEqual(response.json, {"status": "ok", "message": "FOGIS API Gateway"})

    @patch("fogis_api_client_http_wrapper.client.fetch_matches_list_json")
    def test_matches_endpoint(self, mock_fetch):
        """Test the /matches endpoint."""
        # Set up the mock
        mock_fetch.return_value = [{"id": "1", "home_team": "Team A", "away_team": "Team B"}]

        # Call the endpoint
        response = self.client.get("/matches")

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [{"id": "1", "home_team": "Team A", "away_team": "Team B"}])
        mock_fetch.assert_called_once()

    @patch("fogis_api_client_http_wrapper.client.fetch_matches_list_json")
    def test_matches_endpoint_with_query_params(self, mock_fetch):
        """Test the /matches endpoint with query parameters."""
        # Set up the mock - return response in the format that the API actually returns
        mock_fetch.return_value = {
            "matchlista": [{"id": "1", "home_team": "Team A", "away_team": "Team B", "datum": "2023-01-01"}]
        }

        # Test with date range parameters
        response = self.client.get("/matches?from_date=2023-01-01&to_date=2023-12-31")
        self.assertEqual(response.status_code, 200)
        mock_fetch.assert_called_with(filter_params={"datumFran": "2023-01-01", "datumTill": "2023-12-31"})

        # Reset mock for next test
        mock_fetch.reset_mock()

        # Test with pagination parameters
        response = self.client.get("/matches?limit=10&offset=5")
        self.assertEqual(response.status_code, 200)
        mock_fetch.assert_called_with(filter_params={})

        # Reset mock for next test
        mock_fetch.reset_mock()

        # Test with sorting parameters
        response = self.client.get("/matches?sort_by=datum&order=desc")
        self.assertEqual(response.status_code, 200)
        mock_fetch.assert_called_with(filter_params={})

    @patch("fogis_api_client_http_wrapper.client.fetch_match_json")
    def test_match_details_endpoint(self, mock_fetch):
        """Test the /match/<match_id> endpoint."""
        # Set up the mock
        mock_fetch.return_value = {
            "id": "123",
            "home_team": "Team A",
            "away_team": "Team B",
            "events": [{"id": "1", "type": "goal"}],
        }

        # Call the endpoint
        response = self.client.get("/match/123")

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "id": "123",
                "home_team": "Team A",
                "away_team": "Team B",
                "events": [{"id": "1", "type": "goal"}],
            },
        )
        mock_fetch.assert_called_once_with("123")

    @patch("fogis_api_client_http_wrapper.client.fetch_match_json")
    @patch("fogis_api_client_http_wrapper.client.fetch_match_players_json")
    @patch("fogis_api_client_http_wrapper.client.fetch_match_officials_json")
    def test_match_details_endpoint_with_query_params(self, mock_officials, mock_players, mock_match):
        """Test the /match/<match_id> endpoint with query parameters."""
        # Set up the mocks
        mock_match.return_value = {
            "id": "123",
            "home_team": "Team A",
            "away_team": "Team B",
            "events": [{"id": "1", "type": "goal"}],
        }
        mock_players.return_value = [{"id": "1", "name": "John Doe"}]
        mock_officials.return_value = [{"id": "1", "name": "Jane Smith", "role": "Referee"}]

        # Test with include_events=false
        response = self.client.get("/match/123?include_events=false")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("events", response.json)
        mock_match.assert_called_with("123")

        # Reset mocks for next test
        mock_match.reset_mock()
        mock_players.reset_mock()
        mock_officials.reset_mock()

        # Test with include_players=true
        response = self.client.get("/match/123?include_players=true")
        self.assertEqual(response.status_code, 200)
        self.assertIn("players", response.json)
        mock_match.assert_called_with("123")
        mock_players.assert_called_with("123")

        # Reset mocks for next test
        mock_match.reset_mock()
        mock_players.reset_mock()
        mock_officials.reset_mock()

        # Test with include_officials=true
        response = self.client.get("/match/123?include_officials=true")
        self.assertEqual(response.status_code, 200)
        self.assertIn("officials", response.json)
        mock_match.assert_called_with("123")
        mock_officials.assert_called_with("123")

    @patch("fogis_api_client_http_wrapper.client.fetch_match_json")
    def test_match_details_endpoint_error(self, mock_fetch):
        """Test the /match/<match_id> endpoint with an error."""
        # Set up the mock to raise an exception
        mock_fetch.side_effect = Exception("Test error")

        # Call the endpoint
        response = self.client.get("/match/123")

        # Verify the response
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {"error": "Test error"})
        mock_fetch.assert_called_once_with("123")

    @patch("fogis_api_client_http_wrapper.client.fetch_matches_list_json")
    def test_matches_endpoint_error(self, mock_fetch):
        """Test the /matches endpoint with an error."""
        # Set up the mock to raise an exception
        mock_fetch.side_effect = Exception("Test error")

        # Call the endpoint
        response = self.client.get("/matches")

        # Verify the response
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {"error": "Test error"})
        mock_fetch.assert_called_once()

    def test_invalid_endpoint(self):
        """Test accessing an invalid endpoint."""
        response = self.client.get("/invalid-endpoint")
        self.assertEqual(response.status_code, 404)

    def test_signal_handler(self):
        """Test the signal handler function."""
        # This is a simple test to ensure the function exists and can be called
        # We can't easily test the actual signal handling without complex mocking
        self.assertTrue(callable(fogis_api_client_http_wrapper.signal_handler))

    @patch("fogis_api_client_http_wrapper.client.fetch_match_result_json")
    def test_match_result_endpoint(self, mock_fetch):
        """Test the /match/<match_id>/result endpoint."""
        # Set up the mock
        mock_fetch.return_value = {"id": "123", "home_score": 2, "away_score": 1}

        # Call the endpoint
        response = self.client.get("/match/123/result")

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"id": "123", "home_score": 2, "away_score": 1})
        mock_fetch.assert_called_once_with("123")

    @patch("fogis_api_client_http_wrapper.client.fetch_match_events_json")
    def test_match_events_endpoint(self, mock_fetch):
        """Test the /match/<match_id>/events GET endpoint."""
        # Set up the mock
        mock_fetch.return_value = [{"id": "1", "type": "goal", "player": "John Doe", "team": "Team A", "time": "45:00"}]

        # Call the endpoint
        response = self.client.get("/match/123/events")

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            [{"id": "1", "type": "goal", "player": "John Doe", "team": "Team A", "time": "45:00"}],
        )
        mock_fetch.assert_called_once_with("123")

    @patch("fogis_api_client_http_wrapper.client.fetch_match_events_json")
    def test_match_events_endpoint_with_query_params(self, mock_fetch):
        """Test the /match/<match_id>/events GET endpoint with query parameters."""
        # Set up the mock
        mock_fetch.return_value = [
            {"id": "1", "type": "goal", "player": "John Doe", "team": "Team A", "time": "45:00"},
            {"id": "2", "type": "card", "player": "Jane Smith", "team": "Team B", "time": "60:00"},
            {
                "id": "3",
                "type": "substitution",
                "player": "Bob Johnson",
                "team": "Team A",
                "time": "75:00",
            },
        ]

        # Test with type filter
        response = self.client.get("/match/123/events?type=goal")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]["type"], "goal")
        mock_fetch.assert_called_with("123")

        # Reset mock for next test
        mock_fetch.reset_mock()

        # Test with player filter
        response = self.client.get("/match/123/events?player=Jane")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]["player"], "Jane Smith")
        mock_fetch.assert_called_with("123")

        # Reset mock for next test
        mock_fetch.reset_mock()

        # Test with team filter
        response = self.client.get("/match/123/events?team=Team A")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 2)
        self.assertEqual(response.json[0]["team"], "Team A")
        self.assertEqual(response.json[1]["team"], "Team A")
        mock_fetch.assert_called_with("123")

        # Reset mock for next test
        mock_fetch.reset_mock()

        # Test with pagination
        response = self.client.get("/match/123/events?limit=1&offset=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]["id"], "2")
        mock_fetch.assert_called_with("123")

        # Reset mock for next test
        mock_fetch.reset_mock()

        # Test with sorting
        response = self.client.get("/match/123/events?sort_by=time&order=desc")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 3)
        self.assertEqual(response.json[0]["time"], "75:00")
        mock_fetch.assert_called_with("123")

    @patch("fogis_api_client_http_wrapper.client.report_match_event")
    def test_report_match_event_endpoint(self, mock_report):
        """Test the /match/<match_id>/events POST endpoint."""
        # Set up the mock
        mock_report.return_value = {"status": "success"}

        # Call the endpoint
        event_data = {"type": "goal", "player": "John Doe"}
        response = self.client.post("/match/123/events", json=event_data)

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "success"})

        # Verify that matchid was added to the event data
        expected_data = {"type": "goal", "player": "John Doe", "matchid": "123"}
        mock_report.assert_called_once_with(expected_data)

    def test_report_match_event_endpoint_no_data(self):
        """Test the /match/<match_id>/events POST endpoint with no data."""
        # Call the endpoint with no JSON data
        response = self.client.post("/match/123/events")

        # Verify the response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": "No event data provided"})

    @patch("fogis_api_client_http_wrapper.client.clear_match_events")
    def test_clear_match_events_endpoint(self, mock_clear):
        """Test the /match/<match_id>/events/clear endpoint."""
        # Set up the mock
        mock_clear.return_value = {"status": "success"}

        # Call the endpoint
        response = self.client.post("/match/123/events/clear")

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "success"})
        mock_clear.assert_called_once_with("123")

    @patch("fogis_api_client_http_wrapper.client.fetch_match_officials_json")
    def test_match_officials_endpoint(self, mock_fetch):
        """Test the /match/<match_id>/officials endpoint."""
        # Set up the mock
        mock_fetch.return_value = [{"id": "1", "name": "Jane Smith", "role": "Referee"}]

        # Call the endpoint
        response = self.client.get("/match/123/officials")

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [{"id": "1", "name": "Jane Smith", "role": "Referee"}])
        mock_fetch.assert_called_once_with("123")

    @patch("fogis_api_client_http_wrapper.client.fetch_team_players_json")
    def test_team_players_endpoint(self, mock_fetch):
        """Test the /team/<team_id>/players endpoint."""
        # Set up the mock
        mock_fetch.return_value = [{"id": "1", "name": "John Doe", "position": "Forward"}]

        # Call the endpoint
        response = self.client.get("/team/456/players")

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [{"id": "1", "name": "John Doe", "position": "Forward"}])
        mock_fetch.assert_called_once_with("456")

    @patch("fogis_api_client_http_wrapper.client.fetch_team_officials_json")
    def test_team_officials_endpoint(self, mock_fetch):
        """Test the /team/<team_id>/officials endpoint."""
        # Set up the mock
        mock_fetch.return_value = [{"id": "1", "name": "Coach Smith", "role": "Coach"}]

        # Call the endpoint
        response = self.client.get("/team/456/officials")

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [{"id": "1", "name": "Coach Smith", "role": "Coach"}])
        mock_fetch.assert_called_once_with("456")

    @patch("fogis_api_client_http_wrapper.client.mark_reporting_finished")
    def test_finish_match_report_endpoint(self, mock_finish):
        """Test the /match/<match_id>/finish endpoint."""
        # Set up the mock
        mock_finish.return_value = {"success": True}

        # Call the endpoint
        response = self.client.post("/match/123/finish")

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"success": True})
        mock_finish.assert_called_once_with("123")

    @patch("fogis_api_client_http_wrapper.MatchListFilter")
    def test_filtered_matches_endpoint(self, mock_filter_class):
        """Test the /matches/filter endpoint."""
        # Set up the mock
        mock_filter_instance = mock_filter_class.return_value
        mock_filter_instance.fetch_filtered_matches.return_value = [{"id": "1", "home_team": "Team A", "away_team": "Team B"}]

        # Call the endpoint with filter data
        filter_data = {"from_date": "2023-01-01", "status": "upcoming"}
        response = self.client.post("/matches/filter", json=filter_data)

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [{"id": "1", "home_team": "Team A", "away_team": "Team B"}])

        # Verify that the filter properties were set correctly
        self.assertEqual(mock_filter_instance.from_date, "2023-01-01")
        self.assertEqual(mock_filter_instance.status, "upcoming")
        mock_filter_instance.fetch_filtered_matches.assert_called_once_with(fogis_api_client_http_wrapper.client)


if __name__ == "__main__":
    unittest.main()
