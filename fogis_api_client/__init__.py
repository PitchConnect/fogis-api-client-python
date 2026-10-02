"""Client for FOGIS, the Swedish Football Association's referee system.

How FOGIS actually behaves is documented in docs/FOGIS_API.md;
this package follows that file, not the 0.x code.
"""

from importlib.metadata import version

from .checks import Problem, check_report
from .client import FogisClient
from .compat import FogisApiClient
from .enums import AssignmentStatus, EventType, FootballType, ResultType
from .errors import (
    FogisAPIRequestError,
    FogisAuthServiceUnavailableError,
    FogisDataError,
    FogisError,
    FogisInvalidCredentialsError,
    FogisLoginError,
    FogisRejectedError,
    FogisSessionExpiredError,
)
from .models import (
    Assignment,
    CautionRecord,
    LineupChange,
    LineupEntry,
    Match,
    MatchEvent,
    MatchResult,
    MatchTeam,
    TeamOfficial,
)
from .session import FogisSession
from .writes import DryRun, FogisWriteCancelled, next_score

__version__ = version("fogis-api-client-timmyBird")

__all__ = [
    "Assignment",
    "AssignmentStatus",
    "CautionRecord",
    "DryRun",
    "EventType",
    "FogisAPIRequestError",
    "FogisApiClient",
    "FogisAuthServiceUnavailableError",
    "FogisClient",
    "FogisDataError",
    "FogisError",
    "FogisInvalidCredentialsError",
    "FogisLoginError",
    "FogisRejectedError",
    "FogisSession",
    "FogisSessionExpiredError",
    "FogisWriteCancelled",
    "FootballType",
    "LineupChange",
    "LineupEntry",
    "Match",
    "MatchEvent",
    "MatchResult",
    "MatchTeam",
    "Problem",
    "ResultType",
    "TeamOfficial",
    "__version__",
    "check_report",
    "next_score",
]
