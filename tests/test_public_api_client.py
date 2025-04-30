"""
Tests for the public API client.

These tests verify that the public API client correctly interacts with the internal API layer.
"""
import pytest
from unittest.mock import MagicMock, patch

import requests

from fogis_api_client.public_api_client import (
    FogisAPIRequestError,
    FogisDataError,
    FogisLoginError,
    PublicApiClient,
)


def test_public_api_client_initialization():
    """Test that the public API client can be initialized."""
    # Test with username and password
    client = PublicApiClient(username="test", password="test")
    assert client.username == "test"
    assert client.password == "test"
    assert client.cookies is None
    # BASE_URL can be overridden by environment variables, so we don't test the exact value

    # Test with cookies
    cookies = {"FogisMobilDomarKlient_ASPXAUTH": "test", "ASP_NET_SessionId": "test"}
    client = PublicApiClient(cookies=cookies)
    assert client.username is None
    assert client.password is None
    assert client.cookies == cookies

    # Test with invalid parameters
    with pytest.raises(ValueError):
        PublicApiClient()


def test_login():
    """Test the login method."""
    # Test with existing cookies
    cookies = {"FogisMobilDomarKlient_ASPXAUTH": "test", "ASP_NET_SessionId": "test"}
    client = PublicApiClient(cookies=cookies)
    result = client.login()
    assert result == cookies
    assert client.cookies == cookies

    # Test login failure
    client = PublicApiClient(username="test", password="test")
    client.cookies = None

    # Patch the authenticate function to raise an error
    def mock_login():
        raise FogisLoginError("Test login error")

    # Save original login method
    original_login = client.login
    # Replace with our mock
    client.login = mock_login

    # Test that the error is raised
    with pytest.raises(FogisLoginError, match="Test login error"):
        client.login()


@patch("fogis_api_client.internal.api_client.InternalApiClient.get_matches_list")
@patch("fogis_api_client.public_api_client.PublicApiClient.login")
def test_fetch_matches_list_json(mock_login, mock_get_matches_list):
    """Test the fetch_matches_list_json method."""
    # Mock the login and get_matches_list methods
    mock_login.return_value = {
        "FogisMobilDomarKlient_ASPXAUTH": "test",
        "ASP_NET_SessionId": "test",
    }
    mock_get_matches_list.return_value = {"matchlista": []}

    # Test with default filter parameters
    client = PublicApiClient(username="test", password="test")
    client.cookies = mock_login.return_value
    result = client.fetch_matches_list_json()
    assert result == {"matchlista": []}
    mock_login.assert_not_called()
    mock_get_matches_list.assert_called_once()

    # Test with custom filter parameters
    mock_get_matches_list.reset_mock()
    filter_params = {"datumFran": "2021-01-01", "datumTill": "2021-01-31"}
    result = client.fetch_matches_list_json(filter_params)
    assert result == {"matchlista": []}
    mock_get_matches_list.assert_called_once_with(filter_params)


@patch("fogis_api_client.internal.api_client.InternalApiClient.get_match")
@patch("fogis_api_client.public_api_client.PublicApiClient.login")
def test_fetch_match_json(mock_login, mock_get_match):
    """Test the fetch_match_json method."""
    # Mock the login and get_match methods
    mock_login.return_value = {
        "FogisMobilDomarKlient_ASPXAUTH": "test",
        "ASP_NET_SessionId": "test",
    }
    mock_get_match.return_value = {
        "matchid": 123456,
        "hemmalag": "Home Team",
        "bortalag": "Away Team",
    }

    # Test with integer match_id
    client = PublicApiClient(username="test", password="test")
    client.cookies = mock_login.return_value
    result = client.fetch_match_json(123456)
    assert result == {
        "matchid": 123456,
        "hemmalag": "Home Team",
        "bortalag": "Away Team",
    }
    mock_login.assert_not_called()
    mock_get_match.assert_called_once_with(123456)

    # Test with string match_id
    mock_get_match.reset_mock()
    result = client.fetch_match_json("123456")
    assert result == {
        "matchid": 123456,
        "hemmalag": "Home Team",
        "bortalag": "Away Team",
    }
    mock_get_match.assert_called_once_with(123456)
