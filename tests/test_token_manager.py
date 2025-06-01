"""
Tests for the TokenManager class.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from token_manager import TokenManager


class TestTokenManager(unittest.TestCase):
    """Test cases for the TokenManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "SCOPES": [
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/contacts"
            ],
            "TOKEN_REFRESH_BUFFER_DAYS": 6
        }

        # Create temporary files for testing
        self.temp_dir = tempfile.mkdtemp()
        self.credentials_file = os.path.join(self.temp_dir, "credentials.json")
        self.token_file = os.path.join(self.temp_dir, "token.json")

        # Sample credentials data
        self.credentials_data = {
            "installed": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"]
            }
        }

        # Sample token data
        self.token_data = {
            "token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": [
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/contacts"
            ],
            "expiry": (datetime.now() + timedelta(days=30)).isoformat()
        }

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        if os.path.exists(self.credentials_file):
            os.remove(self.credentials_file)
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
        os.rmdir(self.temp_dir)

    def test_init(self):
        """Test TokenManager initialization."""
        token_manager = TokenManager(
            self.config,
            self.credentials_file,
            self.token_file
        )

        self.assertEqual(token_manager.config, self.config)
        self.assertEqual(token_manager.credentials_file, self.credentials_file)
        self.assertEqual(token_manager.token_file, self.token_file)
        self.assertEqual(token_manager.scopes, self.config["SCOPES"])
        self.assertEqual(token_manager.refresh_buffer_days, 6)

    def test_get_credentials_no_token_file(self):
        """Test getting credentials when no token file exists."""
        token_manager = TokenManager(
            self.config,
            self.credentials_file,
            self.token_file
        )

        result = token_manager.get_credentials()
        self.assertIsNone(result)

    def test_get_credentials_valid_file(self):
        """Test getting credentials from valid file."""
        # Create token file
        with open(self.token_file, 'w') as f:
            json.dump(self.token_data, f)

        token_manager = TokenManager(
            self.config,
            self.credentials_file,
            self.token_file
        )

        # Mock the Credentials.from_authorized_user_file to return a valid mock
        with patch('token_manager.Credentials') as mock_creds_class:
            mock_creds = Mock()
            mock_creds.valid = True
            mock_creds_class.from_authorized_user_file.return_value = mock_creds

            result = token_manager.get_credentials()
            self.assertIsNotNone(result)
            self.assertTrue(result.valid)

    def test_get_credentials_invalid_format(self):
        """Test getting credentials with invalid format."""
        # Create invalid token file
        invalid_token_data = {
            "token": "test_access_token"
            # Missing required fields
        }

        with open(self.token_file, 'w') as f:
            json.dump(invalid_token_data, f)

        token_manager = TokenManager(
            self.config,
            self.credentials_file,
            self.token_file
        )

        # Mock Credentials.from_authorized_user_file to raise an exception
        with patch('token_manager.Credentials') as mock_creds_class:
            mock_creds_class.from_authorized_user_file.side_effect = Exception("Invalid format")

            result = token_manager.get_credentials()
            self.assertIsNone(result)

    def test_check_token_expiration_no_token(self):
        """Test token expiration check when no token exists."""
        token_manager = TokenManager(
            self.config,
            self.credentials_file,
            self.token_file
        )

        needs_refresh, expiry = token_manager.check_token_expiration()
        self.assertTrue(needs_refresh)
        self.assertIsNone(expiry)

    def test_check_token_expiration_expired(self):
        """Test token expiration check with expired token."""
        token_manager = TokenManager(
            self.config,
            self.credentials_file,
            self.token_file
        )

        # Mock get_credentials to return expired credentials
        with patch.object(token_manager, 'get_credentials') as mock_get_creds:
            mock_creds = Mock()
            mock_creds.expiry = datetime.now() - timedelta(days=1)  # Expired yesterday
            mock_get_creds.return_value = mock_creds

            needs_refresh, expiry = token_manager.check_token_expiration()
            self.assertTrue(needs_refresh)
            self.assertIsNotNone(expiry)

    def test_check_token_expiration_valid(self):
        """Test token expiration check with valid token."""
        token_manager = TokenManager(
            self.config,
            self.credentials_file,
            self.token_file
        )

        # Mock get_credentials to return valid credentials
        with patch.object(token_manager, 'get_credentials') as mock_get_creds:
            mock_creds = Mock()
            mock_creds.expiry = datetime.now() + timedelta(days=30)  # Expires in 30 days
            mock_get_creds.return_value = mock_creds

            needs_refresh, expiry = token_manager.check_token_expiration()
            self.assertFalse(needs_refresh)
            self.assertIsNotNone(expiry)


if __name__ == '__main__':
    unittest.main()
