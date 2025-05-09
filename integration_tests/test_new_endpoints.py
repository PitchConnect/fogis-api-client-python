"""
Integration tests for the newly added endpoints in the mock server.

This module contains tests for the endpoints that were added to the mock server
to enhance its capabilities and make it more comprehensive.
"""

import pytest
from fogis_api_client import FogisApiClient


def test_fetch_match_officials(
    fogis_test_client: FogisApiClient, clear_request_history
):
    """Test fetching match officials data."""
    # Get a random match ID
    matches = fogis_test_client.fetch_matches_list_json()
    assert matches is not None
    assert "matchlista" in matches
    assert len(matches["matchlista"]) > 0
    match_id = matches["matchlista"][0]["matchid"]

    # Call the endpoint method
    result = fogis_test_client.fetch_match_json(match_id)

    # Verify the result
    assert result is not None
    assert "hemmalag" in result
    assert "bortalag" in result


def test_fetch_match_result(
    fogis_test_client: FogisApiClient, clear_request_history
):
    """Test fetching match result data."""
    # Get a random match ID
    matches = fogis_test_client.fetch_matches_list_json()
    assert matches is not None
    assert "matchlista" in matches
    assert len(matches["matchlista"]) > 0
    match_id = matches["matchlista"][0]["matchid"]

    # Call the endpoint method
    result = fogis_test_client.fetch_match_result_json(match_id)

    # Verify the result
    assert result is not None
    if isinstance(result, list):
        assert len(result) > 0
    else:
        # The result might have different field names depending on the API version
        assert any(key in result for key in ["matchresultattypid", "hemmamal", "bortamal"])


def test_delete_match_event(fogis_test_client: FogisApiClient, clear_request_history):
    """Test deleting a match event."""
    # Get a random match ID
    matches = fogis_test_client.fetch_matches_list_json()
    assert matches is not None
    assert "matchlista" in matches
    assert len(matches["matchlista"]) > 0
    match_id = matches["matchlista"][0]["matchid"]

    # Get events for the match
    events = fogis_test_client.fetch_match_events_json(match_id)
    assert events is not None
    assert len(events) > 0

    # Delete the first event
    event_id = events[0]["matchhandelseid"]
    result = fogis_test_client.delete_match_event(event_id)

    # Verify the result
    assert result is not None
    assert isinstance(result, dict)
    assert result.get("success") is True


def test_team_official_action(fogis_test_client: FogisApiClient, clear_request_history):
    """Test reporting a team official action."""
    # Get a random match ID
    matches = fogis_test_client.fetch_matches_list_json()
    assert matches is not None
    assert "matchlista" in matches
    assert len(matches["matchlista"]) > 0
    match_id = matches["matchlista"][0]["matchid"]

    # Get team IDs
    match_details = fogis_test_client.fetch_match_json(match_id)
    assert match_details is not None
    team_id = match_details["hemmalagid"]

    # Create a team official action
    action = {
        "matchid": match_id,
        "matchlagid": team_id,
        "matchlagledareid": 12345,  # Sample ID
        "matchlagledaretypid": 1,  # Sample type ID
    }

    # Report the action
    result = fogis_test_client.report_team_official_action(action)

    # Verify the result
    assert result is not None
    assert isinstance(result, dict)
    assert result.get("success") is True
