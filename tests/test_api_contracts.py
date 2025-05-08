"""
Tests for the API contracts module.

This module contains tests for the API contract validation functionality.
"""
import json
import unittest
from unittest.mock import patch

from jsonschema import ValidationError

from fogis_api_client.api_contracts import (
    MATCH_EVENT_SCHEMA,
    MATCH_RESULT_FLAT_SCHEMA,
    MATCH_RESULT_NESTED_SCHEMA,
    convert_flat_to_nested_match_result,
    validate_request,
    validate_response,
)
from fogis_api_client.fogis_api_client import FogisApiClient


class TestApiContracts(unittest.TestCase):
    """Test cases for the API contracts module."""

    def test_match_result_nested_schema_valid(self):
        """Test that a valid nested match result passes validation."""
        data = {
            "matchresultatListaJSON": [
                {
                    "matchid": 123456,
                    "matchresultattypid": 1,  # Full time
                    "matchlag1mal": 2,
                    "matchlag2mal": 1,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                },
                {
                    "matchid": 123456,
                    "matchresultattypid": 2,  # Half-time
                    "matchlag1mal": 1,
                    "matchlag2mal": 0,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                },
            ]
        }
        # This should not raise an exception
        validate_request("/MatchWebMetoder.aspx/SparaMatchresultatLista", data)

    def test_match_result_nested_schema_invalid(self):
        """Test that an invalid nested match result fails validation."""
        # Missing required field matchlag1mal
        data = {
            "matchresultatListaJSON": [
                {
                    "matchid": 123456,
                    "matchresultattypid": 1,
                    "matchlag2mal": 1,
                    "wo": False,
                    "ow": False,
                    "ww": False,
                }
            ]
        }
        with self.assertRaises(ValidationError):
            validate_request("/MatchWebMetoder.aspx/SparaMatchresultatLista", data)

    def test_match_result_flat_schema_valid(self):
        """Test that a valid flat match result passes validation."""
        data = {
            "matchid": 123456,
            "hemmamal": 2,
            "bortamal": 1,
            "halvtidHemmamal": 1,
            "halvtidBortamal": 0,
        }
        # This should not raise an exception when validating against the flat schema
        try:
            from jsonschema import validate
            validate(instance=data, schema=MATCH_RESULT_FLAT_SCHEMA)
            # If we get here, validation passed
            validation_passed = True
        except ValidationError:
            validation_passed = False
        self.assertTrue(validation_passed)

    def test_match_result_flat_schema_invalid(self):
        """Test that an invalid flat match result fails validation."""
        # Missing required field bortamal
        data = {"matchid": 123456, "hemmamal": 2}
        with self.assertRaises(ValidationError):
            json.loads(json.dumps(data), object_hook=lambda d: validate_flat_schema(d))

    def test_convert_flat_to_nested(self):
        """Test conversion from flat to nested match result structure."""
        flat_data = {
            "matchid": 123456,
            "hemmamal": 2,
            "bortamal": 1,
            "halvtidHemmamal": 1,
            "halvtidBortamal": 0,
        }
        nested_data = convert_flat_to_nested_match_result(flat_data)

        # Verify the structure
        self.assertIn("matchresultatListaJSON", nested_data)
        self.assertEqual(len(nested_data["matchresultatListaJSON"]), 2)

        # Verify full-time result
        fulltime = nested_data["matchresultatListaJSON"][0]
        self.assertEqual(fulltime["matchid"], 123456)
        self.assertEqual(fulltime["matchresultattypid"], 1)
        self.assertEqual(fulltime["matchlag1mal"], 2)
        self.assertEqual(fulltime["matchlag2mal"], 1)

        # Verify half-time result
        halftime = nested_data["matchresultatListaJSON"][1]
        self.assertEqual(halftime["matchid"], 123456)
        self.assertEqual(halftime["matchresultattypid"], 2)
        self.assertEqual(halftime["matchlag1mal"], 1)
        self.assertEqual(halftime["matchlag2mal"], 0)

    def test_match_event_schema_valid(self):
        """Test that a valid match event passes validation."""
        data = {
            "matchid": 123456,
            "matchhandelsetypid": 6,  # Regular goal
            "matchminut": 35,
            "matchlagid": 78910,
            "spelareid": 12345,
            "period": 1,
            "hemmamal": 1,
            "bortamal": 0,
        }
        # This should not raise an exception
        validate_request("/MatchWebMetoder.aspx/SparaMatchhandelse", data)

    def test_match_event_schema_invalid(self):
        """Test that an invalid match event fails validation."""
        # Missing required field matchminut
        data = {
            "matchid": 123456,
            "matchhandelsetypid": 6,
            "matchlagid": 78910,
            "spelareid": 12345,
            "period": 1,
        }
        with self.assertRaises(ValidationError):
            validate_request("/MatchWebMetoder.aspx/SparaMatchhandelse", data)

    @patch("fogis_api_client.fogis_api_client.FogisApiClient._api_request")
    def test_report_match_result_with_validation(self, mock_api_request):
        """Test that report_match_result validates the data before sending."""
        # Mock the API response
        mock_api_request.return_value = {"success": True}

        # Create a client instance
        client = FogisApiClient(username="test", password="test")

        # Test with valid flat data
        valid_data = {
            "matchid": 123456,
            "hemmamal": 2,
            "bortamal": 1,
            "halvtidHemmamal": 1,
            "halvtidBortamal": 0,
        }
        result = client.report_match_result(valid_data)
        self.assertTrue(result["success"])

        # Test with invalid flat data (missing required field)
        invalid_data = {
            "matchid": 123456,
            "hemmamal": 2,
            # Missing bortamal
        }
        with self.assertRaises(ValueError):
            client.report_match_result(invalid_data)

    @patch("fogis_api_client.fogis_api_client.FogisApiClient._api_request")
    def test_report_match_event_with_validation(self, mock_api_request):
        """Test that report_match_event validates the data before sending."""
        # Mock the API response
        mock_api_request.return_value = {"success": True, "id": 12345}

        # Create a client instance
        client = FogisApiClient(username="test", password="test")

        # Test with valid event data
        valid_data = {
            "matchid": 123456,
            "matchhandelsetypid": 6,  # Regular goal
            "matchminut": 35,
            "matchlagid": 78910,
            "spelareid": 12345,
            "period": 1,
            "hemmamal": 1,
            "bortamal": 0,
        }
        result = client.report_match_event(valid_data)
        self.assertTrue(result["success"])

        # Test with invalid event data (missing required field)
        invalid_data = {
            "matchid": 123456,
            "matchhandelsetypid": 6,
            # Missing matchminut and matchlagid
            "personid": 12345,
            "period": 1,
        }
        with self.assertRaises(ValidationError):
            client.report_match_event(invalid_data)


def validate_flat_schema(data):
    """Helper function to validate against the flat schema."""
    if isinstance(data, dict) and "matchid" in data:
        from jsonschema import validate
        validate(instance=data, schema=MATCH_RESULT_FLAT_SCHEMA)
    return data


if __name__ == "__main__":
    unittest.main()
