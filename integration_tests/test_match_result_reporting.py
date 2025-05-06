"""
Integration tests for match result reporting.

These tests verify that the match result reporting functionality works correctly
and that the client sends the correct data structure to the API.
"""
import logging
from typing import Any, Dict, Union, cast

import pytest
import requests

from fogis_api_client import FogisApiClient, FogisAPIRequestError
from fogis_api_client.types import MatchResultDict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestMatchResultReporting:
    """Integration tests for match result reporting."""

    @pytest.mark.parametrize(
        "scenario,result_data,expected_success",
        [
            # Flat format test case
            (
                "flat_format",
                cast(
                    MatchResultDict,
                    {
                        "matchid": 12345,
                        "hemmamal": 2,
                        "bortamal": 1,
                        "halvtidHemmamal": 1,
                        "halvtidBortamal": 0,
                    },
                ),
                True,
            ),
            # Nested format test case
            (
                "nested_format",
                {
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
                },
                True,
            ),
        ],
        ids=["flat_format", "nested_format"],
    )
    def test_report_match_result_formats(
        self,
        fogis_test_client: FogisApiClient,
        clear_request_history,
        scenario: str,
        result_data: Union[Dict[str, Any], MatchResultDict],
        expected_success: bool,
    ):
        """Test reporting match results using different formats."""

        # Report the match result
        response = fogis_test_client.report_match_result(result_data)

        # Verify the response
        assert isinstance(response, dict)
        assert "success" in response
        assert response["success"] is expected_success

    @pytest.mark.parametrize(
        "scenario,result_data,expected_exception",
        [
            # Missing fields test case
            (
                "missing_fields",
                {
                    "matchid": 12345,
                    # Missing hemmamal and bortamal
                },
                ValueError,
            ),
            # Invalid nested format test case
            (
                "invalid_nested_format",
                {
                    "matchresultatListaJSON": [
                        {
                            "matchid": 12345,
                            # Missing matchresultattypid, matchlag1mal, matchlag2mal
                            "wo": False,
                            "ow": False,
                            "ww": False,
                        }
                    ]
                },
                FogisAPIRequestError,
            ),
        ],
        ids=["missing_fields", "invalid_nested_format"],
    )
    def test_report_match_result_error_cases(
        self,
        fogis_test_client: FogisApiClient,
        clear_request_history,
        scenario: str,
        result_data: Dict[str, Any],
        expected_exception: type,
    ):
        """Test reporting match results with error cases."""

        # Attempt to report the match result and expect failure
        with pytest.raises(expected_exception) as excinfo:
            fogis_test_client.report_match_result(result_data)

        # Verify the error message contains useful information
        error_message = str(excinfo.value)

        # Check for specific error information based on the scenario
        if scenario == "missing_fields":
            assert "hemmamal" in error_message.lower() or "bortamal" in error_message.lower(), \
                "Error message should mention the missing fields"
            assert "required" in error_message.lower(), "Error message should indicate fields are required"
            # Enhanced assertion to check for more specific error details
            assert any(term in error_message.lower() for term in ["missing", "field", "parameter"]), \
                "Error message should provide details about what is missing"
        elif scenario == "invalid_nested_format":
            assert "matchresultattypid" in error_message.lower() or "matchlag1mal" in error_message.lower() \
                or "matchlag2mal" in error_message.lower(), "Error message should mention the missing fields"
            assert "required" in error_message.lower(), "Error message should indicate a required field is missing"
            # Enhanced assertion to check for more specific error details
            assert any(term in error_message.lower() for term in ["invalid", "format", "structure", "schema"]), \
                "Error message should provide details about the invalid format"

    @pytest.mark.parametrize(
        "scenario,result_data,expected_success",
        [
            # Extra time test case
            (
                "extra_time",
                {
                    "matchid": 12345,
                    "hemmamal": 3,  # Final result after extra time
                    "bortamal": 2,  # Final result after extra time
                    "halvtidHemmamal": 1,
                    "halvtidBortamal": 1,
                    "fullTimeHemmamal": 2,  # Result after regular time
                    "fullTimeBortamal": 2,  # Result after regular time
                },
                True,
            ),
            # Penalties test case
            (
                "penalties",
                {
                    "matchid": 12345,
                    "hemmamal": 3,  # Final result after extra time
                    "bortamal": 3,  # Final result after extra time
                    "halvtidHemmamal": 1,
                    "halvtidBortamal": 1,
                    "fullTimeHemmamal": 2,  # Result after regular time
                    "fullTimeBortamal": 2,  # Result after regular time
                    "penaltiesHemmamal": 5,  # Result after penalties
                    "penaltiesBortamal": 4,  # Result after penalties
                },
                True,
            ),
            # Walkover test case
            (
                "walkover",
                {
                    "matchresultatListaJSON": [
                        {
                            "matchid": 12345,
                            "matchresultattypid": 1,  # Full time
                            "matchlag1mal": 3,
                            "matchlag2mal": 0,
                            "wo": True,  # Walkover
                            "ow": False,
                            "ww": False,
                        }
                    ]
                },
                True,
            ),
            # Abandoned match test case
            (
                "abandoned_match",
                {
                    "matchresultatListaJSON": [
                        {
                            "matchid": 12345,
                            "matchresultattypid": 1,  # Full time
                            "matchlag1mal": 1,
                            "matchlag2mal": 1,
                            "wo": False,
                            "ow": False,
                            "ww": True,  # Abandoned match
                        }
                    ]
                },
                True,
            ),
            # High score test case
            (
                "high_score",
                {
                    "matchid": 12345,
                    "hemmamal": 10,
                    "bortamal": 0,
                    "halvtidHemmamal": 5,
                    "halvtidBortamal": 0,
                },
                True,
            ),
        ],
        ids=["extra_time", "penalties", "walkover", "abandoned_match", "high_score"],
    )
    def test_report_match_result_special_cases(
        self,
        fogis_test_client: FogisApiClient,
        clear_request_history,
        scenario: str,
        result_data: Union[Dict[str, Any], MatchResultDict],
        expected_success: bool,
    ):
        """Test reporting match results with special cases (extra time, penalties, walkover)."""

        # Report the match result
        response = fogis_test_client.report_match_result(result_data)

        # Verify the response
        assert isinstance(response, dict)
        assert "success" in response
        assert response["success"] is expected_success

    def test_complete_match_reporting_workflow(
        self, mock_fogis_server: Dict[str, str], fogis_test_client: FogisApiClient, clear_request_history
    ):
        """Test the complete match reporting workflow."""

        # Request history is already cleared by the fixture

        # 1. Report match result
        match_id = 12345
        result_data = cast(
            MatchResultDict,
            {
                "matchid": match_id,
                "hemmamal": 2,
                "bortamal": 1,
                "halvtidHemmamal": 1,
                "halvtidBortamal": 0,
            },
        )
        result_response = fogis_test_client.report_match_result(result_data)
        assert result_response["success"] is True

        # 2. Mark reporting as finished
        finish_response = fogis_test_client.mark_reporting_finished(match_id)
        assert finish_response["success"] is True

        # 3. Verify the request structure sent to the API
        history_response = requests.get(f"{mock_fogis_server['base_url']}/request-history")
        history_data = history_response.json()

        # Find the match result request in the history
        match_result_requests = [
            req for req in history_data["history"] if req["endpoint"] == "/MatchWebMetoder.aspx/SparaMatchresultatLista"
        ]

        assert len(match_result_requests) > 0, "No match result request found in history"

        # Verify the structure of the request
        match_result_request = match_result_requests[0]
        request_data = match_result_request["data"]

        # The client should convert the flat format to the nested format
        assert "matchresultatListaJSON" in request_data
        assert isinstance(request_data["matchresultatListaJSON"], list)
        assert len(request_data["matchresultatListaJSON"]) == 2  # Full time and half time

        # Check the full time result
        full_time = next(r for r in request_data["matchresultatListaJSON"] if r["matchresultattypid"] == 1)
        assert full_time["matchid"] == match_id
        assert full_time["matchlag1mal"] == 2
        assert full_time["matchlag2mal"] == 1

        # Check the half time result
        half_time = next(r for r in request_data["matchresultatListaJSON"] if r["matchresultattypid"] == 2)
        assert half_time["matchid"] == match_id
        assert half_time["matchlag1mal"] == 1
        assert half_time["matchlag2mal"] == 0

    def test_verify_request_structure_with_extra_time_and_penalties(
        self, mock_fogis_server: Dict[str, str], test_credentials: Dict[str, str], mock_api_urls, clear_request_history
    ):
        """Test that verifies the structure of requests with extra time and penalties."""

        # Create a client with test credentials
        client = FogisApiClient(
            username=test_credentials["username"],
            password=test_credentials["password"],
        )

        # Request history is already cleared by the fixture

        # Create match result data with extra time and penalties
        match_id = 12345
        result_data = {
            "matchid": match_id,
            "hemmamal": 3,  # Final result after extra time
            "bortamal": 3,  # Final result after extra time
            "halvtidHemmamal": 1,
            "halvtidBortamal": 1,
            "extraTimeHemmamal": 3,  # Result after extra time
            "extraTimeBortamal": 3,  # Result after extra time
            "penaltiesHemmamal": 5,  # Result after penalties
            "penaltiesBortamal": 4,  # Result after penalties
            "fullTimeHemmamal": 2,  # Result after regular time
            "fullTimeBortamal": 2,  # Result after regular time
        }

        # Report the match result
        result_response = client.report_match_result(result_data)
        assert result_response["success"] is True

        # Verify the request structure sent to the API
        history_response = requests.get(f"{mock_fogis_server['base_url']}/request-history")
        history_data = history_response.json()

        # Find the match result request in the history
        match_result_requests = [
            req for req in history_data["history"] if req["endpoint"] == "/MatchWebMetoder.aspx/SparaMatchresultatLista"
        ]

        assert len(match_result_requests) > 0, "No match result request found in history"

        # Verify the structure of the request
        match_result_request = match_result_requests[0]
        request_data = match_result_request["data"]

        # The client should convert the flat format to the nested format
        assert "matchresultatListaJSON" in request_data
        assert isinstance(request_data["matchresultatListaJSON"], list)
        assert len(request_data["matchresultatListaJSON"]) == 2  # Only full time and half time are supported in the API

        # Check the full time result
        full_time = next(r for r in request_data["matchresultatListaJSON"] if r["matchresultattypid"] == 1)
        assert full_time["matchid"] == match_id
        assert full_time["matchlag1mal"] == 3  # Final result after extra time
        assert full_time["matchlag2mal"] == 3  # Final result after extra time

        # Check the half time result
        half_time = next(r for r in request_data["matchresultatListaJSON"] if r["matchresultattypid"] == 2)
        assert half_time["matchid"] == match_id
        assert half_time["matchlag1mal"] == 1
        assert half_time["matchlag2mal"] == 1

        # Note: Extra time and penalties are not sent as separate result types in the API
        # They are only included in the flat format, but the API only supports result types 1 and 2
