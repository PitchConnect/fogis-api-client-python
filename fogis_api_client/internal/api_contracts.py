"""
API contract definitions for FOGIS API client.

This module contains JSON Schema definitions for the API contracts that must be
maintained when interacting with the FOGIS API. These schemas define the expected
structure of data sent to and received from the API.

The schemas are used for:
1. Validating request payloads before sending to the API
2. Validating response data from the API
3. Testing API interactions to ensure contract compliance
4. Documenting the required data structures
"""
import logging
import re
from typing import Any, Dict, Optional

import jsonschema
from jsonschema import ValidationError

# Configure logging
logger = logging.getLogger(__name__)


class ValidationConfig:
    """
    Configuration options for API validation.

    Attributes:
        enable_validation (bool): Whether to enable validation (default: True)
        strict_mode (bool): Whether to raise exceptions on validation failure (default: True)
        log_validation_success (bool): Whether to log successful validations (default: True)
    """

    enable_validation = True
    strict_mode = True
    log_validation_success = True


# Schema for match result reporting (nested format)
MATCH_RESULT_NESTED_SCHEMA = {
    "type": "object",
    "required": ["matchresultatListaJSON"],
    "properties": {
        "matchresultatListaJSON": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["matchid", "matchresultattypid", "matchlag1mal", "matchlag2mal", "wo", "ow", "ww"],
                "properties": {
                    "matchid": {"type": "integer"},
                    "matchresultattypid": {"type": "integer", "enum": [1, 2]},  # 1=fulltime, 2=halftime
                    "matchlag1mal": {"type": "integer", "minimum": 0},
                    "matchlag2mal": {"type": "integer", "minimum": 0},
                    "wo": {"type": "boolean"},
                    "ow": {"type": "boolean"},
                    "ww": {"type": "boolean"},
                },
                "additionalProperties": False,
            },
        }
    },
    "additionalProperties": False,
}

# Schema for match result reporting (flat format)
MATCH_RESULT_FLAT_SCHEMA = {
    "type": "object",
    "required": ["matchid", "hemmamal", "bortamal"],
    "properties": {
        "matchid": {"type": "integer"},
        "hemmamal": {"type": "integer", "minimum": 0},
        "bortamal": {"type": "integer", "minimum": 0},
        "halvtidHemmamal": {"type": "integer", "minimum": 0},
        "halvtidBortamal": {"type": "integer", "minimum": 0},
    },
    "additionalProperties": False,
}

# Schema for match event reporting
MATCH_EVENT_SCHEMA = {
    "type": "object",
    "required": ["matchid", "period", "matchhandelsetypid", "matchminut", "matchlagid"],
    "properties": {
        "matchid": {"type": "integer"},
        "matchhandelseid": {"type": "integer"},
        "matchhandelsetypid": {"type": "integer"},
        "matchhandelsetypnamn": {"type": "string"},
        "matchminut": {"type": "integer", "minimum": 0},
        "matchlagid": {"type": "integer"},
        "matchlagnamn": {"type": "string"},
        "spelareid": {"type": ["integer", "null"]},
        "spelarenamn": {"type": ["string", "null"]},
        "hemmamal": {"type": ["integer", "null"], "minimum": 0},
        "bortamal": {"type": ["integer", "null"], "minimum": 0},
        # Common properties
        "assisterande": {"type": ["string", "null"]},
        "assisterandeid": {"type": ["integer", "null"]},
        "period": {"type": "integer", "minimum": 1},
        "mal": {"type": ["boolean", "null"]},
        "strafflage": {"type": ["string", "null"]},
        "straffriktning": {"type": ["string", "null"]},
        "straffresultat": {"type": ["string", "null"]},
        # Default values for rarely used fields
        "sekund": {"type": ["integer", "null"], "default": 0},
        "planpositionx": {"type": ["string", "null"], "default": "-1"},
        "planpositiony": {"type": ["string", "null"], "default": "-1"},
        "relateradTillMatchhandelseID": {"type": ["integer", "null"], "default": 0},
        "spelareid2": {"type": ["integer", "null"], "default": -1},
        "matchdeltagareid2": {"type": ["integer", "null"], "default": -1},
    },
    "additionalProperties": False,
}

# Schema for match event deletion
MATCH_EVENT_DELETE_SCHEMA = {
    "type": "object",
    "required": ["matchhandelseid"],
    "properties": {"matchhandelseid": {"type": "integer"}},
    "additionalProperties": False,
}

# Schema for marking match reporting as finished
MARK_REPORTING_FINISHED_SCHEMA = {
    "type": "object",
    "required": ["matchid"],
    "properties": {"matchid": {"type": "integer"}},
    "additionalProperties": False,
}

# Schema for team official action reporting
TEAM_OFFICIAL_ACTION_SCHEMA = {
    "type": "object",
    "required": ["matchid", "matchlagid", "matchlagledareid", "matchlagledaretypid"],
    "properties": {
        "matchid": {"type": "integer"},
        "matchlagid": {"type": "integer"},
        "matchlagledareid": {"type": "integer"},
        "matchminut": {"type": ["integer", "null"], "minimum": 0},
        "matchlagledaretypid": {"type": "integer"},
    },
    "additionalProperties": False,
}

# Schema for match participant update
MATCH_PARTICIPANT_SCHEMA = {
    "type": "object",
    "required": ["matchdeltagareid", "trojnummer", "lagdelid"],
    "properties": {
        "matchdeltagareid": {"type": "integer"},
        "trojnummer": {"type": "integer"},
        "lagdelid": {"type": "integer"},
        "lagkapten": {"type": "boolean"},
        "ersattare": {"type": "boolean"},
        "positionsnummerhv": {"type": "integer"},
        "arSpelandeLedare": {"type": "boolean"},
        "ansvarig": {"type": "boolean"},
    },
    "additionalProperties": False,
}

# Schema for match list filter
MATCH_LIST_FILTER_SCHEMA = {
    "type": "object",
    "properties": {
        "filter": {
            "type": "object",
            "properties": {
                "datumFran": {"type": "string", "format": "date"},
                "datumTill": {"type": "string", "format": "date"},
                "datumTyp": {"type": "integer"},
                "typ": {"type": "string"},
                "status": {"type": "array", "items": {"type": "string"}},
                "alderskategori": {"type": "array", "items": {"type": "integer"}},
                "kon": {"type": "array", "items": {"type": "integer"}},
                "sparadDatum": {"type": "string", "format": "date"},
            },
        }
    },
    "required": ["filter"],
    "additionalProperties": False,
}

# Schema for match fetch
MATCH_FETCH_SCHEMA = {
    "type": "object",
    "required": ["matchid"],
    "properties": {"matchid": {"type": "integer"}},
    "additionalProperties": False,
}

# Dictionary mapping API endpoints to their request schemas
REQUEST_SCHEMAS = {
    # Match result endpoints
    "/MatchWebMetoder.aspx/SparaMatchresultatLista": MATCH_RESULT_NESTED_SCHEMA,
    # Match event endpoints
    "/MatchWebMetoder.aspx/SparaMatchhandelse": MATCH_EVENT_SCHEMA,
    "/MatchWebMetoder.aspx/RaderaMatchhandelse": MATCH_EVENT_DELETE_SCHEMA,
    # Match reporting endpoints
    "/MatchWebMetoder.aspx/SparaMatchGodkannDomarrapport": MARK_REPORTING_FINISHED_SCHEMA,
    # Team official action endpoints
    "/MatchWebMetoder.aspx/SparaMatchlagledare": TEAM_OFFICIAL_ACTION_SCHEMA,
    # Match participant endpoints
    "/MatchWebMetoder.aspx/SparaMatchdeltagare": MATCH_PARTICIPANT_SCHEMA,
    # Match list endpoints
    "/MatchWebMetoder.aspx/GetMatcherAttRapportera": MATCH_LIST_FILTER_SCHEMA,
    # Match fetch endpoints
    "/MatchWebMetoder.aspx/GetMatch": MATCH_FETCH_SCHEMA,
    "/MatchWebMetoder.aspx/GetMatchdeltagareLista": MATCH_FETCH_SCHEMA,
    "/MatchWebMetoder.aspx/GetMatchfunktionarerLista": MATCH_FETCH_SCHEMA,
    "/MatchWebMetoder.aspx/GetMatchhandelselista": MATCH_FETCH_SCHEMA,
    "/MatchWebMetoder.aspx/GetMatchresultatlista": MATCH_FETCH_SCHEMA,
}

# Dictionary mapping API endpoints to their response schemas
# Note: These are minimal schemas that only validate the structure, not the content
RESPONSE_SCHEMAS = {
    # These would be defined similarly to REQUEST_SCHEMAS
    # For now, we'll focus on request validation
}


def extract_endpoint_from_url(url: str) -> str:
    """
    Extracts the endpoint path from a full URL.

    Args:
        url: The full URL (e.g., 'https://fogis.svenskfotboll.se/MatchWebMetoder.aspx/SparaMatchresultatLista')

    Returns:
        str: The endpoint path (e.g., '/MatchWebMetoder.aspx/SparaMatchresultatLista')
    """
    # Use regex to extract the endpoint path
    match = re.search(r"(/[^/]+\.aspx/[^/]+)$", url)
    if match:
        return match.group(1)

    # Fallback: just return the URL as is
    return url


def validate_request(endpoint: str, payload: Dict[str, Any]) -> bool:
    """
    Validates a request payload against the schema for the given endpoint.

    Args:
        endpoint: The API endpoint path (e.g., '/MatchWebMetoder.aspx/SparaMatchresultatLista')
        payload: The request payload to validate

    Returns:
        bool: True if the payload is valid, False otherwise

    Raises:
        ValidationError: If the payload does not match the schema and strict_mode is True
        ValueError: If the endpoint does not have a defined schema and strict_mode is True
    """
    # Skip validation if disabled
    if not ValidationConfig.enable_validation:
        return True

    # Check if schema exists for this endpoint
    if endpoint not in REQUEST_SCHEMAS:
        message = f"No schema defined for endpoint: {endpoint}"
        logger.warning(message)
        if ValidationConfig.strict_mode:
            raise ValueError(message)
        return False

    schema = REQUEST_SCHEMAS[endpoint]

    try:
        jsonschema.validate(instance=payload, schema=schema)
        if ValidationConfig.log_validation_success:
            logger.debug(f"Payload for {endpoint} is valid")
        return True
    except ValidationError as e:
        detailed_error = f"Payload validation failed for {endpoint}: {e}"
        logger.error(detailed_error)
        if ValidationConfig.strict_mode:
            raise ValidationError(detailed_error) from e
        return False


def validate_response(endpoint: str, response_data: Dict[str, Any]) -> bool:
    """
    Validates a response from the API against the schema for the given endpoint.

    Args:
        endpoint: The API endpoint path
        response_data: The response data to validate

    Returns:
        bool: True if the response is valid, False otherwise

    Raises:
        ValidationError: If the response does not match the schema and strict_mode is True
        ValueError: If the endpoint does not have a defined schema and strict_mode is True
    """
    # Skip validation if disabled
    if not ValidationConfig.enable_validation:
        return True

    # Check if schema exists for this endpoint
    if endpoint not in RESPONSE_SCHEMAS:
        message = f"No response schema defined for endpoint: {endpoint}"
        logger.warning(message)
        # We don't raise an error for missing response schemas, even in strict mode
        return True

    schema = RESPONSE_SCHEMAS[endpoint]

    try:
        jsonschema.validate(instance=response_data, schema=schema)
        if ValidationConfig.log_validation_success:
            logger.debug(f"Response for {endpoint} is valid")
        return True
    except ValidationError as e:
        detailed_error = f"Response validation failed for {endpoint}: {e}"
        logger.error(detailed_error)
        if ValidationConfig.strict_mode:
            raise ValidationError(detailed_error) from e
        return False


def convert_flat_to_nested_match_result(flat_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a flat match result structure to the nested structure required by the API.

    Args:
        flat_data: The flat match result data with fields like 'hemmamal' and 'bortamal'

    Returns:
        Dict[str, Any]: The nested structure with 'matchresultatListaJSON' array

    Raises:
        ValueError: If required fields are missing
    """
    # Validate the flat data against the flat schema
    try:
        jsonschema.validate(instance=flat_data, schema=MATCH_RESULT_FLAT_SCHEMA)
    except ValidationError as e:
        raise ValueError(f"Invalid flat match result data: {e}")

    # Extract fields from the flat data
    match_id = flat_data["matchid"]
    fulltime_home = flat_data["hemmamal"]
    fulltime_away = flat_data["bortamal"]
    halftime_home = flat_data.get("halvtidHemmamal", 0)
    halftime_away = flat_data.get("halvtidBortamal", 0)

    # Create the nested structure
    nested_data = {
        "matchresultatListaJSON": [
            {
                "matchid": match_id,
                "matchresultattypid": 1,  # Full time
                "matchlag1mal": fulltime_home,
                "matchlag2mal": fulltime_away,
                "wo": False,
                "ow": False,
                "ww": False,
            },
            {
                "matchid": match_id,
                "matchresultattypid": 2,  # Half-time
                "matchlag1mal": halftime_home,
                "matchlag2mal": halftime_away,
                "wo": False,
                "ow": False,
                "ww": False,
            },
        ]
    }

    # Validate the nested data against the nested schema
    try:
        jsonschema.validate(instance=nested_data, schema=MATCH_RESULT_NESTED_SCHEMA)
    except ValidationError as e:
        raise ValueError(f"Generated nested match result data is invalid: {e}")

    return nested_data


def get_schema_for_endpoint(endpoint: str) -> Optional[Dict[str, Any]]:
    """
    Returns the request schema for the given endpoint.

    Args:
        endpoint: The API endpoint path

    Returns:
        Optional[Dict[str, Any]]: The schema for the endpoint, or None if not found
    """
    return REQUEST_SCHEMAS.get(endpoint)
