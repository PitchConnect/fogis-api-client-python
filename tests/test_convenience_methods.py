"""
Tests for convenience methods in PublicApiClient.

This module tests the new convenience methods that provide a more intuitive
and user-friendly API interface for common operations.
"""

import warnings
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from fogis_api_client.public_api_client import FogisAPIRequestError, PublicApiClient


class TestConvenienceMethods:
    """Test class for convenience methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = PublicApiClient(username="test", password="test")
        self.client.authentication_method = "oauth"  # Mock authentication

        # Mock sample match data
        self.sample_match = {
            "matchid": 123456,
            "lag1namn": "Home Team",
            "lag2namn": "Away Team",
            "datum": "2025-01-15",
            "tid": "19:00",
            "anlaggningnamn": "Test Arena",
            "status": "klar",
            "serienamn": "Test League",
            "lag1resultat": 2,
            "lag2resultat": 1,
            "matchlag1id": 111,
            "matchlag2id": 222,
            "domaruppdraglista": ["referee1"],
        }

        self.sample_events = [
            {"typ": "mål", "namn": "Goal", "lag": "Home Team"},
            {"typ": "kort", "namn": "Yellow card", "lag": "Away Team"},
            {"typ": "byte", "namn": "Substitution", "lag": "Home Team"},
        ]

    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_details")
    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_players")
    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_officials")
    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_events_json")
    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_result_json")
    def test_fetch_complete_match_success(self, mock_result, mock_events, mock_officials, mock_players, mock_details):
        """Test successful complete match fetch."""
        # Mock all the underlying methods
        mock_details.return_value = self.sample_match
        mock_players.return_value = {"home": [{"name": "Player1"}], "away": [{"name": "Player2"}]}
        mock_officials.return_value = {"home": [{"name": "Coach1"}], "away": [{"name": "Coach2"}]}
        mock_events.return_value = self.sample_events
        mock_result.return_value = {"home_score": 2, "away_score": 1}

        # Test the method
        result = self.client.fetch_complete_match(123456)

        # Verify structure
        assert result["match_id"] == 123456
        assert result["match_details"] == self.sample_match
        assert result["players"]["home"][0]["name"] == "Player1"
        assert result["officials"]["home"][0]["name"] == "Coach1"
        assert result["events"] == self.sample_events
        assert result["result"]["home_score"] == 2

        # Verify metadata
        assert result["metadata"]["include_optional"] is True
        assert len(result["metadata"]["success"]) == 5  # All endpoints successful
        assert len(result["metadata"]["errors"]) == 0
        assert len(result["metadata"]["warnings"]) == 0

    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_details")
    def test_fetch_complete_match_critical_failure(self, mock_details):
        """Test complete match fetch when critical data fails."""
        # Mock critical failure
        mock_details.side_effect = FogisAPIRequestError("Match not found")

        # Should raise exception for critical failure
        with pytest.raises(FogisAPIRequestError, match="Failed to fetch critical match details"):
            self.client.fetch_complete_match(123456)

    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_details")
    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_players")
    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_events_json")
    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_result_json")
    def test_fetch_complete_match_partial_failure(self, mock_result, mock_events, mock_players, mock_details):
        """Test complete match fetch with partial failures."""
        # Mock partial success
        mock_details.return_value = self.sample_match
        mock_events.return_value = self.sample_events
        mock_result.return_value = {"score": "2-1"}
        mock_players.side_effect = FogisAPIRequestError("Players not available")

        # Should succeed with warnings
        result = self.client.fetch_complete_match(123456)

        assert result["match_details"] == self.sample_match
        assert result["events"] == self.sample_events
        assert result["players"] is None
        assert len(result["metadata"]["warnings"]) > 0
        assert "Could not fetch players" in result["metadata"]["warnings"][0]

    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_matches_list_json")
    def test_get_recent_matches(self, mock_fetch_matches):
        """Test getting recent matches."""
        # Mock matches with different dates
        mock_matches = [
            {**self.sample_match, "datum": "2025-01-10", "matchid": 1},
            {**self.sample_match, "datum": "2025-01-15", "matchid": 2},
            {**self.sample_match, "datum": "2025-01-05", "matchid": 3},
        ]
        mock_fetch_matches.return_value = mock_matches

        # Test recent matches
        result = self.client.get_recent_matches(days=30)

        # Should be sorted by date (newest first)
        assert len(result) == 3
        assert result[0]["matchid"] == 2  # 2025-01-15
        assert result[1]["matchid"] == 1  # 2025-01-10
        assert result[2]["matchid"] == 3  # 2025-01-05

        # Verify filter parameters were used
        call_args = mock_fetch_matches.call_args[0][0]
        assert "datumFran" in call_args
        assert "datumTill" in call_args

    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_details")
    def test_get_match_summary(self, mock_details):
        """Test getting match summary."""
        mock_details.return_value = self.sample_match

        result = self.client.get_match_summary(123456)

        # Verify summary structure
        assert result["match_id"] == 123456
        assert result["home_team"] == "Home Team"
        assert result["away_team"] == "Away Team"
        assert result["date"] == "2025-01-15"
        assert result["time"] == "19:00"
        assert result["venue"] == "Test Arena"
        assert result["status"] == "klar"
        assert result["final_score"] == "2-1"
        assert result["match_completed"] is True
        assert result["referee_assigned"] is True

    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_events_json")
    def test_get_match_events_by_type(self, mock_events):
        """Test getting events organized by type."""
        mock_events.return_value = self.sample_events

        result = self.client.get_match_events_by_type(123456)

        # Verify categorization
        assert len(result["goals"]) == 1
        assert len(result["cards"]) == 1
        assert len(result["substitutions"]) == 1
        assert len(result["other"]) == 0

        # Test filtering by specific type
        goals_only = self.client.get_match_events_by_type(123456, event_type="goals")
        assert "goals" in goals_only
        assert len(goals_only["goals"]) == 1

    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_details")
    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_players")
    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_events_by_type")
    def test_get_team_statistics(self, mock_events_by_type, mock_players, mock_details):
        """Test getting team statistics."""
        mock_details.return_value = self.sample_match
        mock_players.return_value = {"home": [{"name": "Player1"}, {"name": "Player2"}], "away": [{"name": "Player3"}]}
        mock_events_by_type.return_value = {
            "goals": [{"lag": "Home Team"}],
            "cards": [{"lag": "Away Team"}],
            "substitutions": [],
        }

        result = self.client.get_team_statistics(123456)

        # Verify statistics structure
        assert result["home"]["team_name"] == "Home Team"
        assert result["home"]["player_count"] == 2
        assert result["home"]["goals"] == 1
        assert result["home"]["cards"] == 0

        assert result["away"]["team_name"] == "Away Team"
        assert result["away"]["player_count"] == 1
        assert result["away"]["goals"] == 0
        assert result["away"]["cards"] == 1

    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_matches_list_json")
    def test_find_matches(self, mock_fetch_matches):
        """Test finding matches with criteria."""
        mock_matches = [
            {**self.sample_match, "lag1namn": "IFK Göteborg", "serienamn": "Allsvenskan"},
            {**self.sample_match, "lag2namn": "IFK Malmö", "serienamn": "Superettan"},
            {**self.sample_match, "lag1namn": "AIK", "serienamn": "Allsvenskan"},
        ]
        mock_fetch_matches.return_value = mock_matches

        # Test team name filter
        result = self.client.find_matches(team_name="IFK")
        assert len(result) == 2

        # Test competition filter
        result = self.client.find_matches(competition="Allsvenskan")
        assert len(result) == 2

        # Test limit
        result = self.client.find_matches(limit=1)
        assert len(result) == 1

    @patch("fogis_api_client.public_api_client.PublicApiClient.fetch_matches_list_json")
    def test_get_matches_requiring_action(self, mock_fetch_matches):
        """Test getting matches requiring action."""
        today = datetime.now()
        future_date = (today + timedelta(days=5)).strftime("%Y-%m-%d")
        past_date = (today - timedelta(days=2)).strftime("%Y-%m-%d")

        mock_matches = [
            {**self.sample_match, "datum": future_date, "status": "ej_pabörjad", "matchid": 1},
            {**self.sample_match, "datum": past_date, "status": "klar", "matchid": 2},
            {**self.sample_match, "datum": past_date, "status": "avbruten", "matchid": 3},
        ]
        mock_fetch_matches.return_value = mock_matches

        result = self.client.get_matches_requiring_action()

        # Verify categorization
        assert len(result["upcoming"]) == 1
        assert result["upcoming"][0]["matchid"] == 1
        assert len(result["recently_completed"]) == 1
        assert result["recently_completed"][0]["matchid"] == 2
        assert len(result["cancelled"]) == 1
        assert result["cancelled"][0]["matchid"] == 3


class TestDeprecationWarnings:
    """Test deprecation warnings for backward compatibility methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = PublicApiClient(username="test", password="test")
        self.client.authentication_method = "oauth"

    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_details")
    def test_fetch_match_json_deprecation(self, mock_details):
        """Test deprecation warning for fetch_match_json."""
        mock_details.return_value = {"matchid": 123456}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.client.fetch_match_json(123456)

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message)
            assert "get_match_details" in str(w[0].message)

    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_players")
    def test_fetch_match_players_json_deprecation(self, mock_players):
        """Test deprecation warning for fetch_match_players_json."""
        mock_players.return_value = {"home": [], "away": []}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = self.client.fetch_match_players_json(123456)

            # Should return legacy format
            assert "hemmalag" in result
            assert "bortalag" in result

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "get_match_players" in str(w[0].message)

    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_officials")
    @patch("fogis_api_client.public_api_client.PublicApiClient.get_match_details")
    def test_fetch_match_officials_json_deprecation(self, mock_details, mock_officials):
        """Test deprecation warning for fetch_match_officials_json."""
        mock_officials.return_value = {"home": [], "away": []}
        mock_details.return_value = {"domaruppdraglista": []}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = self.client.fetch_match_officials_json(123456)

            # Should return legacy format
            assert "hemmalag" in result
            assert "bortalag" in result
            assert "domare" in result

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "get_match_officials" in str(w[0].message)
