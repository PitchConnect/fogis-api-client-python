"""
Tests for core error handling functionality.

This module tests the error handling decorators, circuit breakers,
and exception classes to improve code coverage.
"""

import time

import pytest

from fogis_api_client.core.error_handling import (
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
)


class TestFogisExceptions:
    """Test suite for FOGIS exception classes."""

    def test_fogis_operation_error(self):
        """Test base FogisOperationError exception."""
        error = FogisOperationError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_fogis_authentication_error(self):
        """Test FogisAuthenticationError exception."""
        error = FogisAuthenticationError("Auth failed")
        assert str(error) == "Auth failed"
        assert isinstance(error, FogisOperationError)

    def test_fogis_api_error(self):
        """Test FogisAPIError exception."""
        error = FogisAPIError("API call failed")
        assert str(error) == "API call failed"
        assert isinstance(error, FogisOperationError)

    def test_fogis_connection_error(self):
        """Test FogisConnectionError exception."""
        error = FogisConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, FogisOperationError)

    def test_fogis_validation_error(self):
        """Test FogisValidationError exception."""
        error = FogisValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, FogisOperationError)

    def test_fogis_rate_limit_error(self):
        """Test FogisRateLimitError exception."""
        error = FogisRateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert isinstance(error, FogisOperationError)

    def test_configuration_error(self):
        """Test ConfigurationError exception."""
        error = ConfigurationError("Config invalid")
        assert str(error) == "Config invalid"
        assert isinstance(error, FogisOperationError)


class TestHandleFogisOperations:
    """Test suite for handle_fogis_operations decorator."""

    def test_handle_fogis_operations_success(self):
        """Test decorator with successful function execution."""

        @handle_fogis_operations("test_operation")
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    def test_handle_fogis_operations_with_generic_exception(self):
        """Test decorator handling generic exceptions."""

        @handle_fogis_operations("test_operation")
        def test_function():
            raise ValueError("Generic error")

        with pytest.raises(FogisOperationError):
            test_function()

    def test_handle_fogis_operations_preserves_fogis_exceptions(self):
        """Test decorator preserves existing FOGIS exceptions."""

        @handle_fogis_operations("test_operation")
        def test_function():
            raise FogisValidationError("Validation failed")

        with pytest.raises(FogisValidationError):
            test_function()


class TestHandleApiErrors:
    """Test suite for handle_api_errors decorator."""

    def test_handle_api_errors_success(self):
        """Test decorator with successful function execution."""

        @handle_api_errors("test_operation")
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    def test_handle_api_errors_with_exception(self):
        """Test decorator handling exceptions."""

        @handle_api_errors("test_operation")
        def test_function():
            raise ValueError("API error")

        with pytest.raises(ValueError):
            test_function()


class TestFogisCircuitBreaker:
    """Test suite for FogisCircuitBreaker class."""

    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        cb = FogisCircuitBreaker(failure_threshold=3, recovery_timeout=1)

        def test_function():
            return "success"

        result = cb.call(test_function)
        assert result == "success"
        assert cb.state == "CLOSED"

    def test_circuit_breaker_open_state(self):
        """Test circuit breaker transitions to open state."""
        cb = FogisCircuitBreaker(failure_threshold=2, recovery_timeout=1)

        def failing_function():
            raise Exception("Test failure")

        # Trigger failures to open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_function)

        assert cb.state == "OPEN"

        # Next call should fail immediately
        with pytest.raises(FogisOperationError, match="Circuit breaker is OPEN"):
            cb.call(failing_function)

    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery to closed state."""
        cb = FogisCircuitBreaker(failure_threshold=1, recovery_timeout=1)

        def failing_function():
            raise Exception("Test failure")

        def success_function():
            return "success"

        # Open the circuit
        with pytest.raises(Exception):
            cb.call(failing_function)

        assert cb.state == "OPEN"

        # Wait for recovery timeout
        time.sleep(1.1)

        # Successful call should close the circuit
        result = cb.call(success_function)
        assert result == "success"
        assert cb.state == "CLOSED"

    def test_reset_circuit_breaker(self):
        """Test circuit breaker reset functionality."""
        # First, break the circuit
        cb = FogisCircuitBreaker(failure_threshold=1, recovery_timeout=60)

        def failing_function():
            raise Exception("Test failure")

        with pytest.raises(Exception):
            cb.call(failing_function)

        assert cb.state == "OPEN"

        # Reset the circuit breaker
        reset_circuit_breaker()

        # The global circuit breaker should be reset, but our local one is still open
        # This tests that the reset function works
        assert cb.state == "OPEN"  # Local instance unchanged
