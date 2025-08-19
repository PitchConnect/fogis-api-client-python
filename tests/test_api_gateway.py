"""
Tests for the FOGIS API Gateway.
"""

import unittest
from unittest.mock import MagicMock

# Import the Flask app from the API gateway
import fogis_api_gateway


class TestApiGateway(unittest.TestCase):
    """Test case for the API gateway."""

    def setUp(self):
        """Set up the test case."""
        # Create a test client
        self.app = fogis_api_gateway.app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Set up mock for the Fogis API client
        self.mock_fogis_client = MagicMock()
        fogis_api_gateway.client = self.mock_fogis_client

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

    def test_index_endpoint(self):
        """Test the / endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")
        self.assertEqual(response.json["message"], "FOGIS API Gateway")

    def test_swagger_json_endpoint(self):
        """Test the /api/swagger.json endpoint."""
        # Call the endpoint
        response = self.client.get("/api/swagger.json")

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, dict)

        # Check that the OpenAPI version is correct
        self.assertEqual(response.json["openapi"], "3.0.2")

        # Check that the title is correct
        self.assertEqual(response.json["info"]["title"], "FOGIS API Gateway")

        # Check that the paths are defined
        self.assertIn("paths", response.json)
        self.assertIsInstance(response.json["paths"], dict)

        # Check that the components are defined
        self.assertIn("components", response.json)
        self.assertIn("schemas", response.json["components"])

        # Check that all required schemas are defined
        required_schemas = ["Error", "Match", "MatchResult", "Event", "Player", "Official"]
        for schema in required_schemas:
            self.assertIn(schema, response.json["components"]["schemas"])

        # Check that all endpoints are documented
        required_paths = [
            "/",
            "/hello",
            "/matches",
            "/matches/filter",
            "/match/{match_id}",
            "/match/{match_id}/result",
            "/match/{match_id}/events",
            "/match/{match_id}/events/clear",
            "/match/{match_id}/officials",
            "/match/{match_id}/finish",
            "/team/{team_id}/players",
            "/team/{team_id}/officials",
        ]
        for path in required_paths:
            self.assertIn(path, response.json["paths"])

    def test_swagger_ui_endpoint(self):
        """Test the /api/docs endpoint."""
        # Call the endpoint
        response = self.client.get("/api/docs/")

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"swagger-ui", response.data)
        self.assertIn(b"html", response.data)


if __name__ == "__main__":
    unittest.main()
