"""FOGIS API Client package.

This package provides a client for interacting with the FOGIS API.
"""

from .fogis_api_client import (
    FogisApiClient,
    FogisApiError,
    FogisLoginError,
    FogisAPIRequestError,
    FogisDataError,
)
from .event_types import EVENT_TYPES
from .logging_config import (
    SensitiveFilter,
    add_sensitive_filter,
    configure_logging,
    get_log_levels,
    get_logger,
    set_log_level,
)
from .match_list_filter import MatchListFilter
from .types import (
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
    "MatchListFilter",
    "FogisApiError",
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
]
