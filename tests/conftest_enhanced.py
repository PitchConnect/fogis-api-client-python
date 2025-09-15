"""
Test configuration for FOGIS API Client tests with enhanced logging support.

This module provides test fixtures and configuration for enhanced logging
and circuit breaker isolation between tests.
"""

import pytest

# Import enhanced logging components if available
try:
    from fogis_api_client.core.error_handling import reset_circuit_breaker

    HAS_ENHANCED_LOGGING = True
except ImportError:
    HAS_ENHANCED_LOGGING = False


@pytest.fixture(autouse=True)
def reset_enhanced_logging():
    """Reset enhanced logging circuit breaker between tests."""
    if HAS_ENHANCED_LOGGING:
        reset_circuit_breaker()
    yield
    if HAS_ENHANCED_LOGGING:
        reset_circuit_breaker()
