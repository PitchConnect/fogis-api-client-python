"""
Test the pytest plugin for the mock FOGIS API server.

This module contains tests that verify the functionality of the pytest plugin
for the mock FOGIS API server.
"""

import logging

import requests

from fogis_api_client import FogisApiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_mock_server(mock_fogis_server):
    """Test that the mock_fogis_server fixture works correctly."""
    # Verify that the mock server is running
    assert mock_fogis_server is not None
    assert "base_url" in mock_fogis_server

    # Try to access the health endpoint
    response = requests.get(f"{mock_fogis_server['base_url']}/health")
    assert response.status_code == 200

    # Verify the response
    data = response.json()
    assert data["status"] == "healthy"


def test_mock_api_urls(mock_fogis_server, mock_api_urls):
    """Test that the mock_api_urls fixture works correctly."""
    # Verify that the API URLs are overridden
    assert FogisApiClient.BASE_URL.startswith(mock_fogis_server["base_url"])

    # Create a client
    client = FogisApiClient(
        username="test_user",
        password="test_password",
    )

    # Try to login
    cookies = client.login()

    # Verify that login was successful
    assert cookies is not None
    assert any(k for k in cookies if k.startswith("FogisMobilDomarKlient"))


def test_fogis_test_client(fogis_test_client):
    """Test that the fogis_test_client fixture works correctly."""
    # Verify that the client is configured correctly
    assert fogis_test_client is not None

    # Try to login
    cookies = fogis_test_client.login()

    # Verify that login was successful
    assert cookies is not None
    assert any(k for k in cookies if k.startswith("FogisMobilDomarKlient"))

    # Try to fetch matches
    matches = fogis_test_client.fetch_matches_list_json()

    # Verify that matches were fetched
    assert matches is not None
    # The response might be a dict or a list depending on the mock server implementation
    assert isinstance(matches, (list, dict))
