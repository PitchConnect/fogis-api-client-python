"""
Tests for the AuthServer class.
"""

import unittest
from unittest.mock import Mock, patch

from auth_server import AuthServer
from token_manager import TokenManager


class TestAuthServer(unittest.TestCase):
    """Test cases for the AuthServer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "AUTH_SERVER_HOST": "localhost",
            "AUTH_SERVER_PORT": 8080,
            "SCOPES": [
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/contacts"
            ],
            "TOKEN_REFRESH_BUFFER_DAYS": 6
        }

        # Create mock token manager
        self.mock_token_manager = Mock(spec=TokenManager)
        self.mock_token_manager.config = self.config

    def test_init(self):
        """Test AuthServer initialization."""
        auth_server = AuthServer(self.config, self.mock_token_manager)

        self.assertEqual(auth_server.config, self.config)
        self.assertEqual(auth_server.token_manager, self.mock_token_manager)
        self.assertEqual(auth_server.host, "localhost")
        self.assertEqual(auth_server.port, 8080)
        self.assertIsNone(auth_server.server)
        self.assertFalse(auth_server.auth_completed)
        self.assertFalse(auth_server.auth_success)

    def test_init_default_host_port(self):
        """Test AuthServer initialization with default host and port."""
        config_no_host_port = {
            "SCOPES": [
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/contacts"
            ]
        }

        auth_server = AuthServer(config_no_host_port, self.mock_token_manager)

        self.assertEqual(auth_server.host, "localhost")
        self.assertEqual(auth_server.port, 8080)

    def test_start_mock_token_manager(self):
        """Test starting the auth server with mocked token manager."""
        auth_server = AuthServer(self.config, self.mock_token_manager)

        # Mock the token manager's initiate_auth_flow method
        self.mock_token_manager.initiate_auth_flow.return_value = "http://test-auth-url?state=test-state"

        # Mock make_server to avoid actually starting a server
        with patch('auth_server.make_server') as mock_make_server:
            mock_server = Mock()
            mock_make_server.return_value = mock_server

            result = auth_server.start()

            self.assertEqual(result, "http://test-auth-url?state=test-state")
            self.assertEqual(auth_server.state, "test-state")
            self.mock_token_manager.initiate_auth_flow.assert_called_once()

    def test_wait_for_auth_timeout(self):
        """Test waiting for authentication with timeout."""
        auth_server = AuthServer(self.config, self.mock_token_manager)

        # Test timeout (should return False quickly)
        result = auth_server.wait_for_auth(timeout=1)
        self.assertFalse(result)

    def test_wait_for_auth_success(self):
        """Test waiting for authentication with success."""
        auth_server = AuthServer(self.config, self.mock_token_manager)

        # Simulate successful auth
        auth_server.auth_completed = True
        auth_server.auth_success = True

        result = auth_server.wait_for_auth(timeout=1)
        self.assertTrue(result)

    def test_stop_no_server(self):
        """Test stopping when no server is running."""
        auth_server = AuthServer(self.config, self.mock_token_manager)

        # Should not raise an exception
        auth_server.stop()

    def test_stop_with_server(self):
        """Test stopping with running server."""
        auth_server = AuthServer(self.config, self.mock_token_manager)

        # Mock server
        mock_server = Mock()
        auth_server.server = mock_server

        auth_server.stop()

        mock_server.shutdown.assert_called_once()

    def test_get_auth_url_no_server(self):
        """Test getting auth URL when no server is running."""
        auth_server = AuthServer(self.config, self.mock_token_manager)

        result = auth_server.get_auth_url()
        self.assertIsNone(result)

    def test_get_auth_url_with_server(self):
        """Test getting auth URL when server is running."""
        auth_server = AuthServer(self.config, self.mock_token_manager)

        # Simulate server running
        auth_server.server = Mock()
        auth_server.state = "test-state"

        result = auth_server.get_auth_url()
        self.assertIsNotNone(result)
        self.assertIn("localhost:8080", result)


if __name__ == '__main__':
    unittest.main()
