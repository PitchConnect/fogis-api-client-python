"""
Tests for the API validation layer.

This module contains tests for the API validation functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from jsonschema import ValidationError

from fogis_api_client.internal.api_contracts import (
    ValidationConfig,
    extract_endpoint_from_url,
    validate_request,
)



class TestValidationLayer(unittest.TestCase):
    """Test cases for the API validation layer."""

    def setUp(self):
        """Set up test fixtures."""
        # Save original validation config
        self.original_enable_validation = ValidationConfig.enable_validation
        self.original_strict_mode = ValidationConfig.strict_mode
        self.original_log_validation_success = ValidationConfig.log_validation_success

        # Enable validation for tests
        ValidationConfig.enable_validation = True
        ValidationConfig.strict_mode = True
        ValidationConfig.log_validation_success = True

    def tearDown(self):
        """Tear down test fixtures."""
        # Restore original validation config
        ValidationConfig.enable_validation = self.original_enable_validation
        ValidationConfig.strict_mode = self.original_strict_mode
        ValidationConfig.log_validation_success = self.original_log_validation_success

    def test_extract_endpoint_from_url(self):
        """Test extracting endpoint from URL."""
        # Test with full URL
        url = "https://fogis.svenskfotboll.se/MatchWebMetoder.aspx/SparaMatchresultatLista"
        endpoint = extract_endpoint_from_url(url)
        self.assertEqual(endpoint, "/MatchWebMetoder.aspx/SparaMatchresultatLista")

        # Test with just the endpoint
        url = "/MatchWebMetoder.aspx/SparaMatchresultatLista"
        endpoint = extract_endpoint_from_url(url)
        self.assertEqual(endpoint, url)

        # Test with invalid URL
        url = "invalid-url"
        endpoint = extract_endpoint_from_url(url)
        self.assertEqual(endpoint, url)

    def test_validate_request_valid(self):
        """Test validating a valid request payload."""
        # Create a valid match fetch payload
        payload = {"matchid": 123456}
        endpoint = "/MatchWebMetoder.aspx/GetMatch"

        # Validation should succeed
        result = validate_request(endpoint, payload)
        self.assertTrue(result)

    def test_validate_request_invalid(self):
        """Test validating an invalid request payload."""
        # Create an invalid match fetch payload (missing required field)
        payload = {"not_matchid": 123456}
        endpoint = "/MatchWebMetoder.aspx/GetMatch"

        # In strict mode, validation should raise an exception
        with self.assertRaises(ValidationError):
            validate_request(endpoint, payload)

        # In non-strict mode, validation should return False
        ValidationConfig.strict_mode = False
        result = validate_request(endpoint, payload)
        self.assertFalse(result)

    def test_validate_request_no_schema(self):
        """Test validating a request with no schema."""
        payload = {"some_field": "some_value"}
        endpoint = "/NonExistentEndpoint"

        # In strict mode, validation should raise an exception
        with self.assertRaises(ValueError):
            validate_request(endpoint, payload)

        # In non-strict mode, validation should return False
        ValidationConfig.strict_mode = False
        result = validate_request(endpoint, payload)
        self.assertFalse(result)

    def test_validate_request_disabled(self):
        """Test validating a request with validation disabled."""
        # Create an invalid payload
        payload = {"not_matchid": 123456}
        endpoint = "/MatchWebMetoder.aspx/GetMatch"

        # Disable validation
        ValidationConfig.enable_validation = False

        # Validation should succeed even with invalid payload
        result = validate_request(endpoint, payload)
        self.assertTrue(result)



if __name__ == "__main__":
    unittest.main()
