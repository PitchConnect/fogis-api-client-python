"""
Tests for the API validation layer.

This module contains tests for the API validation functionality.
"""
import unittest
from unittest.mock import MagicMock, patch

from jsonschema import ValidationError

from fogis_api_client.api_contracts import (
    ValidationConfig,
    extract_endpoint_from_url,
    validate_request,
    validate_response,
)
from fogis_api_client.fogis_api_client import FogisApiClient, FogisDataError


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

    @patch("fogis_api_client.fogis_api_client.requests.Session")
    def test_api_request_validation_success(self, mock_session):
        """Test API request with successful validation."""
        # Create a mock client
        client = FogisApiClient(username="test", password="test")
        client.cookies = {"cookie1": "value1"}  # Add cookies to skip login

        # Mock the session's post method
        mock_session_instance = mock_session.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = {"d": '{"matchid": 123456, "hemmalag": "Team A", "bortalag": "Team B"}'}
        mock_response.raise_for_status.return_value = None
        mock_session_instance.post.return_value = mock_response

        # Make an API request with valid payload
        url = f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatch"
        payload = {"matchid": 123456}
        response_data = client._api_request(url, payload)

        # Verify the response
        self.assertEqual(response_data, {"matchid": 123456, "hemmalag": "Team A", "bortalag": "Team B"})
        mock_session_instance.post.assert_called_once()

    @patch("fogis_api_client.fogis_api_client.requests.Session")
    def test_api_request_validation_failure(self, mock_session):
        """Test API request with validation failure."""
        # Create a mock client
        client = FogisApiClient(username="test", password="test")
        client.cookies = {"cookie1": "value1"}  # Add cookies to skip login

        # Make an API request with invalid payload
        url = f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatch"
        payload = {"not_matchid": 123456}  # Invalid payload

        # In strict mode, validation should raise an exception
        with self.assertRaises(FogisDataError):
            client._api_request(url, payload)

        # In non-strict mode, validation should not raise an exception
        ValidationConfig.strict_mode = False
        
        # Mock the session's post method for non-strict mode test
        mock_session_instance = mock_session.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = {"d": '{"matchid": 123456, "hemmalag": "Team A", "bortalag": "Team B"}'}
        mock_response.raise_for_status.return_value = None
        mock_session_instance.post.return_value = mock_response
        
        # Request should succeed in non-strict mode
        response_data = client._api_request(url, payload)
        self.assertEqual(response_data, {"matchid": 123456, "hemmalag": "Team A", "bortalag": "Team B"})


if __name__ == "__main__":
    unittest.main()
