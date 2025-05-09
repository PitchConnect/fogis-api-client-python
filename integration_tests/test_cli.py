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
from unittest.mock import patch

import requests

from fogis_api_client.cli.api_client import MockServerApiClient


class TestCli(unittest.TestCase):
    """Test case for the CLI."""

    @classmethod
    def setUpClass(cls):
        """Set up the test case."""
        # Start the mock server in a separate process
        cls.server_process = subprocess.Popen(
            [sys.executable, "-m", "fogis_api_client.cli.mock_server", "start", "--threaded"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # Wait for the server to start
        time.sleep(2)
        
        # Create an API client
        cls.client = MockServerApiClient()
        
        # Wait for the server to be ready
        for _ in range(10):
            try:
                status = cls.client.get_status()
                if status.get("status") == "running":
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.5)
        else:
            raise RuntimeError("Failed to start the mock server")

    @classmethod
    def tearDownClass(cls):
        """Tear down the test case."""
        # Stop the mock server
        try:
            cls.client.shutdown_server()
        except:
            pass
        
        # Terminate the server process
        cls.server_process.terminate()
        cls.server_process.wait()

    def test_status_command(self):
        """Test the status command."""
        # Run the status command
        result = subprocess.run(
            [sys.executable, "-m", "fogis_api_client.cli.mock_server", "status", "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Check the result
        self.assertEqual(result.returncode, 0)
        status = json.loads(result.stdout)
        self.assertEqual(status["status"], "running")
        self.assertEqual(status["host"], "localhost")
        self.assertEqual(status["port"], 5001)

    def test_history_command(self):
        """Test the history command."""
        # Clear the history
        result = subprocess.run(
            [sys.executable, "-m", "fogis_api_client.cli.mock_server", "history", "clear"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Check the result
        self.assertEqual(result.returncode, 0)
        
        # Make a request to the server
        requests.get("http://localhost:5001/mdk/Login.aspx")
        
        # View the history
        result = subprocess.run(
            [sys.executable, "-m", "fogis_api_client.cli.mock_server", "history", "view", "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Check the result
        self.assertEqual(result.returncode, 0)
        history = json.loads(result.stdout)
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[-1]["method"], "GET")
        self.assertEqual(history[-1]["path"], "/mdk/Login.aspx")

    def test_validation_command(self):
        """Test the validation command."""
        # Get the validation status
        result = subprocess.run(
            [sys.executable, "-m", "fogis_api_client.cli.mock_server", "validation", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Check the result
        self.assertEqual(result.returncode, 0)
        self.assertIn("Request validation is", result.stdout)
        
        # Disable validation
        result = subprocess.run(
            [sys.executable, "-m", "fogis_api_client.cli.mock_server", "validation", "disable"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Check the result
        self.assertEqual(result.returncode, 0)
        self.assertIn("Request validation disabled", result.stdout)
        
        # Enable validation
        result = subprocess.run(
            [sys.executable, "-m", "fogis_api_client.cli.mock_server", "validation", "enable"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Check the result
        self.assertEqual(result.returncode, 0)
        self.assertIn("Request validation enabled", result.stdout)

    def test_test_command(self):
        """Test the test command."""
        # Test the login endpoint
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "fogis_api_client.cli.mock_server",
                "test",
                "/mdk/Login.aspx",
                "--method",
                "GET",
                "--json",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Check the result
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)


if __name__ == "__main__":
    unittest.main()
