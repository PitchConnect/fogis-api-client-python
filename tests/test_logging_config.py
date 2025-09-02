"""Tests for the logging_config module."""

import io
import logging
import unittest
from unittest.mock import patch

from fogis_api_client.logging_config import (
    SensitiveFilter,
    add_sensitive_filter,
    configure_logging,
    get_log_levels,
    get_logger,
    set_log_level,
)


class TestLoggingConfig(unittest.TestCase):
    """Test cases for the logging_config module."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset the root logger before each test
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        root_logger.setLevel(logging.WARNING)  # Default level

    def test_configure_logging_default(self):
        """Test configure_logging with default parameters."""
        configure_logging()
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.INFO)
        self.assertEqual(len(root_logger.handlers), 1)
        self.assertIsInstance(root_logger.handlers[0], logging.StreamHandler)

    def test_configure_logging_custom_level(self):
        """Test configure_logging with custom level."""
        configure_logging(level=logging.DEBUG)
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.DEBUG)

    def test_configure_logging_string_level(self):
        """Test configure_logging with string level."""
        configure_logging(level="DEBUG")
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.DEBUG)

    def test_configure_logging_file(self):
        """Test configure_logging with file output."""
        with patch("logging.FileHandler") as mock_file_handler:
            configure_logging(log_to_file=True, log_file="test.log", enable_enhanced=False)
            mock_file_handler.assert_called_once_with("test.log")

    def test_get_logger(self):
        """Test get_logger function."""
        logger = get_logger("test_logger")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test_logger")

    def test_set_log_level(self):
        """Test set_log_level function."""
        logger = logging.getLogger("fogis_api_client")
        set_log_level(logging.DEBUG)
        self.assertEqual(logger.level, logging.DEBUG)

    def test_set_log_level_string(self):
        """Test set_log_level with string level."""
        logger = logging.getLogger("fogis_api_client")
        set_log_level("DEBUG")
        self.assertEqual(logger.level, logging.DEBUG)

    def test_get_log_levels(self):
        """Test get_log_levels function."""
        levels = get_log_levels()
        self.assertIsInstance(levels, dict)
        self.assertEqual(levels["DEBUG"], logging.DEBUG)
        self.assertEqual(levels["INFO"], logging.INFO)
        self.assertEqual(levels["WARNING"], logging.WARNING)
        self.assertEqual(levels["ERROR"], logging.ERROR)
        self.assertEqual(levels["CRITICAL"], logging.CRITICAL)

    def test_sensitive_filter(self):
        """Test SensitiveFilter class."""
        # Create a filter
        filter = SensitiveFilter()

        # Create a log record with sensitive information
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Password: secret123",
            args=(),
            exc_info=None,
        )

        # Apply the filter
        filter.filter(record)

        # Check that the password was masked
        self.assertEqual(record.msg, "Password: ********")

    def test_sensitive_filter_custom_patterns(self):
        """Test SensitiveFilter with custom patterns."""
        # Create a filter with custom patterns
        filter = SensitiveFilter({"api_key": "[MASKED_API_KEY]"})

        # Create a log record with sensitive information
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="API Key: abc123",
            args=(),
            exc_info=None,
        )

        # Apply the filter
        filter.filter(record)

        # Check that the API key was masked
        self.assertEqual(record.msg, "API Key: [MASKED_API_KEY]")

    def test_add_sensitive_filter(self):
        """Test add_sensitive_filter function."""
        # Capture log output
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = logging.getLogger("fogis_api_client")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        # Add the sensitive filter
        add_sensitive_filter()

        # Log a message with sensitive information
        logger.info("Password: secret123")

        # Check that the password was masked in the log output
        log_output = stream.getvalue()
        self.assertIn("Password: ********", log_output)


if __name__ == "__main__":
    unittest.main()
