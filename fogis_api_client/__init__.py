"""FOGIS API Client package.

This package provides a client for interacting with the FOGIS API.
"""

from fogis_api_client.api_contracts import (
    ValidationConfig,
    convert_flat_to_nested_match_result,
    validate_request,
    validate_response,
)
from fogis_api_client.event_types import EVENT_TYPES
# Import from the public API client for backward compatibility
from fogis_api_client.public_api_client import PublicApiClient as FogisApiClient
from fogis_api_client.public_api_client import FogisAPIRequestError, FogisDataError, FogisLoginError
from fogis_api_client.logging_config import (
    SensitiveFilter,
    add_sensitive_filter,
    configure_logging,
    get_log_levels,
    get_logger,
    set_log_level,
)
from fogis_api_client.types import (
    CookieDict,
    EventDict,
    MatchDict,
    MatchListResponse,
    MatchParticipantDict,
    MatchResultDict,
    OfficialActionDict,
    OfficialDict,
    PlayerDict,
    TeamPlayersResponse,
)

__all__ = [
    # API Client
    "FogisApiClient",
    "FogisLoginError",
    "FogisAPIRequestError",
    "FogisDataError",
    "EVENT_TYPES",
    # Type definitions
    "CookieDict",
    "EventDict",
    "MatchDict",
    "MatchListResponse",
    "MatchParticipantDict",
    "MatchResultDict",
    "OfficialActionDict",
    "OfficialDict",
    "PlayerDict",
    "TeamPlayersResponse",
    # Logging utilities
    "configure_logging",
    "get_logger",
    "set_log_level",
    "get_log_levels",
    "add_sensitive_filter",
    "SensitiveFilter",
    # Validation utilities
    "ValidationConfig",
    "validate_request",
    "validate_response",
    "convert_flat_to_nested_match_result",
]
