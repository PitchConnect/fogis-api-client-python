"""
Tests for Issue #316: Date filter support for fetch_complete_match and get_match_details.

This test file verifies that matches older than 7 days can be fetched when appropriate
filter parameters are provided, fixing the bug where the default 7-day window prevented
access to older matches.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from fogis_api_client.public_api_client import FogisAPIRequestError, PublicApiClient


@pytest.fixture
def mock_client():
    """Create a mock PublicApiClient for testing."""
    with patch("fogis_api_client.public_api_client.PublicApiClient.login"):
        client = PublicApiClient(username="test_user", password="test_pass")
        client.cookies = {"ASP.NET_SessionId": "test_session"}
        return client


@pytest.fixture
def sample_old_match():
    """Sample match data for a match older than 7 days."""
    old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    return {
        "matchid": 123456,
        "lag1namn": "Team A",
        "lag2namn": "Team B",
        "datum": old_date,
        "tid": "19:00",
        "arena": "Test Arena",
        "matchlag1id": 1001,
        "matchlag2id": 1002,
    }


@pytest.fixture
def sample_recent_match():
    """Sample match data for a recent match (within 7 days)."""
    recent_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    return {
        "matchid": 789012,
        "lag1namn": "Team C",
        "lag2namn": "Team D",
        "datum": recent_date,
        "tid": "15:00",
        "arena": "Recent Arena",
        "matchlag1id": 2001,
        "matchlag2id": 2002,
    }


class TestIssue316DateFilter:
    """Test suite for Issue #316: Date filter support."""

    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_matches_list_json")
    def test_get_match_details_with_custom_filter(self, mock_fetch_matches, mock_client, sample_old_match):
        """Test that get_match_details accepts and passes filter_params."""
        # Mock the fetch_matches_list_json to return an old match
        mock_fetch_matches.return_value = [sample_old_match]

        # Call get_match_details with custom filter
        custom_filter = {"datumFran": "2024-01-01", "datumTill": "2024-12-31"}
        result = mock_client.get_match_details(123456, filter_params=custom_filter)

        # Verify the filter was passed through
        mock_fetch_matches.assert_called_once_with(custom_filter)

        # Verify the correct match was returned
        assert result["matchid"] == 123456
        assert result["lag1namn"] == "Team A"

    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_matches_list_json")
    def test_get_match_details_without_filter_uses_default(self, mock_fetch_matches, mock_client, sample_recent_match):
        """Test that get_match_details without filter_params uses default behavior."""
        # Mock the fetch_matches_list_json to return a recent match
        mock_fetch_matches.return_value = [sample_recent_match]

        # Call get_match_details without filter (should use default)
        result = mock_client.get_match_details(789012)

        # Verify no filter was passed (None)
        mock_fetch_matches.assert_called_once_with(None)

        # Verify the correct match was returned
        assert result["matchid"] == 789012
        assert result["lag1namn"] == "Team C"

    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_matches_list_json")
    def test_get_match_details_match_not_found(self, mock_fetch_matches, mock_client):
        """Test that get_match_details raises error when match is not found."""
        # Mock empty match list
        mock_fetch_matches.return_value = []

        # Verify error is raised
        with pytest.raises(FogisAPIRequestError, match="Match with ID 999999 not found"):
            mock_client.get_match_details(999999)

    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_details")
    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_events_json")
    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_result_json")
    def test_fetch_complete_match_with_search_filter(
        self, mock_result, mock_events, mock_details, mock_client, sample_old_match
    ):
        """Test that fetch_complete_match accepts and passes search_filter."""
        # Mock the underlying methods
        mock_details.return_value = sample_old_match
        mock_events.return_value = []
        mock_result.return_value = {"score": "2-1"}

        # Call fetch_complete_match with search_filter
        search_filter = {"datumFran": "2024-01-01", "datumTill": "2024-12-31"}
        result = mock_client.fetch_complete_match(123456, include_optional=False, search_filter=search_filter)

        # Verify the filter was passed to get_match_details
        mock_details.assert_called_once_with(123456, filter_params=search_filter)

        # Verify the result structure
        assert result["match_id"] == 123456
        assert result["match_details"]["matchid"] == 123456
        assert result["metadata"]["success"]["match_details"] is True

    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_details")
    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_events_json")
    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_result_json")
    def test_fetch_complete_match_without_search_filter(
        self, mock_result, mock_events, mock_details, mock_client, sample_recent_match
    ):
        """Test that fetch_complete_match without search_filter uses default behavior."""
        # Mock the underlying methods
        mock_details.return_value = sample_recent_match
        mock_events.return_value = []
        mock_result.return_value = {"score": "1-0"}

        # Call fetch_complete_match without search_filter
        result = mock_client.fetch_complete_match(789012, include_optional=False)

        # Verify no filter was passed to get_match_details (None)
        mock_details.assert_called_once_with(789012, filter_params=None)

        # Verify the result structure
        assert result["match_id"] == 789012
        assert result["match_details"]["matchid"] == 789012
        assert result["metadata"]["success"]["match_details"] is True

    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_matches_list_json")
    def test_old_match_retrieval_scenario(self, mock_fetch_matches, mock_client, sample_old_match):
        """
        Integration test: Simulate the real-world scenario from Issue #316.

        A match played 30 days ago should be retrievable when appropriate
        filter parameters are provided.
        """
        # Simulate the scenario: match is 30 days old
        mock_fetch_matches.return_value = [sample_old_match]

        # Without filter, the match would not be in the default 7-day window
        # (simulated by returning empty list)
        mock_fetch_matches.side_effect = [
            [],  # First call without filter returns empty
            [sample_old_match],  # Second call with filter returns the match
        ]

        # First attempt without filter should fail
        with pytest.raises(FogisAPIRequestError, match="Match with ID 123456 not found"):
            mock_client.get_match_details(123456)

        # Second attempt with custom filter should succeed
        custom_filter = {"datumFran": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")}
        result = mock_client.get_match_details(123456, filter_params=custom_filter)

        assert result["matchid"] == 123456
        assert result["lag1namn"] == "Team A"

    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_matches_list_json")
    def test_filter_params_types(self, mock_fetch_matches, mock_client, sample_old_match):
        """Test that various filter parameter types are handled correctly."""
        mock_fetch_matches.return_value = [sample_old_match]

        # Test with date strings
        filter_with_dates = {"datumFran": "2024-01-01", "datumTill": "2024-12-31"}
        result = mock_client.get_match_details(123456, filter_params=filter_with_dates)
        assert result["matchid"] == 123456

        # Test with additional filter parameters
        complex_filter = {
            "datumFran": "2024-01-01",
            "datumTill": "2024-12-31",
            "typ": "alla",
            "status": ["avbruten", "uppskjuten"],
        }
        result = mock_client.get_match_details(123456, filter_params=complex_filter)
        assert result["matchid"] == 123456

    def test_backward_compatibility(self, mock_client):
        """
        Test that the changes maintain backward compatibility.

        Existing code that doesn't use filter_params should continue to work.
        """
        with patch("fogis_api_client.public_api_client.PublicApiClient.fetch_matches_list_json") as mock_fetch:
            mock_fetch.return_value = [{"matchid": 111, "lag1namn": "A", "lag2namn": "B"}]

            # Old-style call without filter_params
            result = mock_client.get_match_details(111)
            assert result["matchid"] == 111

            # Old-style call to fetch_complete_match
            with patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_events_json") as mock_events:
                with patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_result_json") as mock_result:
                    mock_events.return_value = []
                    mock_result.return_value = {}

                    result = mock_client.fetch_complete_match(111, include_optional=False)
                    assert result["match_id"] == 111
