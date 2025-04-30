"""
Pytest fixtures for integration tests with the mock FOGIS API server.
"""
import logging
import os
import time
from typing import Dict, Generator

import pytest
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def mock_fogis_server() -> Generator[Dict[str, str], None, None]:
    """
    Fixture that connects to the containerized mock FOGIS API server.

    Yields:
        Dict with server information including the base URL
    """
    # Get the mock server URL from environment variable or use default
    mock_server_url = os.environ.get("MOCK_SERVER_URL", "http://mock-fogis-server:5001")

    # For local testing outside of Docker, fall back to localhost if the container isn't accessible
    if "mock-fogis-server" in mock_server_url:
        try:
            # Try to connect to the containerized mock server
            response = requests.get(f"{mock_server_url}/health", timeout=1)
            if response.status_code != 200:
                # If not successful, fall back to localhost
                mock_server_url = "http://localhost:5001"
        except requests.exceptions.RequestException:
            # If connection fails, fall back to localhost
            mock_server_url = "http://localhost:5001"

    # Wait for the server to be ready
    max_retries = 10
    retry_delay = 2

    logger.info(f"Connecting to mock FOGIS server at {mock_server_url}")

    for i in range(max_retries):
        try:
            response = requests.get(f"{mock_server_url}/health")
            if response.status_code == 200:
                logger.info(f"Successfully connected to mock FOGIS server at {mock_server_url}")
                break
        except requests.exceptions.RequestException as e:
            logger.info(f"Waiting for mock FOGIS server to be ready (attempt {i+1}/{max_retries}): {e}")

        time.sleep(retry_delay)
    else:
        raise RuntimeError(f"Failed to connect to mock FOGIS server at {mock_server_url} after {max_retries} attempts")

    # Parse the URL to get host and port
    from urllib.parse import urlparse
    parsed_url = urlparse(mock_server_url)
    host = parsed_url.hostname
    port = str(parsed_url.port) if parsed_url.port else "5000"

    # Yield the server information
    yield {
        "base_url": mock_server_url,
        "host": host,
        "port": port,
    }


@pytest.fixture
def test_credentials() -> Dict[str, str]:
    """
    Fixture that provides test credentials for the mock FOGIS API.

    Returns:
        Dict with username and password
    """
    return {
        "username": "test_user",
        "password": "test_password",
    }
