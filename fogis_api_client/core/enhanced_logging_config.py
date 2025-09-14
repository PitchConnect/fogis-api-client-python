"""
Enhanced logging configuration for FOGIS API Client.

This module provides enterprise-grade structured logging following the v2.1.0 standard
established in the match-list-processor service. It includes service context, component
separation, location information, and comprehensive error handling for FOGIS API operations.
"""

import logging
import logging.handlers
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class FogisAPIFormatter(logging.Formatter):
    """Enhanced formatter for FOGIS API Client with structured output."""

    def __init__(self, enable_structured: bool = True):
        self.enable_structured = enable_structured
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with enhanced structure and context."""
        # Generate timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")

        # Service context
        service_name = "fogis-api-client"

        # Component context (from logger adapter or module name)
        component = getattr(record, "component", None)
        if not component:
            # Extract component from logger name
            logger_parts = record.name.split(".")
            if len(logger_parts) > 1:
                component = logger_parts[-1]
            else:
                component = "api_client"

        # Location information
        location = f"{record.filename}:{record.funcName}:{record.lineno}"

        # Filter sensitive information
        message = self._filter_sensitive_data(record.getMessage())

        if self.enable_structured:
            # Structured format: timestamp - service - component - level - location - message
            return f"{timestamp} - {service_name} - {component} - " f"{record.levelname} - {location} - {message}"
        else:
            # Simple format for console in development
            return f"[{record.levelname}] {component}:{record.funcName}:{record.lineno} - {message}"

    def _filter_sensitive_data(self, message: str) -> str:
        """Filter sensitive information from log messages."""
        patterns = [
            # API keys and tokens
            (r"(api[_-]?key|token|secret|password|pwd|client[_-]?secret)[\s=:]+[^\s&]+", r"\1=[FILTERED]"),
            # Session cookies and authentication
            (r"(session[_-]?id|auth[_-]?token|csrf[_-]?token)[\s=:]+[^\s&]+", r"\1=[FILTERED]"),
            # FOGIS specific credentials
            (r"(username|user[_-]?id|login)[\s=:]+[^\s&]+", r"\1=[FILTERED]"),
            # URLs with sensitive parameters
            (r"(\?|&)(key|token|secret|password|session|auth)=[^&\s]+", r"\1\2=[FILTERED]"),
            # Email addresses (keep domain for debugging)
            (r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", r"***@\2"),
            # Phone numbers
            (r"(\+?[0-9]{1,3}[-.\s]?)?(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})", r"***-***-****"),
        ]

        filtered_message = message
        for pattern, replacement in patterns:
            filtered_message = re.sub(pattern, replacement, filtered_message, flags=re.IGNORECASE)

        return filtered_message


def get_enhanced_logger(name: str, component: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger for the FOGIS API Client.

    Args:
        name: Logger name (typically __name__)
        component: Optional component name for context

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Add component context if provided
    if component:
        logger = logging.LoggerAdapter(logger, {"component": component})

    return logger


def configure_enhanced_logging(
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_structured: bool = True,
    log_dir: str = "logs",
    log_file: str = "fogis-api-client.log",
) -> None:
    """
    Configure enhanced logging for FOGIS API Client.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Enable console logging
        enable_file: Enable file logging with rotation
        enable_structured: Enable structured logging format
        log_dir: Directory for log files
        log_file: Log file name
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set root logger level
    root_logger.setLevel(numeric_level)

    # Create formatter
    formatter = FogisAPIFormatter(enable_structured=enable_structured)

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Create log directory if it doesn't exist
    if enable_file:
        os.makedirs(log_dir, exist_ok=True)

    # File handler with rotation
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, log_file), maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduce verbosity of third-party libraries
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("bs4").setLevel(logging.WARNING)
    logging.getLogger("jsonschema").setLevel(logging.WARNING)

    # Log configuration success
    logger = get_enhanced_logger(__name__, "enhanced_logging_config")
    logger.info(
        f"Enhanced logging configured: level={log_level}, console={enable_console}, "
        f"file={enable_file}, structured={enable_structured}"
    )


def log_error_context(
    logger: logging.Logger, error: Exception, operation: str, context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log error with comprehensive context information.

    Args:
        logger: Logger instance
        error: Exception that occurred
        operation: Operation being performed when error occurred
        context: Additional context information
    """
    context = context or {}

    # Filter sensitive information from context
    filtered_context = {}
    for key, value in context.items():
        sensitive_keys = ["token", "key", "secret", "password", "session", "auth", "username"]
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            if isinstance(value, str):
                # Keep only first few characters for debugging
                filtered_context[key] = f"{value[:4]}***" if len(value) > 4 else "[FILTERED]"
            else:
                filtered_context[key] = "[FILTERED]"
        else:
            filtered_context[key] = value

    logger.error(
        f"Error in {operation}: {error.__class__.__name__}: {str(error)}",
        extra={"operation": operation, "error_type": error.__class__.__name__, "context": filtered_context},
        exc_info=True,
    )


def log_fogis_metrics(
    logger: logging.Logger, operation: str, processing_time: float, api_info: Dict[str, Any], success: bool = True
) -> None:
    """
    Log FOGIS API operation metrics and performance information.

    Args:
        logger: Logger instance
        operation: FOGIS API operation name
        processing_time: Time taken for processing in seconds
        api_info: Information about FOGIS API operation
        success: Whether the operation was successful
    """
    status = "success" if success else "failed"

    # Filter sensitive information from api_info
    filtered_info = {}
    for key, value in api_info.items():
        sensitive_keys = ["token", "key", "secret", "password", "session", "auth", "username"]
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            # Keep only first few characters for debugging
            if isinstance(value, str):
                filtered_info[key] = f"{value[:4]}***" if len(value) > 4 else "[FILTERED]"
            else:
                filtered_info[key] = "[FILTERED]"
        else:
            filtered_info[key] = value

    logger.info(
        f"FOGIS API operation {status}: {operation} completed in {processing_time:.3f}s",
        extra={"operation": operation, "processing_time": processing_time, "api_info": filtered_info, "success": success},
    )
