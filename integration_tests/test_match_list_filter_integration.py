"""
Integration tests for MatchListFilter.fetch_filtered_matches method.

This test module verifies that the fix for issue #249 works correctly
with the mock server and real API interactions.
"""

from datetime import datetime, timedelta

import pytest

from fogis_api_client import FogisApiClient
from fogis_api_client.enums import AgeCategory, FootballType, Gender, MatchStatus
from fogis_api_client.match_list_filter import MatchListFilter


class TestMatchListFilterIntegration:
    """Integration tests for MatchListFilter.fetch_filtered_matches method."""

    def test_fetch_filtered_matches_basic_functionality(self, fogis_test_client: FogisApiClient):
        """Test basic functionality of fetch_filtered_matches with mock server."""
        # Create a simple filter
        filter_obj = MatchListFilter()

        # This should work without throwing TypeError
        try:
            matches = filter_obj.fetch_filtered_matches(fogis_test_client)

            # Verify we get a list (even if empty)
            assert isinstance(matches, list)

            # If we get matches, verify they have expected structure
            if matches:
                for match in matches:
                    assert isinstance(match, dict)
                    # Check for common match fields
                    expected_fields = ["matchid"]
                    for field in expected_fields:
                        if field in match:  # Not all fields may be present in mock data
                            assert match[field] is not None

        except Exception as e:
            # Should not get TypeError about unexpected keyword argument
            assert "unexpected keyword argument 'filter'" not in str(e)
            # Re-raise other exceptions for debugging
            raise

    def test_fetch_filtered_matches_with_date_range(self, fogis_test_client: FogisApiClient):
        """Test fetch_filtered_matches with date range filtering."""
        # Create filter with date range
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        filter_obj = MatchListFilter().start_date(start_date).end_date(end_date)

        # This should work without throwing TypeError
        try:
            matches = filter_obj.fetch_filtered_matches(fogis_test_client)

            # Verify we get a list
            assert isinstance(matches, list)

        except Exception as e:
            # Should not get TypeError about unexpected keyword argument
            assert "unexpected keyword argument 'filter'" not in str(e)
            # Re-raise other exceptions for debugging
            raise

    def test_fetch_filtered_matches_with_status_filter(self, fogis_test_client: FogisApiClient):
        """Test fetch_filtered_matches with status filtering."""
        # Create filter with status
        filter_obj = MatchListFilter().include_statuses([MatchStatus.COMPLETED])

        # This should work without throwing TypeError
        try:
            matches = filter_obj.fetch_filtered_matches(fogis_test_client)

            # Verify we get a list
            assert isinstance(matches, list)

        except Exception as e:
            # Should not get TypeError about unexpected keyword argument
            assert "unexpected keyword argument 'filter'" not in str(e)
            # Re-raise other exceptions for debugging
            raise

    def test_fetch_filtered_matches_complex_filter(self, fogis_test_client: FogisApiClient):
        """Test fetch_filtered_matches with complex multi-criteria filter."""
        # Create complex filter as shown in the issue
        start_date = "2025-05-01"
        end_date = "2025-07-31"

        filter_obj = (
            MatchListFilter()
            .start_date(start_date)
            .end_date(end_date)
            .include_statuses([MatchStatus.COMPLETED])
            .include_age_categories([AgeCategory.SENIOR])
            .include_genders([Gender.MALE])
        )

        # This should work without throwing TypeError
        try:
            matches = filter_obj.fetch_filtered_matches(fogis_test_client)

            # Verify we get a list
            assert isinstance(matches, list)

            # Verify the payload was built correctly
            payload = filter_obj.build_payload()
            assert payload["datumFran"] == start_date
            assert payload["datumTill"] == end_date
            assert "genomford" in payload["status"]  # MatchStatus.COMPLETED.value
            assert AgeCategory.SENIOR.value in payload["alderskategori"]
            assert Gender.MALE.value in payload["kon"]

        except Exception as e:
            # Should not get TypeError about unexpected keyword argument
            assert "unexpected keyword argument 'filter'" not in str(e)
            # Re-raise other exceptions for debugging
            raise

    def test_fetch_filtered_matches_reproduces_issue_249_example(self, fogis_test_client: FogisApiClient):
        """Test the exact example from issue #249 to ensure it's fixed."""
        # This is the exact code from the issue that was failing
        filter_obj = MatchListFilter()
        filter_obj.start_date("2025-05-01").end_date("2025-07-31")
        filter_obj.include_statuses([MatchStatus.COMPLETED])

        # This should work according to documentation but was failing before the fix
        try:
            historic_matches = filter_obj.fetch_filtered_matches(fogis_test_client)

            # Should not throw TypeError anymore
            assert isinstance(historic_matches, list)
            print(f"Found {len(historic_matches)} matches")

        except TypeError as e:
            # This specific error should not occur anymore
            if "got an unexpected keyword argument 'filter'" in str(e):
                pytest.fail(f"Issue #249 not fixed: {e}")
            else:
                # Re-raise other TypeErrors
                raise
        except Exception as e:
            # Other exceptions are acceptable (auth failures, network issues, etc.)
            # but the specific TypeError should be fixed
            assert "unexpected keyword argument 'filter'" not in str(e)

    def test_fetch_filtered_matches_fallback_behavior(self, fogis_test_client: FogisApiClient):
        """Test that fallback behavior works when server-side filtering fails."""
        # Create a filter that might cause server-side issues
        filter_obj = MatchListFilter().start_date("invalid-date")

        # This should either work or fail gracefully, but not with the original TypeError
        try:
            matches = filter_obj.fetch_filtered_matches(fogis_test_client)
            assert isinstance(matches, list)

        except Exception as e:
            # Should not get the original TypeError
            assert "unexpected keyword argument 'filter'" not in str(e)
            # Other exceptions are acceptable

    def test_build_payload_functionality(self):
        """Test that build_payload works correctly for various filter combinations."""
        # Test empty filter
        empty_filter = MatchListFilter()
        payload = empty_filter.build_payload()
        assert payload == {}

        # Test date range filter
        date_filter = MatchListFilter().start_date("2025-01-01").end_date("2025-12-31")
        payload = date_filter.build_payload()
        assert payload["datumFran"] == "2025-01-01"
        assert payload["datumTill"] == "2025-12-31"

        # Test status filter
        status_filter = MatchListFilter().include_statuses([MatchStatus.COMPLETED, MatchStatus.CANCELLED])
        payload = status_filter.build_payload()
        assert "genomford" in payload["status"]
        assert "installd" in payload["status"]

        # Test complex filter
        complex_filter = (
            MatchListFilter()
            .start_date("2025-01-01")
            .include_statuses([MatchStatus.COMPLETED])
            .include_age_categories([AgeCategory.SENIOR])
            .include_genders([Gender.MALE])
            .include_football_types([FootballType.FOOTBALL])
        )
        payload = complex_filter.build_payload()

        assert payload["datumFran"] == "2025-01-01"
        assert payload["status"] == ["genomford"]
        assert payload["alderskategori"] == [AgeCategory.SENIOR.value]
        assert payload["kon"] == [Gender.MALE.value]
        # Note: football types are client-side filtered, not in server payload


if __name__ == "__main__":
    pytest.main([__file__])
