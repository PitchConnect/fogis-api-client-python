"""
Tests for API compatibility.

These tests verify that the new implementation is compatible with the existing API.
"""
import pytest
from unittest.mock import MagicMock, patch

import requests

from fogis_api_client import FogisApiClient, FogisAPIRequestError, FogisDataError, FogisLoginError


def test_api_compatibility():
    """Test that the new implementation is compatible with the existing API."""
    # Test initialization
    client = FogisApiClient(username="test", password="test")
    assert client.username == "test"
    assert client.password == "test"
    assert client.cookies is None
    # BASE_URL can be overridden by environment variables, so we don't test the exact value

    # Test with cookies
    cookies = {"FogisMobilDomarKlient_ASPXAUTH": "test", "ASP_NET_SessionId": "test"}
    client = FogisApiClient(cookies=cookies)
    assert client.username is None
    assert client.password is None
    assert client.cookies == cookies

    # Test hello_world method
    assert client.hello_world() == "Hello, brave new world!"


@patch("fogis_api_client.public_api_client.PublicApiClient.fetch_matches_list_json")
def test_fetch_matches_list_json_compatibility(mock_fetch_matches_list_json):
    """Test that fetch_matches_list_json is compatible with the existing API."""
    # Mock the fetch_matches_list_json method
    mock_fetch_matches_list_json.return_value = {"matchlista": []}

    # Test with default filter parameters
    client = FogisApiClient(cookies={"FogisMobilDomarKlient_ASPXAUTH": "test"})
    result = client.fetch_matches_list_json()
    assert result == {"matchlista": []}
    mock_fetch_matches_list_json.assert_called_once()

    # Test with custom filter parameters
    mock_fetch_matches_list_json.reset_mock()
    filter_params = {"datumFran": "2021-01-01", "datumTill": "2021-01-31"}
    result = client.fetch_matches_list_json(filter_params)
    assert result == {"matchlista": []}
    mock_fetch_matches_list_json.assert_called_once_with(filter_params)


@patch("fogis_api_client.public_api_client.PublicApiClient.fetch_match_json")
def test_fetch_match_json_compatibility(mock_fetch_match_json):
    """Test that fetch_match_json is compatible with the existing API."""
    # Mock the fetch_match_json method
    mock_fetch_match_json.return_value = {
        "matchid": 123456,
        "hemmalag": "Home Team",
        "bortalag": "Away Team",
    }

    # Test with integer match_id
    client = FogisApiClient(cookies={"FogisMobilDomarKlient_ASPXAUTH": "test"})
    result = client.fetch_match_json(123456)
    assert result == {
        "matchid": 123456,
        "hemmalag": "Home Team",
        "bortalag": "Away Team",
    }
    mock_fetch_match_json.assert_called_once_with(123456)

    # Test with string match_id
    mock_fetch_match_json.reset_mock()
    result = client.fetch_match_json("123456")
    assert result == {
        "matchid": 123456,
        "hemmalag": "Home Team",
        "bortalag": "Away Team",
    }
    mock_fetch_match_json.assert_called_once_with("123456")
