"""
Integration tests for the CLI.

This module contains integration tests for the CLI.
"""

import json
import os
import subprocess
import sys
import time
import unittest
from unittest.mock import patch, MagicMock

import requests

from fogis_api_client.cli.api_client import MockServerApiClient
from integration_tests.mock_fogis_server import MockFogisServer


class TestCli(unittest.TestCase):
    """Test case for the CLI."""

    @classmethod
    def setUpClass(cls):
        """Set up the test case."""
        # Start the mock server directly
        cls.server = MockFogisServer(host="localhost", port=5001)

        # Start the server in a separate thread
        cls.server_thread = cls.server.run(threaded=True)

        # Wait for the server to start
        time.sleep(2)

        # Create an API client
        cls.client = MockServerApiClient()

    @classmethod
    def tearDownClass(cls):
        """Tear down the test case."""
        # Stop the mock server
        try:
            cls.server.shutdown()
            time.sleep(1)  # Give it a moment to shut down
        except Exception as e:
            print(f"Error shutting down server: {e}")

    def test_status_command(self):
        """Test the status command."""
        # Get the status directly from the API client
        status = self.client.get_status()

        # Check the result
        self.assertEqual(status["status"], "running")
        self.assertEqual(status["host"], "localhost")
        self.assertEqual(status["port"], 5001)

    def test_history_command(self):
        """Test the history command."""
        # Clear the history
        response = self.client.clear_history()
        self.assertEqual(response["status"], "success")

        # Make a request to the server
        requests.get("http://localhost:5001/mdk/Login.aspx")

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
