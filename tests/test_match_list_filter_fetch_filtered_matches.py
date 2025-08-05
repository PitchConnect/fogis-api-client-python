"""
Tests for MatchListFilter.fetch_filtered_matches method.

This test module specifically focuses on testing the fetch_filtered_matches method
that was fixed in issue #249 to resolve the TypeError when calling the API.
"""

import unittest
from unittest.mock import MagicMock

from fogis_api_client import FogisApiClient
from fogis_api_client.enums import AgeCategory, FootballType, Gender, MatchStatus
from fogis_api_client.match_list_filter import MatchListFilter
from fogis_api_client.public_api_client import FogisAPIRequestError


class TestMatchListFilterFetchFilteredMatches(unittest.TestCase):
    """Test cases for MatchListFilter.fetch_filtered_matches method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock(spec=FogisApiClient)
        self.sample_matches = [
            {
                "matchid": 1001,
                "hemmalag": "Team A",
                "bortalag": "Team B",
                "datum": "2025-05-15",
                "tid": "19:00",
                "installd": False,
                "avbruten": False,
                "uppskjuten": False,
                "arslutresultat": True,  # Completed match
                "tavlingAlderskategori": AgeCategory.SENIOR.value,
                "tavlingKonId": Gender.MALE.value,
                "fotbollstypid": FootballType.FOOTBALL.value,
            },
            {
                "matchid": 1002,
                "hemmalag": "Team C",
                "bortalag": "Team D",
                "datum": "2025-06-01",
                "tid": "15:00",
                "installd": False,
                "avbruten": False,
                "uppskjuten": False,
                "arslutresultat": False,  # Not completed
                "tavlingAlderskategori": AgeCategory.YOUTH.value,
                "tavlingKonId": Gender.FEMALE.value,
                "fotbollstypid": FootballType.FUTSAL.value,
            },
        ]

    def test_fetch_filtered_matches_with_correct_parameter_name(self):
        """Test that fetch_filtered_matches calls API with correct parameter name."""
        # Setup
        filter_obj = MatchListFilter().start_date("2025-05-01").end_date("2025-07-31")

        # Mock the API response with matchlista format
        mock_response = {"matchlista": self.sample_matches}
        self.mock_client.fetch_matches_list_json.return_value = mock_response

        # Execute
        result = filter_obj.fetch_filtered_matches(self.mock_client)

        # Verify
        self.mock_client.fetch_matches_list_json.assert_called_once_with(
            filter_params={"datumFran": "2025-05-01", "datumTill": "2025-07-31"}
        )
        self.assertEqual(result, self.sample_matches)

    def test_fetch_filtered_matches_with_status_filter(self):
        """Test fetch_filtered_matches with status filtering."""
        # Setup
        filter_obj = MatchListFilter().include_statuses([MatchStatus.COMPLETED])

        # Mock the API response
        mock_response = {"matchlista": self.sample_matches}
        self.mock_client.fetch_matches_list_json.return_value = mock_response

        # Execute
        result = filter_obj.fetch_filtered_matches(self.mock_client)

        # Verify - should only return completed matches
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["matchid"], 1001)
        self.assertTrue(result[0]["arslutresultat"])

    def test_fetch_filtered_matches_handles_list_response(self):
        """Test that fetch_filtered_matches handles direct list response."""
        # Setup
        filter_obj = MatchListFilter()

        # Mock the API response as a direct list
        self.mock_client.fetch_matches_list_json.return_value = self.sample_matches

        # Execute
        result = filter_obj.fetch_filtered_matches(self.mock_client)

        # Verify
        self.assertEqual(result, self.sample_matches)

    def test_fetch_filtered_matches_handles_none_response(self):
        """Test that fetch_filtered_matches handles None response gracefully."""
        # Setup
        filter_obj = MatchListFilter()

        # Mock the API response as None
        self.mock_client.fetch_matches_list_json.return_value = None

        # Execute
        result = filter_obj.fetch_filtered_matches(self.mock_client)

        # Verify
        self.assertEqual(result, [])

    def test_fetch_filtered_matches_handles_empty_dict_response(self):
        """Test that fetch_filtered_matches handles empty dict response."""
        # Setup
        filter_obj = MatchListFilter()

        # Mock the API response as empty dict
        self.mock_client.fetch_matches_list_json.return_value = {}

        # Execute
        result = filter_obj.fetch_filtered_matches(self.mock_client)

        # Verify
        self.assertEqual(result, [])

    def test_fetch_filtered_matches_fallback_on_server_side_failure(self):
        """Test that fetch_filtered_matches falls back to basic fetch on server-side failure."""
        # Setup
        filter_obj = MatchListFilter().start_date("2025-05-01")

        # Mock server-side filtering to fail, but basic fetch to succeed
        self.mock_client.fetch_matches_list_json.side_effect = [
            FogisAPIRequestError("Server-side filtering failed"),  # First call fails
            {"matchlista": self.sample_matches},  # Second call (fallback) succeeds
        ]

        # Execute
        result = filter_obj.fetch_filtered_matches(self.mock_client)

        # Verify
        self.assertEqual(len(self.mock_client.fetch_matches_list_json.call_args_list), 2)
        # First call should have filter_params
        first_call = self.mock_client.fetch_matches_list_json.call_args_list[0]
        self.assertIn("filter_params", first_call.kwargs)
        # Second call should have no parameters (fallback)
        second_call = self.mock_client.fetch_matches_list_json.call_args_list[1]
        self.assertEqual(len(second_call.args), 0)
        self.assertEqual(len(second_call.kwargs), 0)

        self.assertEqual(result, self.sample_matches)

    def test_fetch_filtered_matches_raises_on_complete_failure(self):
        """Test that fetch_filtered_matches raises exception when both server-side and fallback fail."""
        # Setup
        filter_obj = MatchListFilter().start_date("2025-05-01")

        # Mock both calls to fail
        self.mock_client.fetch_matches_list_json.side_effect = FogisAPIRequestError("Complete failure")

        # Execute & Verify
        with self.assertRaises(FogisAPIRequestError):
            filter_obj.fetch_filtered_matches(self.mock_client)

    def test_fetch_filtered_matches_complex_filter(self):
        """Test fetch_filtered_matches with complex multi-criteria filter."""
        # Setup
        filter_obj = (
            MatchListFilter()
            .start_date("2025-05-01")
            .end_date("2025-07-31")
            .include_statuses([MatchStatus.COMPLETED])
            .include_age_categories([AgeCategory.SENIOR])
            .include_genders([Gender.MALE])
        )

        # Mock the API response
        mock_response = {"matchlista": self.sample_matches}
        self.mock_client.fetch_matches_list_json.return_value = mock_response

        # Execute
        result = filter_obj.fetch_filtered_matches(self.mock_client)

        # Verify API call with correct payload
        expected_payload = {
            "datumFran": "2025-05-01",
            "datumTill": "2025-07-31",
            "status": ["genomford"],
            "alderskategori": [AgeCategory.SENIOR.value],
            "kon": [Gender.MALE.value],
        }
        self.mock_client.fetch_matches_list_json.assert_called_once_with(filter_params=expected_payload)

        # Verify filtering - should only return matches that meet all criteria
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["matchid"], 1001)

    def test_fetch_filtered_matches_handles_single_match_dict_response(self):
        """Test that fetch_filtered_matches handles single match dict response."""
        # Setup
        filter_obj = MatchListFilter()
        single_match = self.sample_matches[0]

        # Mock the API response as a single match dict (not wrapped in matchlista)
        self.mock_client.fetch_matches_list_json.return_value = single_match

        # Execute
        result = filter_obj.fetch_filtered_matches(self.mock_client)

        # Verify
        self.assertEqual(result, [single_match])


if __name__ == "__main__":
    unittest.main()
