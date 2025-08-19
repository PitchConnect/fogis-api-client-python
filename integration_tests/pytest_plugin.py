"""
Pytest plugin for the mock FOGIS API server.

This plugin provides fixtures and hooks to automatically start and stop the mock server
for integration tests. It ensures that the mock server is running before tests that need it
and properly cleans up after tests.

Usage:
    1. Add the plugin to your pytest configuration:
       ```
       # In pyproject.toml
       [tool.pytest.ini_options]
       plugins = ["integration_tests.pytest_plugin"]
       ```

    2. Use the fixtures in your tests:
       ```python
       def test_something(mock_server_auto):
           # The mock server is automatically started and stopped
           # mock_server_auto contains the server URL and other information
           ...
       ```
"""

import logging
import os
import time
from typing import Dict, Generator

import pytest
import requests

# Import the API clients
from fogis_api_client import FogisApiClient
from fogis_api_client.internal.api_client import InternalApiClient

# Import the mock server
from integration_tests.mock_fogis_server import MockFogisServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockServerManager:
    """
    Manager for the mock FOGIS API server.

    This class provides methods to start, stop, and check the status of the mock server.
    It ensures that only one instance of the server is running at a time.
    """

    _instance = None
    _server = None
    _server_thread = None
    _base_url = None

    @classmethod
    def get_instance(cls) -> "MockServerManager":
        """
        Get the singleton instance of the manager.

        Returns:
            MockServerManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_server(self, host: str = "localhost", port: int = 5001) -> Dict[str, str]:
        """
        Start the mock server if it's not already running.

        Args:
            host: Host to bind the server to
            port: Port to run the server on

        Returns:
            Dict with server information including the base URL
        """
        # Check if the server is already running
        if self._server is not None and self._server_thread is not None and self._server_thread.is_alive():
            logger.info(f"Mock server is already running at {self._base_url}")
            return {
                "base_url": self._base_url,
                "host": host,
                "port": str(port),
            }

        # Try to connect to an existing server
        urls_to_try = [
            f"http://{host}:{port}",
            "http://localhost:5001",
            "http://127.0.0.1:5001",
            "http://0.0.0.0:5001",
            os.environ.get("MOCK_SERVER_URL", "http://mock-fogis-server:5001"),
        ]

        for url in urls_to_try:
            try:
                logger.info(f"Trying to connect to mock server at {url}")
                response = requests.get(f"{url}/health", timeout=1)
                if response.status_code == 200:
                    logger.info(f"Successfully connected to existing mock server at {url}")
                    self._base_url = url
                    return {
                        "base_url": url,
                        "host": host,
                        "port": str(port),
                    }
            except requests.exceptions.RequestException as e:
                logger.info(f"Failed to connect to {url}: {e}")

        # If we get here, no existing server was found, so start a new one
        logger.info(f"Starting new mock server on {host}:{port}")
        self._server = MockFogisServer(host=host, port=port)
        self._server_thread = self._server.run(threaded=True)
        self._base_url = f"http://{host}:{port}"

        # Wait for the server to be ready
        self._wait_for_server()

        return {
            "base_url": self._base_url,
            "host": host,
            "port": str(port),
        }

    def stop_server(self) -> None:
        """
        Stop the mock server if it's running.
        """
        if self._server is not None:
            logger.info("Stopping mock server")
            try:
                self._server.shutdown()
                self._server = None
                self._server_thread = None
                self._base_url = None
            except Exception as e:
                logger.error(f"Error stopping mock server: {e}")

    def _wait_for_server(self, max_retries: int = 10, retry_delay: int = 2) -> bool:
        """
        Wait for the server to be ready.

        Args:
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds

        Returns:
            bool: True if the server is ready, False otherwise
        """
        logger.info(f"Waiting for mock server to be ready at {self._base_url}")

        # Small initial delay to avoid immediate connection resets during server boot
        time.sleep(0.2)

        for i in range(max_retries):
            try:
                response = requests.get(f"{self._base_url}/health")
                if response.status_code == 200:
                    logger.info(f"Mock server is ready at {self._base_url}")
                    return True
            except requests.exceptions.RequestException as e:
                # First couple of attempts are often during socket setup; keep them quieter
                if i < 2:
                    logger.debug(f"Waiting for mock server to be ready (attempt {i + 1}/{max_retries}): {e}")
                else:
                    logger.info(f"Waiting for mock server to be ready (attempt {i + 1}/{max_retries}): {e}")

            time.sleep(retry_delay)

        logger.error(f"Failed to connect to mock server at {self._base_url} after {max_retries} attempts")
        return False

    def clear_request_history(self) -> None:
        """
        Clear the request history of the mock server.
        """
        if self._base_url is not None:
            try:
                requests.post(f"{self._base_url}/clear-request-history")
                logger.info("Cleared mock server request history")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to clear request history: {e}")


# Register the plugin
def pytest_configure(config):
    """
    Register the plugin with pytest.
    """
    config.pluginmanager.register(MockServerPlugin(), "mock_server_plugin")


class MockServerPlugin:
    """
    Pytest plugin for the mock FOGIS API server.
    """

    @pytest.fixture(scope="session")
    def mock_server_auto(self) -> Generator[Dict[str, str], None, None]:
        """
        Fixture that automatically starts and stops the mock server.

        This fixture starts the mock server at the beginning of the test session
        and stops it at the end. It's useful for running tests that require the
        mock server without having to start it manually.

        Yields:
            Dict with server information including the base URL
        """
        # Start the server
        manager = MockServerManager.get_instance()
        server_info = manager.start_server()

        # Yield the server information
        yield server_info

        # Stop the server
        manager.stop_server()

    @pytest.fixture
    def mock_api_urls_auto(self, mock_server_auto: Dict[str, str]) -> Generator[None, None, None]:
        """
        Temporarily override API URLs to point to mock server.

        This fixture handles setting up and tearing down the API URLs for tests.
        It ensures that the URLs are properly restored after the test completes,
        even if the test fails.

        Args:
            mock_server_auto: The mock server fixture

        Yields:
            None
        """
        # Store original base URLs
        original_base_url = FogisApiClient.BASE_URL
        original_internal_base_url = InternalApiClient.BASE_URL

        # Override base URLs to use the mock server
        FogisApiClient.BASE_URL = f"{mock_server_auto['base_url']}/mdk"
        InternalApiClient.BASE_URL = f"{mock_server_auto['base_url']}/mdk"

        # Clear request history at the beginning of each test for better isolation
        manager = MockServerManager.get_instance()
        manager.clear_request_history()

        try:
            # Run the test
            yield
        finally:
            # Restore original base URLs
            FogisApiClient.BASE_URL = original_base_url
            InternalApiClient.BASE_URL = original_internal_base_url

    @pytest.fixture
    def clear_request_history_auto(self, mock_server_auto: Dict[str, str]) -> Generator[None, None, None]:
        """
        Fixture that clears the request history before and after each test.

        This ensures test isolation by preventing previous test requests from affecting current tests.

        Args:
            mock_server_auto: The mock server fixture

        Yields:
            None
        """
        # Clear request history at the beginning of the test
        manager = MockServerManager.get_instance()
        manager.clear_request_history()

        # Run the test
        yield

        # Clear again after the test to leave a clean state for the next test
        manager.clear_request_history()

    @pytest.fixture
    def fogis_test_client_auto(self, mock_server_auto: Dict[str, str], mock_api_urls_auto) -> FogisApiClient:
        """
        Fixture that provides a configured FogisApiClient for testing.

        This fixture combines the mock_server_auto and mock_api_urls_auto fixtures
        to create a properly configured client for testing. It reduces code duplication by
        handling the common pattern of creating a client with test credentials.

        Args:
            mock_server_auto: The mock server fixture
            mock_api_urls_auto: The fixture that temporarily overrides API URLs

        Returns:
            FogisApiClient: A configured client for testing
        """
        # Create a client with test credentials
        client = FogisApiClient(
            username="test_user",
            password="test_password",
        )

        # Return the client
        return client
