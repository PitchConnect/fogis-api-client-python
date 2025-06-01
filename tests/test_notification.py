"""
Tests for the NotificationSender class.
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock

from notification import NotificationSender


class TestNotificationSender(unittest.TestCase):
    """Test cases for the NotificationSender class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "NOTIFICATION_METHOD": "email",
            "NOTIFICATION_EMAIL_SENDER": "sender@example.com",
            "NOTIFICATION_EMAIL_RECEIVER": "receiver@example.com",
            "SMTP_SERVER": "smtp.gmail.com",
            "SMTP_PORT": 587,
            "SMTP_USERNAME": "sender@example.com",
            "SMTP_PASSWORD": "test_password",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/test",
            "SLACK_WEBHOOK_URL": "https://hooks.slack.com/test"
        }

        self.test_auth_url = "https://accounts.google.com/oauth/authorize?test=123"
        self.test_expiry_info = "Token expires in 1 day"

    def test_init_email(self):
        """Test NotificationSender initialization with email method."""
        sender = NotificationSender(self.config)

        self.assertEqual(sender.config, self.config)
        self.assertEqual(sender.method, "email")

    def test_init_discord(self):
        """Test NotificationSender initialization with Discord method."""
        config = self.config.copy()
        config["NOTIFICATION_METHOD"] = "discord"

        sender = NotificationSender(config)

        self.assertEqual(sender.method, "discord")

    def test_init_default_method(self):
        """Test NotificationSender initialization with default method."""
        config = self.config.copy()
        del config["NOTIFICATION_METHOD"]

        sender = NotificationSender(config)

        self.assertEqual(sender.method, "email")

    @patch('notification.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = NotificationSender(self.config)

        result = sender._send_email("Test Subject", "Test Message")

        self.assertTrue(result)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("sender@example.com", "test_password")
        mock_server.send_message.assert_called_once()

    def test_send_email_missing_config(self):
        """Test email sending with missing configuration."""
        config = self.config.copy()
        del config["SMTP_PASSWORD"]

        sender = NotificationSender(config)

        result = sender._send_email("Test Subject", "Test Message")

        self.assertFalse(result)

    @patch('notification.smtplib.SMTP')
    def test_send_email_smtp_error(self, mock_smtp):
        """Test email sending with SMTP error."""
        # Mock SMTP server that raises exception
        mock_smtp.side_effect = Exception("SMTP connection failed")

        sender = NotificationSender(self.config)

        result = sender._send_email("Test Subject", "Test Message")

        self.assertFalse(result)

    @patch('notification.urlopen')
    def test_send_discord_success(self, mock_urlopen):
        """Test successful Discord webhook sending."""
        # Mock response
        mock_response = Mock()
        mock_response.status = 204
        mock_urlopen.return_value.__enter__.return_value = mock_response

        sender = NotificationSender(self.config)

        result = sender._send_discord("Test Subject", "Test Message", self.test_auth_url)

        self.assertTrue(result)
        mock_urlopen.assert_called_once()

    def test_send_discord_no_webhook_url(self):
        """Test Discord sending without webhook URL."""
        config = self.config.copy()
        del config["DISCORD_WEBHOOK_URL"]

        sender = NotificationSender(config)

        result = sender._send_discord("Test Subject", "Test Message", self.test_auth_url)

        self.assertFalse(result)

    @patch('notification.urlopen')
    def test_send_discord_http_error(self, mock_urlopen):
        """Test Discord sending with HTTP error."""
        # Mock response with error status
        mock_response = Mock()
        mock_response.status = 400
        mock_urlopen.return_value.__enter__.return_value = mock_response

        sender = NotificationSender(self.config)

        result = sender._send_discord("Test Subject", "Test Message", self.test_auth_url)

        self.assertFalse(result)

    @patch('notification.urlopen')
    def test_send_slack_success(self, mock_urlopen):
        """Test successful Slack webhook sending."""
        # Mock response
        mock_response = Mock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        sender = NotificationSender(self.config)

        result = sender._send_slack("Test Subject", "Test Message", self.test_auth_url)

        self.assertTrue(result)
        mock_urlopen.assert_called_once()

    def test_send_slack_no_webhook_url(self):
        """Test Slack sending without webhook URL."""
        config = self.config.copy()
        del config["SLACK_WEBHOOK_URL"]

        sender = NotificationSender(config)

        result = sender._send_slack("Test Subject", "Test Message", self.test_auth_url)

        self.assertFalse(result)

    @patch('notification.NotificationSender._send_email')
    def test_send_auth_notification_email(self, mock_send_email):
        """Test sending auth notification via email."""
        mock_send_email.return_value = True

        sender = NotificationSender(self.config)

        result = sender.send_auth_notification(self.test_auth_url, self.test_expiry_info)

        self.assertTrue(result)
        mock_send_email.assert_called_once()

    @patch('notification.NotificationSender._send_discord')
    def test_send_auth_notification_discord(self, mock_send_discord):
        """Test sending auth notification via Discord."""
        config = self.config.copy()
        config["NOTIFICATION_METHOD"] = "discord"
        mock_send_discord.return_value = True

        sender = NotificationSender(config)

        result = sender.send_auth_notification(self.test_auth_url, self.test_expiry_info)

        self.assertTrue(result)
        mock_send_discord.assert_called_once()

    def test_send_auth_notification_unknown_method(self):
        """Test sending auth notification with unknown method."""
        config = self.config.copy()
        config["NOTIFICATION_METHOD"] = "unknown"

        sender = NotificationSender(config)

        result = sender.send_auth_notification(self.test_auth_url, self.test_expiry_info)

        self.assertFalse(result)

    @patch('notification.NotificationSender._send_email')
    def test_send_success_notification(self, mock_send_email):
        """Test sending success notification."""
        mock_send_email.return_value = True

        sender = NotificationSender(self.config)

        result = sender.send_success_notification()

        self.assertTrue(result)
        mock_send_email.assert_called_once()


if __name__ == '__main__':
    unittest.main()
