from unittest.mock import MagicMock, patch
import pytest
from fogis_api_client.public_api_client import PublicApiClient, FogisAPIRequestError

class TestIssue316:
    def test_fetch_complete_match_exists(self):
        """Test that fetch_complete_match method exists."""
        client = PublicApiClient(username="test", password="test")
        assert hasattr(client, "fetch_complete_match"), "fetch_complete_match method missing"

    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_matches_list_json")
    def test_get_match_details_uses_filter(self, mock_fetch_matches):
        """Test that get_match_details passes filter parameters to fetch_matches_list_json."""
        client = PublicApiClient(username="test", password="test")
        client.cookies = {"test": "cookie"}
        
        # Mock response
        mock_fetch_matches.return_value = {"matchlista": [{"matchid": 123}]}
        
        # Call get_match_details (assuming it exists or will exist)
        if hasattr(client, "get_match_details"):
            client.get_match_details(123, filter_params={"test": "filter"})
            mock_fetch_matches.assert_called_with({"test": "filter"})
        else:
            pytest.fail("get_match_details method missing")

    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_details")
    def test_fetch_complete_match_passes_filter(self, mock_get_match_details):
        """Test that fetch_complete_match passes filter parameters to get_match_details."""
        client = PublicApiClient(username="test", password="test")
        client.cookies = {"test": "cookie"}
        
        mock_get_match_details.return_value = {"matchid": 123}
        
        # Mock other methods called by fetch_complete_match
        with patch.object(client, "fetch_match_players_json", return_value={}), \
             patch.object(client, "fetch_match_events_json", return_value=[]), \
             patch.object(client, "fetch_match_officials_json", return_value={}):
            
            if hasattr(client, "fetch_complete_match"):
                search_filter = {"datumFran": "2020-01-01"}
                client.fetch_complete_match(123, search_filter=search_filter)
                mock_get_match_details.assert_called_with(123, filter_params=search_filter)
            else:
                pytest.fail("fetch_complete_match method missing")
