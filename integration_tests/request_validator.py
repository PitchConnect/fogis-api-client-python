"""
Request validator for the mock FOGIS API server.

This module provides validation functions for API requests to ensure they match
the expected structure required by the FOGIS API.
"""

import json
import logging
from typing import Any, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RequestValidationError(Exception):
    """Exception raised when a request fails validation."""

    pass


class RequestValidator:
    """Validator for API requests to ensure they match the expected structure."""

    # Define expected request schemas for different endpoints
    SCHEMAS = {
        # Match result endpoints
        "/MatchWebMetoder.aspx/SparaMatchresultatLista": {
            "required_fields": ["matchresultatListaJSON"],
            "nested_fields": {
                "matchresultatListaJSON": [
                    {
                        "required_fields": [
                            "matchid",
                            "matchresultattypid",
                            "matchlag1mal",
                            "matchlag2mal",
                            "wo",
                            "ow",
                            "ww",
                        ]
                    }
                ]
            },
        },
        "/MatchWebMetoder.aspx/GetMatchresultatlista": {
            "required_fields": ["matchid"],
        },
        # Match event endpoints
        "/MatchWebMetoder.aspx/SparaMatchhandelse": {
            "required_fields": [
                "matchhandelseid",
                "matchid",
                "matchhandelsetypid",
                "matchminut",
                "matchlagid",
            ]
        },
        "/MatchWebMetoder.aspx/RaderaMatchhandelse": {
            "required_fields": ["matchhandelseid"],
        },
        # Team official endpoints
        "/MatchWebMetoder.aspx/SparaMatchlagledare": {
            "required_fields": ["matchid", "matchlagid", "matchlagledareid", "matchlagledaretypid"]
        },
        # Match participant endpoints
        "/MatchWebMetoder.aspx/SparaMatchdeltagare": {
            "required_fields": ["matchdeltagareid", "trojnummer"]
        },
        # Match reporting endpoints
        "/MatchWebMetoder.aspx/SparaMatchGodkannDomarrapport": {
            "required_fields": ["matchid"]
        },
        # Match fetch endpoints
        "/MatchWebMetoder.aspx/GetMatch": {
            "required_fields": ["matchid"],
        },
        "/MatchWebMetoder.aspx/GetMatchdeltagareLista": {
            "required_fields": ["matchid"],
        },
        "/MatchWebMetoder.aspx/GetMatchfunktionarerLista": {
            "required_fields": ["matchid"],
        },
        "/MatchWebMetoder.aspx/GetMatchhandelselista": {
            "required_fields": ["matchid"],
        },
    }

    @staticmethod
    def validate_request(endpoint: str, data: Dict[str, Any]) -> bool:
        """
        Validate a request against the expected schema.

        Args:
            endpoint: The API endpoint
            data: The request data

        Returns:
            bool: True if the request is valid, False otherwise

        Raises:
            RequestValidationError: If the request fails validation
        """
        # Get the schema for this endpoint
        schema = RequestValidator.SCHEMAS.get(endpoint)
        if not schema:
            logger.warning(f"No schema defined for endpoint {endpoint}")
            return True  # No schema defined, so we can't validate

        # Check required fields
        required_fields = schema.get("required_fields", [])
        for field in required_fields:
            if field not in data:
                error_msg = f"Missing required field '{field}' in request to {endpoint}"
                logger.error(error_msg)
                raise RequestValidationError(error_msg)

        # Check nested fields
        nested_fields = schema.get("nested_fields", {})
        for field, nested_schema in nested_fields.items():
            if field not in data:
                error_msg = f"Missing nested field '{field}' in request to {endpoint}"
                logger.error(error_msg)
                raise RequestValidationError(error_msg)

            # Check if the field is a list or a dict
            if isinstance(nested_schema, list) and isinstance(data[field], list):
                # Validate each item in the list
                for i, item_schema in enumerate(nested_schema):
                    if i < len(data[field]):
                        item = data[field][i]
                        item_required_fields = item_schema.get("required_fields", [])
                        for required_field in item_required_fields:
                            if required_field not in item:
                                error_msg = (
                                    f"Missing required field '{required_field}' in item {i} "
                                    f"of '{field}' in request to {endpoint}"
                                )
                                logger.error(error_msg)
                                raise RequestValidationError(error_msg)
            elif isinstance(nested_schema, dict) and isinstance(data[field], dict):
                # Validate the dict
                dict_required_fields = nested_schema.get("required_fields", [])
                for required_field in dict_required_fields:
                    if required_field not in data[field]:
                        error_msg = f"Missing required field '{required_field}' in '{field}' in request to {endpoint}"
                        logger.error(error_msg)
                        raise RequestValidationError(error_msg)

        return True

    @staticmethod
    def log_request(endpoint: str, data: Dict[str, Any]) -> None:
        """
        Log a request for debugging purposes.

        Args:
            endpoint: The API endpoint
            data: The request data
        """
        logger.info(f"Request to {endpoint}:")
        logger.info(json.dumps(data, indent=2))


def validate_match_result_request(data: Dict[str, Any]) -> bool:
    """
    Validate a match result request.

    Args:
        data: The request data

    Returns:
        bool: True if the request is valid, False otherwise

    Raises:
        RequestValidationError: If the request fails validation
    """
    # Check if the request uses the nested structure
    if "matchresultatListaJSON" in data:
        # Validate the nested structure
        match_results = data["matchresultatListaJSON"]
        if not isinstance(match_results, list) or len(match_results) == 0:
            raise RequestValidationError("matchresultatListaJSON must be a non-empty list")

        # Check each result in the list
        for i, result in enumerate(match_results):
            required_fields = [
                "matchid",
                "matchresultattypid",
                "matchlag1mal",
                "matchlag2mal",
                "wo",
                "ow",
                "ww",
            ]
            for field in required_fields:
                if field not in result:
                    raise RequestValidationError(f"Missing required field '{field}' in result {i} of matchresultatListaJSON")
        return True
    else:
        # Check for the flat structure
        required_fields = ["matchid", "hemmamal", "bortamal"]
        for field in required_fields:
            if field not in data:
                raise RequestValidationError(f"Missing required field '{field}' in match result data")
        return True


def validate_match_event_request(data: Dict[str, Any]) -> bool:
    """
    Validate a match event request.

    Args:
        data: The request data

    Returns:
        bool: True if the request is valid, False otherwise

    Raises:
        RequestValidationError: If the request fails validation
    """
    # Check required fields
    required_fields = [
        "matchhandelseid",
        "matchid",
        "matchhandelsetypid",
        "matchminut",
        "matchlagid",
    ]
    for field in required_fields:
        if field not in data:
            raise RequestValidationError(f"Missing required field '{field}' in match event data")
    return True
