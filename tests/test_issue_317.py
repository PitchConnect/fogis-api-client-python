from unittest.mock import MagicMock, patch
import pytest
from fogis_api_client.public_api_client import PublicApiClient

class TestIssue317:
    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_json")
    @patch("fogis_api_client.internal.api_client.InternalApiClient.get_match_players_for_team")
    def test_fetch_match_players_uses_correct_endpoint(self, mock_get_players, mock_fetch_match):
        """Test that fetch_match_players_json uses get_match_players_for_team with correct IDs."""
        client = PublicApiClient(username="test", password="test")
        client.cookies = {"test": "cookie"}
        
        # Mock match details response
        mock_fetch_match.return_value = {
            "matchid": 123,
            "hemmalagid": 10,
            "bortalagid": 20
        }
        
        # Mock players response
        mock_get_players.return_value = [{"personid": 1, "fornamn": "Test", "efternamn": "Player"}]
        
        # Call fetch_match_players_json
        result = client.fetch_match_players_json(123)
        
        # Verify calls
        mock_fetch_match.assert_called_with(123)
        
        # Should be called twice, once for each team
        assert mock_get_players.call_count == 2
        mock_get_players.assert_any_call(123, 10)
        mock_get_players.assert_any_call(123, 20)
        
        # Verify result structure
        assert "hemmalag" in result
        assert "bortalag" in result
        assert len(result["hemmalag"]) == 1
        assert len(result["bortalag"]) == 1

    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_json")
    @patch("fogis_api_client.internal.api_client.InternalApiClient.get_match_players_for_team")
    def test_fetch_match_players_handles_missing_team_ids(self, mock_get_players, mock_fetch_match):
        """Test that fetch_match_players_json handles missing team IDs gracefully."""
        client = PublicApiClient(username="test", password="test")
        client.cookies = {"test": "cookie"}
        
        # Mock match details response with missing away team ID
        mock_fetch_match.return_value = {
            "matchid": 123,
            "hemmalagid": 10,
            "bortalagid": None
        }
        
        # Mock players response
        mock_get_players.return_value = []
        
        # Call fetch_match_players_json
        result = client.fetch_match_players_json(123)
        
        # Should be called once for home team
        assert mock_get_players.call_count == 1
        mock_get_players.assert_called_with(123, 10)
        
        # Verify result structure
        assert "hemmalag" in result
        assert "bortalag" not in result
