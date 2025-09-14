"""
Tests for the public API client.

These tests verify that the public API client correctly interacts with the internal API layer.
"""

from unittest.mock import Mock, patch

import pytest

from fogis_api_client.public_api_client import (
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
    client.login
    # Replace with our mock
    client.login = mock_login

    # Test that the error is raised
    with pytest.raises(FogisLoginError, match="Test login error"):
        client.login()


@patch("fogis_api_client.public_api_client.PublicApiClient.login")
def test_fetch_matches_list_json(mock_login):
    """Test the fetch_matches_list_json method."""
    # Mock the login method
    mock_login.return_value = {
        "FogisMobilDomarKlient_ASPXAUTH": "test",
        "ASP_NET_SessionId": "test",
    }

    # Create client and mock its session
    client = PublicApiClient(username="test", password="test")
    client.cookies = mock_login.return_value
    client.authentication_method = "aspnet"  # Set authentication method so is_authenticated() returns True

    # Mock the _make_authenticated_request method instead of session.get
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = Mock(return_value={"matchlista": []})
    client._make_authenticated_request = Mock(return_value=mock_response)

    # Test with default filter parameters
    result = client.fetch_matches_list_json()
    assert result == {"matchlista": []}
    mock_login.assert_not_called()
    client._make_authenticated_request.assert_called_once()

    # Test with custom filter parameters
    client._make_authenticated_request.reset_mock()
    filter_params = {"datumFran": "2021-01-01", "datumTill": "2021-01-31"}
    result = client.fetch_matches_list_json(filter_params)
    assert result == {"matchlista": []}
    client._make_authenticated_request.assert_called_once()


@patch("fogis_api_client.public_api_client.PublicApiClient.login")
def test_fetch_match_json(mock_login):
    """Test the fetch_match_json method."""
    # Mock the login method
    mock_login.return_value = {
        "FogisMobilDomarKlient_ASPXAUTH": "test",
        "ASP_NET_SessionId": "test",
    }

    # Create client and mock its session
    client = PublicApiClient(username="test", password="test")
    client.cookies = mock_login.return_value
    client.authentication_method = "aspnet"  # Set authentication method so is_authenticated() returns True

    # Mock the session.get method directly for this test
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = Mock(
        return_value={
            "matchid": 123456,
            "hemmalag": "Home Team",
            "bortalag": "Away Team",
        }
    )
    client.session.get = Mock(return_value=mock_response)

    # Test with integer match_id
    result = client.fetch_match_json(123456)
    assert result == {
        "matchid": 123456,
        "hemmalag": "Home Team",
        "bortalag": "Away Team",
    }
    mock_login.assert_not_called()
    client.session.get.assert_called_once()

    # Test with string match_id
    client.session.get.reset_mock()
    result = client.fetch_match_json("123456")
    assert result == {
        "matchid": 123456,
        "hemmalag": "Home Team",
        "bortalag": "Away Team",
    }
    client.session.get.assert_called_once()
