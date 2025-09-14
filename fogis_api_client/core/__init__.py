"""
Core modules for FOGIS API Client.

This package contains the enhanced logging and error handling infrastructure
following the v2.1.0 standard, specifically designed for FOGIS API operations.
"""

from .enhanced_logging_config import (
    configure_enhanced_logging,
    get_enhanced_logger,
    log_error_context,
    log_fogis_metrics,
)
from .error_handling import (
    ConfigurationError,
    FogisAPIError,
    FogisAuthenticationError,
    FogisCircuitBreaker,
    FogisConnectionError,
    FogisOperationError,
    FogisRateLimitError,
    FogisValidationError,
    handle_api_errors,
    handle_fogis_operations,
    reset_circuit_breaker,
    safe_fogis_operation,
    validate_fogis_parameters,
)

__all__ = [
    # Error handling
    "ConfigurationError",
    "FogisAPIError",
    "FogisAuthenticationError",
    "FogisCircuitBreaker",
    "FogisConnectionError",
    "FogisOperationError",
    "FogisRateLimitError",
    "FogisValidationError",
    "handle_api_errors",
    "handle_fogis_operations",
    "reset_circuit_breaker",
    "safe_fogis_operation",
    "validate_fogis_parameters",
    # Enhanced logging
    "configure_enhanced_logging",
    "get_enhanced_logger",
    "log_error_context",
    "log_fogis_metrics",
]
