"""
Integration tests for match result reporting.

These tests verify that the match result reporting functionality works correctly
and that the client sends the correct data structure to the API.
"""
import logging
from typing import Dict, cast

import pytest
import requests

from fogis_api_client import FogisApiClient, FogisAPIRequestError
from fogis_api_client.types import MatchResultDict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestMatchResultReporting:
    """Integration tests for match result reporting."""

    def test_report_match_result_flat_format(self, mock_fogis_server: Dict[str, str], test_credentials: Dict[str, str]):
        """Test reporting match results using the flat format."""
        # Override the base URL to use the mock server
        FogisApiClient.BASE_URL = f"{mock_fogis_server['base_url']}/mdk"

        # Create a client with test credentials
        client = FogisApiClient(
            username=test_credentials["username"],
            password=test_credentials["password"],
        )

        # Create match result data in flat format
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

        # Report the match result
        response = client.report_match_result(result_data)

        # Verify the response
        assert isinstance(response, dict)
        assert "success" in response
        assert response["success"] is True

    def test_report_match_result_nested_format(self, mock_fogis_server: Dict[str, str], test_credentials: Dict[str, str]):
        """Test reporting match results using the nested format."""
        # Override the base URL to use the mock server
        FogisApiClient.BASE_URL = f"{mock_fogis_server['base_url']}/mdk"

        # Create a client with test credentials
        client = FogisApiClient(
            username=test_credentials["username"],
            password=test_credentials["password"],
        )

        # Create match result data in nested format
        match_id = 12345
        result_data = {
            "matchresultatListaJSON": [
                {
                    "matchid": match_id,
                    "matchresultattypid": 1,  # Full time
                    "matchlag1mal": 2,
                    "matchlag2mal": 1,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                },
                {
                    "matchid": match_id,
                    "matchresultattypid": 2,  # Half-time
                    "matchlag1mal": 1,
                    "matchlag2mal": 0,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                },
            ]
        }

        # Report the match result
        response = client.report_match_result(result_data)

        # Verify the response
        assert isinstance(response, dict)
        assert "success" in response
        assert response["success"] is True

    def test_report_match_result_missing_fields(self, mock_fogis_server: Dict[str, str], test_credentials: Dict[str, str]):
        """Test reporting match results with missing fields."""
        # Override the base URL to use the mock server
        FogisApiClient.BASE_URL = f"{mock_fogis_server['base_url']}/mdk"

        # Create a client with test credentials
        client = FogisApiClient(
            username=test_credentials["username"],
            password=test_credentials["password"],
        )

        # Create invalid match result data (missing required fields)
        result_data = {
            "matchid": 12345,
            # Missing hemmamal and bortamal
        }

        # Attempt to report the match result and expect failure
        with pytest.raises(ValueError):
            client.report_match_result(result_data)

    def test_report_match_result_invalid_nested_format(
        self, mock_fogis_server: Dict[str, str], test_credentials: Dict[str, str]
    ):
        """Test reporting match results with invalid nested format."""
        # Override the base URL to use the mock server
        FogisApiClient.BASE_URL = f"{mock_fogis_server['base_url']}/mdk"

        # Create a client with test credentials
        client = FogisApiClient(
            username=test_credentials["username"],
            password=test_credentials["password"],
        )

        # Create invalid match result data (missing required fields in nested structure)
        result_data = {
            "matchresultatListaJSON": [
                {
                    "matchid": 12345,
                    # Missing matchresultattypid, matchlag1mal, matchlag2mal
                    "wo": False,
                    "ow": False,
                    "ww": False,
                }
            ]
        }

        # Attempt to report the match result and expect failure
        with pytest.raises(FogisAPIRequestError):
            client.report_match_result(result_data)

    def test_report_match_result_with_extra_time(self, mock_fogis_server: Dict[str, str], test_credentials: Dict[str, str]):
        """Test reporting match results with extra time."""
        # Override the base URL to use the mock server
        FogisApiClient.BASE_URL = f"{mock_fogis_server['base_url']}/mdk"

        # Create a client with test credentials
        client = FogisApiClient(
            username=test_credentials["username"],
            password=test_credentials["password"],
        )

        # Create match result data with extra time
        match_id = 12345
        result_data = {
            "matchresultatListaJSON": [
                {
                    "matchid": match_id,
                    "matchresultattypid": 1,  # Full time
                    "matchlag1mal": 2,
                    "matchlag2mal": 2,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                },
                {
                    "matchid": match_id,
                    "matchresultattypid": 2,  # Half-time
                    "matchlag1mal": 1,
                    "matchlag2mal": 1,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                },
                {
                    "matchid": match_id,
                    "matchresultattypid": 3,  # Extra time
                    "matchlag1mal": 3,
                    "matchlag2mal": 2,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                },
            ]
        }

        # Report the match result
        response = client.report_match_result(result_data)

        # Verify the response
        assert isinstance(response, dict)
        assert "success" in response
        assert response["success"] is True

    def test_report_match_result_with_penalties(self, mock_fogis_server: Dict[str, str], test_credentials: Dict[str, str]):
        """Test reporting match results with penalties."""
        # Override the base URL to use the mock server
        FogisApiClient.BASE_URL = f"{mock_fogis_server['base_url']}/mdk"

        # Create a client with test credentials
        client = FogisApiClient(
            username=test_credentials["username"],
            password=test_credentials["password"],
        )

        # Create match result data with penalties
        match_id = 12345
        result_data = {
            "matchresultatListaJSON": [
                {
                    "matchid": match_id,
                    "matchresultattypid": 1,  # Full time
                    "matchlag1mal": 2,
                    "matchlag2mal": 2,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                },
                {
                    "matchid": match_id,
                    "matchresultattypid": 2,  # Half-time
                    "matchlag1mal": 1,
                    "matchlag2mal": 1,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                },
                {
                    "matchid": match_id,
                    "matchresultattypid": 3,  # Extra time
                    "matchlag1mal": 3,
                    "matchlag2mal": 3,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                },
                {
                    "matchid": match_id,
                    "matchresultattypid": 4,  # Penalties
                    "matchlag1mal": 5,
                    "matchlag2mal": 4,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                },
            ]
        }

        # Report the match result
        response = client.report_match_result(result_data)

        # Verify the response
        assert isinstance(response, dict)
        assert "success" in response
        assert response["success"] is True

    def test_report_match_result_walkover(self, mock_fogis_server: Dict[str, str], test_credentials: Dict[str, str]):
        """Test reporting match results with walkover."""
        # Override the base URL to use the mock server
        FogisApiClient.BASE_URL = f"{mock_fogis_server['base_url']}/mdk"

        # Create a client with test credentials
        client = FogisApiClient(
            username=test_credentials["username"],
            password=test_credentials["password"],
        )

        # Create match result data with walkover
        match_id = 12345
        result_data = {
            "matchresultatListaJSON": [
                {
                    "matchid": match_id,
                    "matchresultattypid": 1,  # Full time
                    "matchlag1mal": 3,
                    "matchlag2mal": 0,
                    "wo": True,  # Walkover
                    "ow": False,
                    "ww": False,
                }
            ]
        }

        # Report the match result
        response = client.report_match_result(result_data)

        # Verify the response
        assert isinstance(response, dict)
        assert "success" in response
        assert response["success"] is True

    def test_complete_match_reporting_workflow(self, mock_fogis_server: Dict[str, str], test_credentials: Dict[str, str]):
        """Test the complete match reporting workflow."""
        # Override the base URL to use the mock server
        FogisApiClient.BASE_URL = f"{mock_fogis_server['base_url']}/mdk"

        # Create a client with test credentials
        client = FogisApiClient(
            username=test_credentials["username"],
            password=test_credentials["password"],
        )

        # Clear request history before starting the test
        requests.post(f"{mock_fogis_server['base_url']}/clear-request-history")

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
        result_response = client.report_match_result(result_data)
        assert result_response["success"] is True

        # 2. Mark reporting as finished
        finish_response = client.mark_reporting_finished(match_id)
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
        self, mock_fogis_server: Dict[str, str], test_credentials: Dict[str, str]
    ):
        """Test that verifies the structure of requests with extra time and penalties."""
        # Override the base URL to use the mock server
        FogisApiClient.BASE_URL = f"{mock_fogis_server['base_url']}/mdk"

        # Create a client with test credentials
        client = FogisApiClient(
            username=test_credentials["username"],
            password=test_credentials["password"],
        )

        # Clear request history before starting the test
        requests.post(f"{mock_fogis_server['base_url']}/clear-request-history")

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

        # The client should convert the flat format to the nested format with all result types
        assert "matchresultatListaJSON" in request_data
        assert isinstance(request_data["matchresultatListaJSON"], list)
        assert len(request_data["matchresultatListaJSON"]) == 4  # Full time, half time, extra time, penalties

        # Check the full time result
        full_time = next(r for r in request_data["matchresultatListaJSON"] if r["matchresultattypid"] == 1)
        assert full_time["matchid"] == match_id
        assert full_time["matchlag1mal"] == 2
        assert full_time["matchlag2mal"] == 2

        # Check the half time result
        half_time = next(r for r in request_data["matchresultatListaJSON"] if r["matchresultattypid"] == 2)
        assert half_time["matchid"] == match_id
        assert half_time["matchlag1mal"] == 1
        assert half_time["matchlag2mal"] == 1

        # Check the extra time result
        extra_time = next(r for r in request_data["matchresultatListaJSON"] if r["matchresultattypid"] == 3)
        assert extra_time["matchid"] == match_id
        assert extra_time["matchlag1mal"] == 3
        assert extra_time["matchlag2mal"] == 3

        # Check the penalties result
        penalties = next(r for r in request_data["matchresultatListaJSON"] if r["matchresultattypid"] == 4)
        assert penalties["matchid"] == match_id
        assert penalties["matchlag1mal"] == 5
        assert penalties["matchlag2mal"] == 4
