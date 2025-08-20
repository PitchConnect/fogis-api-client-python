"""
Pytest fixtures for integration tests with the mock FOGIS API server.
"""

import logging
import os
import threading
import time
from typing import Dict, Generator

import pytest
import requests

# Import the API clients
from fogis_api_client import FogisApiClient

# Import the mock server
from integration_tests.mock_fogis_server import MockFogisServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def mock_fogis_server() -> Generator[Dict[str, str], None, None]:
    """
    Fixture that connects to the mock FOGIS API server or starts one locally if needed.

    Yields:
        Dict with server information including the base URL
    """
    # Get the mock server URL from environment variable or use default
    mock_server_url = os.environ.get("MOCK_SERVER_URL", "http://mock-fogis-server:5001")
    server_thread = None
    local_server = None

    # Try different URLs if the default one doesn't work
    urls_to_try = [
        mock_server_url,
        "http://localhost:5001",
        "http://127.0.0.1:5001",
        "http://0.0.0.0:5001",
    ]

    # Try each URL until one works
    for url in urls_to_try:
        try:
            logger.info(f"Trying to connect to mock server at {url}")
            response = requests.get(f"{url}/health", timeout=1)
            if response.status_code == 200:
                mock_server_url = url
                logger.info(f"Successfully connected to mock server at {url}")
                break
        except requests.exceptions.RequestException as e:
            logger.info(f"Failed to connect to {url}: {e}")
    else:
        # If we get here, none of the URLs worked, so start a local server
        logger.warning("Could not connect to mock server with any of the tried URLs, starting a local server")
        local_server = MockFogisServer(host="localhost", port=5001)

        # Start the server in a separate thread
        def run_server():
            local_server.app.run(host="localhost", port=5001)

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # Use localhost as the server URL
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
            logger.info(f"Waiting for mock FOGIS server to be ready (attempt {i + 1}/{max_retries}): {e}")

        time.sleep(retry_delay)
    else:
        if server_thread:
            # If we started a local server but it's not responding, something is wrong
            raise RuntimeError(f"Started a local mock server but failed to connect to it at {mock_server_url}")
        else:
            # If we're trying to connect to an external server and it's not responding
            raise RuntimeError(f"Failed to connect to mock FOGIS server at {mock_server_url} after {max_retries} attempts")

    # Parse the URL to get host and port
    from urllib.parse import urlparse

    parsed_url = urlparse(mock_server_url)
    host = parsed_url.hostname
    port = str(parsed_url.port) if parsed_url.port else "5000"

    # Yield the server information
    try:
        yield {
            "base_url": mock_server_url,
            "host": host,
            "port": port,
        }
    finally:
        # Clean up the server thread if we started one
        if server_thread and server_thread.is_alive():
            logger.info("Shutting down local mock server")
            # We don't need to explicitly stop the thread since it's a daemon thread
            # and will be terminated when the main thread exits


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


@pytest.fixture
def clear_request_history(mock_fogis_server: Dict[str, str]) -> None:
    """
    Fixture that clears the request history before and after each test.

    This ensures test isolation by preventing previous test requests from affecting current tests.
    Using this fixture is CRITICAL for proper test isolation and should be included in all test methods
    that interact with the mock server.

    Without this fixture, tests may interfere with each other as the mock server maintains state
    between test runs, which can lead to flaky tests and false positives/negatives.

    Args:
        mock_fogis_server: The mock server information
    """
    # Clear request history at the beginning of the test
    requests.post(f"{mock_fogis_server['base_url']}/clear-request-history")
    yield
    # Clear again after the test to leave a clean state for the next test
    # This helps with debugging and ensures proper isolation
    requests.post(f"{mock_fogis_server['base_url']}/clear-request-history")




