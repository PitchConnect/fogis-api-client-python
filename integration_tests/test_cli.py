"""
Integration tests for the CLI.

This module contains integration tests for the CLI.
"""

import time
import unittest

import requests

from fogis_api_client.cli.api_client import MockServerApiClient
from integration_tests.mock_fogis_server import MockFogisServer


class TestCli(unittest.TestCase):
    """Test case for the CLI."""

    @classmethod
    def setUpClass(cls):
        """Set up the test case."""
        # Prefer reusing an existing server (e.g., when run via pytest plugin/script)
        base_urls = ["http://127.0.0.1:5001", "http://localhost:5001"]
        detected_base = None
        for base in base_urls:
            try:
                resp = requests.get(f"{base}/health", timeout=0.3)
                if resp.status_code == 200:
                    detected_base = base
                    break
            except requests.exceptions.RequestException:
                pass
        if detected_base is None:
            # Start the mock server directly (bind explicitly to IPv4 to avoid IPv6 issues)
            cls.server = MockFogisServer(host="127.0.0.1", port=5001)
            cls.server_thread = cls.server.run(threaded=True)
            detected_base = "http://127.0.0.1:5001"
            # Wait for server readiness
            for _ in range(20):
                try:
                    resp = requests.get(f"{detected_base}/health", timeout=0.5)
                    if resp.status_code == 200:
                        break
                except requests.exceptions.RequestException:
                    pass
                time.sleep(0.3)
        else:
            cls.server = None
            cls.server_thread = None
        # Create an API client after readiness confirmed
        from urllib.parse import urlparse

        parsed = urlparse(detected_base)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 5001
        cls.client = MockServerApiClient(host=host, port=port)
        # Ensure CLI /api/cli/status endpoint is ready as well
        cls.client.wait_for_server(timeout=5)
        cls._expected_host = host

    @classmethod
    def tearDownClass(cls):
        """Tear down the test case."""
        # Stop the mock server only if we started it here
        if getattr(cls, "server", None) is not None:
            try:
                cls.server.shutdown()
                time.sleep(0.5)
            except Exception as e:
                print(f"Error shutting down server: {e}")

    def test_status_command(self):
        """Test the status command."""
        # Get the status directly from the API client
        status = self.client.get_status()

        # Check the result
        self.assertEqual(status["status"], "running")
        # Accept either localhost or 127.0.0.1 depending on who started the server
        self.assertIn(status["host"], ("127.0.0.1", "localhost"))
        self.assertEqual(status["port"], 5001)

    def test_history_command(self):
        """Test the history command."""
        # Clear the history
        response = self.client.clear_history()
        self.assertEqual(response["status"], "success")

        # Make a request to the server
        requests.get("http://127.0.0.1:5001/mdk/Login.aspx")

        # View the history
        history = self.client.get_history()

        # Check the result
        self.assertGreaterEqual(len(history), 1)

        # Find the request to /mdk/Login.aspx
        login_requests = [req for req in history if req["path"] == "/mdk/Login.aspx"]
        self.assertGreaterEqual(len(login_requests), 1, "No requests to /mdk/Login.aspx found in history")

        # Check the most recent login request
        login_request = login_requests[-1]
        self.assertEqual(login_request["method"], "GET")
        self.assertEqual(login_request["path"], "/mdk/Login.aspx")

    def test_validation_command(self):
        """Test the validation command."""
        # Get the validation status
        status = self.client.get_validation_status()
        self.assertIsNotNone(status)

        # Disable validation
        response = self.client.set_validation_status(False)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["validation_enabled"], False)

        # Verify validation is disabled
        status = self.client.get_validation_status()
        self.assertFalse(status)

        # Enable validation
        response = self.client.set_validation_status(True)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["validation_enabled"], True)

        # Verify validation is enabled
        status = self.client.get_validation_status()
        self.assertTrue(status)

    def test_test_command(self):
        """Test the test command."""
        # Test the login endpoint directly
        response = self.client.test_endpoint("/mdk/Login.aspx", "GET")

        # Check the result
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)


if __name__ == "__main__":
    unittest.main()
