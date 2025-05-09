"""
Integration tests for the newly added endpoints in the mock server.

This module contains tests for the endpoints that were added to the mock server
to enhance its capabilities and make it more comprehensive.
"""

import pytest
from fogis_api_client import FogisApiClient


@pytest.mark.parametrize(
    "endpoint_method,expected_fields",
    [
        (
            "fetch_match_officials_json",
            ["hemmalag", "bortalag", "hemmalagid", "bortalagid", "matchid", "funktionarer"],
        ),
        (
            "fetch_match_result_list_json",
            ["hemmalag", "bortalag", "hemmalagid", "bortalagid", "matchid", "matchresultattyper", "matchresultat"],
        ),
    ],
    ids=["match_officials", "match_result_list"],
)
def test_fetch_endpoints(
    fogis_test_client: FogisApiClient, clear_request_history, endpoint_method, expected_fields
):
    """Test fetching data from the newly added endpoints."""
    # Get a random match ID
    matches = fogis_test_client.fetch_matches_list_json()
    assert matches is not None
    assert "matcher" in matches
    assert len(matches["matcher"]) > 0
    match_id = matches["matcher"][0]["matchid"]

    # Call the endpoint method
    method = getattr(fogis_test_client, endpoint_method)
    result = method(match_id)

    # Verify the result
    assert result is not None
    for field in expected_fields:
        assert field in result, f"Field '{field}' not found in result"


def test_delete_match_event(fogis_test_client: FogisApiClient, clear_request_history):
    """Test deleting a match event."""
    # Get a random match ID
    matches = fogis_test_client.fetch_matches_list_json()
    assert matches is not None
    assert "matcher" in matches
    assert len(matches["matcher"]) > 0
    match_id = matches["matcher"][0]["matchid"]

    # Get events for the match
    events = fogis_test_client.fetch_match_events_json(match_id)
    assert events is not None
    assert len(events) > 0

    # Delete the first event
    event_id = events[0]["matchhandelseid"]
    result = fogis_test_client.delete_match_event(event_id)

    # Verify the result
    assert result is True


def test_team_official_action(fogis_test_client: FogisApiClient, clear_request_history):
    """Test reporting a team official action."""
    # Get a random match ID
    matches = fogis_test_client.fetch_matches_list_json()
    assert matches is not None
    assert "matcher" in matches
    assert len(matches["matcher"]) > 0
    match_id = matches["matcher"][0]["matchid"]

    # Get team IDs
    match_details = fogis_test_client.fetch_match_json(match_id)
    assert match_details is not None
    team_id = match_details["hemmalagid"]

    # Create a team official action
    action = {
        "matchlagid": team_id,
        "personid": 12345,  # Sample person ID
        "roll": "Tränare",  # Role (e.g., Coach)
    }

    # Report the action
    result = fogis_test_client.report_team_official_action(action)

    # Verify the result
    assert result is True
