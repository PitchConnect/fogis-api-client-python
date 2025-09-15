"""
Enhanced error handling for FOGIS API Client.

This module provides comprehensive error handling with circuit breaker patterns,
retry logic, and detailed error context for FOGIS API operations.
"""

import functools
import time
from typing import Any, Callable, Dict, Optional

import requests

from .enhanced_logging_config import get_enhanced_logger, log_error_context


# Custom exception classes for FOGIS API operations
class FogisOperationError(Exception):
    """Base exception for FOGIS API operation errors."""

    pass


class FogisAuthenticationError(FogisOperationError):
    """Exception raised when FOGIS authentication fails."""

    pass


class FogisAPIError(FogisOperationError):
    """Exception raised when FOGIS API calls fail."""

    pass


class FogisConnectionError(FogisOperationError):
    """Exception raised when connection to FOGIS fails."""

    pass


class FogisValidationError(FogisOperationError):
    """Exception raised when FOGIS data validation fails."""

    pass


class FogisRateLimitError(FogisOperationError):
    """Exception raised when FOGIS rate limits are exceeded."""

    pass


class ConfigurationError(FogisOperationError):
    """Exception raised when configuration is invalid."""

    pass


class FogisCircuitBreaker:
    """Circuit breaker for FOGIS API operations."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise FogisOperationError("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


# Global circuit breaker instance - can be reset for testing
_circuit_breaker = FogisCircuitBreaker()


def reset_circuit_breaker():
    """Reset the circuit breaker state - useful for testing."""
    global _circuit_breaker
    _circuit_breaker = FogisCircuitBreaker()


def handle_fogis_operations(operation_name: str, component: str = "fogis_operations"):
    """
    Decorator for handling FOGIS API operations with enhanced logging.

    Args:
        operation_name: Name of the operation being performed
        component: Component name for logging context
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_enhanced_logger(func.__module__, component)
            start_time = time.time()

            logger.info(f"Starting {operation_name}")

            try:
                # Execute with circuit breaker protection
                result = _circuit_breaker.call(func, *args, **kwargs)

                duration = time.time() - start_time
                logger.info(f"Successfully completed {operation_name} in {duration:.2f}s")

                return result

            except FogisOperationError as e:
                duration = time.time() - start_time
                context = {
                    "operation": operation_name,
                    "duration": duration,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                }

                log_error_context(logger, e, operation_name, context)
                raise

            except requests.exceptions.RequestException as e:
                duration = time.time() - start_time
                context = {
                    "operation": operation_name,
                    "duration": duration,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                }

                # Convert requests exceptions to appropriate FOGIS exceptions
                fogis_error = _convert_requests_error(e, operation_name)
                log_error_context(logger, fogis_error, operation_name, context)
                raise fogis_error from e

            except Exception as e:
                duration = time.time() - start_time
                context = {
                    "operation": operation_name,
                    "duration": duration,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                }

                # Wrap unexpected errors in FogisOperationError
                wrapped_error = FogisOperationError(f"Unexpected error in {operation_name}: {str(e)}")
                log_error_context(logger, wrapped_error, operation_name, context)
                raise wrapped_error from e

        return wrapper

    return decorator


def handle_api_errors(operation_name: str, component: str = "api"):
    """
    Decorator for handling API errors with enhanced logging.

    Args:
        operation_name: Name of the API operation being performed
        component: Component name for logging context
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_enhanced_logger(func.__module__, component)
            start_time = time.time()

            logger.info(f"Starting {operation_name}")

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Successfully completed {operation_name} in {duration:.2f}s")
                return result

            except Exception as e:
                duration = time.time() - start_time
                context = {
                    "operation": operation_name,
                    "duration": duration,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                }

                log_error_context(logger, e, operation_name, context)
                raise

        return wrapper

    return decorator


def safe_fogis_operation(operation: Callable, *args, max_retries: int = 3, retry_delay: float = 1.0, **kwargs) -> Any:
    """
    Execute FOGIS operation with retry logic and error handling.

    Args:
        operation: Function to execute
        *args: Arguments for the operation
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        **kwargs: Keyword arguments for the operation

    Returns:
        Result of the operation

    Raises:
        FogisOperationError: If operation fails after all retries
    """
    logger = get_enhanced_logger(__name__, "safe_operation")

    for attempt in range(max_retries + 1):
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Operation failed after {max_retries} retries: {str(e)}")
                raise FogisOperationError(f"Operation failed after {max_retries} retries") from e

            logger.warning(f"Operation attempt {attempt + 1} failed, retrying in {retry_delay}s: {str(e)}")
            time.sleep(retry_delay)


def validate_fogis_parameters(
    username: Optional[str] = None,
    password: Optional[str] = None,
    base_url: Optional[str] = None,
    cookies: Optional[Dict] = None,
) -> None:
    """
    Validate FOGIS API operation parameters.

    Args:
        username: FOGIS username
        password: FOGIS password
        base_url: FOGIS base URL
        cookies: Session cookies

    Raises:
        ConfigurationError: If parameters are invalid
    """
    if username is not None:
        if not isinstance(username, str) or not username.strip():
            raise ConfigurationError("username must be a non-empty string")

    if password is not None:
        if not isinstance(password, str) or not password.strip():
            raise ConfigurationError("password must be a non-empty string")

    if base_url is not None:
        if not isinstance(base_url, str) or not base_url.strip():
            raise ConfigurationError("base_url must be a non-empty string")
        if not (base_url.startswith("http://") or base_url.startswith("https://")):
            raise ConfigurationError("base_url must be a valid HTTP/HTTPS URL")

    if cookies is not None:
        if not isinstance(cookies, dict):
            raise ConfigurationError("cookies must be a dictionary")


def _convert_requests_error(requests_error: requests.exceptions.RequestException, operation: str) -> FogisOperationError:
    """Convert requests exception to appropriate FOGIS exception."""
    error_details = str(requests_error)

    # Connection errors
    if isinstance(requests_error, requests.exceptions.ConnectionError):
        return FogisConnectionError(f"Connection failed in {operation}: {error_details}")

    # Timeout errors
    if isinstance(requests_error, requests.exceptions.Timeout):
        return FogisConnectionError(f"Timeout in {operation}: {error_details}")

    # HTTP errors
    if isinstance(requests_error, requests.exceptions.HTTPError):
        if hasattr(requests_error, "response") and requests_error.response is not None:
            status_code = requests_error.response.status_code

            # Authentication errors
            if status_code == 401:
                return FogisAuthenticationError(f"Authentication failed in {operation}: {error_details}")

            # Rate limiting errors
            if status_code == 429:
                return FogisRateLimitError(f"Rate limit exceeded in {operation}: {error_details}")

            # Server errors
            if 500 <= status_code < 600:
                return FogisAPIError(f"FOGIS API server error in {operation}: {error_details}")

    # Generic API error
    return FogisAPIError(f"FOGIS API error in {operation}: {error_details}")
