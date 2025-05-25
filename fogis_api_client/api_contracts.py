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

Usage:
    from fogis_api_client.api_contracts import (
        validate_request,
        validate_response,
        REQUEST_SCHEMAS,
        RESPONSE_SCHEMAS,
        ValidationConfig,
    )

    # Configure validation
    ValidationConfig.enable_validation = True
    ValidationConfig.strict_mode = True

    # Validate a request payload
    validate_request('/MatchWebMetoder.aspx/SparaMatchresultatLista', payload)

    # Validate a response
    validate_response('/MatchWebMetoder.aspx/GetMatchresultatlista', response_data)
"""
import logging
import re
import warnings
from typing import Any, Dict, Optional

import jsonschema
from jsonschema import ValidationError

# Import from internal module
from fogis_api_client.internal.api_contracts import (
    MATCH_EVENT_DELETE_SCHEMA,
    MATCH_EVENT_SCHEMA,
    MATCH_FETCH_SCHEMA,
    MATCH_LIST_FILTER_SCHEMA,
    MATCH_PARTICIPANT_SCHEMA,
    MATCH_RESULT_FLAT_SCHEMA,
    MATCH_RESULT_NESTED_SCHEMA,
    MARK_REPORTING_FINISHED_SCHEMA,
    REQUEST_SCHEMAS,
    RESPONSE_SCHEMAS,
    TEAM_OFFICIAL_ACTION_SCHEMA,
    ValidationConfig,
    convert_flat_to_nested_match_result,
    extract_endpoint_from_url,
    get_schema_for_endpoint,
    validate_request,
    validate_response,
)

# Configure logging
logger = logging.getLogger(__name__)

# Emit a deprecation warning
warnings.warn(
    "The fogis_api_client.api_contracts module is deprecated. "
    "Use fogis_api_client.internal.api_contracts instead.",
    DeprecationWarning,
    stacklevel=2
)


# ValidationConfig is imported from internal module


# All schemas and functions are imported from internal module
