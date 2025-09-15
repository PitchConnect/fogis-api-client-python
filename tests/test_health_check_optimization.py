"""
Tests for health check logging optimization.

This module tests that health check endpoints generate minimal, optimized logging
instead of verbose multi-line output.
"""

import json
import logging
import time
from unittest.mock import patch

from fogis_api_client_http_wrapper import app as wrapper_app
from fogis_api_gateway import app as gateway_app


class TestHealthCheckOptimization:
    """Test suite for health check logging optimization."""

    def test_gateway_health_check_optimized_logging(self, caplog):
        """Test that gateway health check generates single optimized log line."""
        with gateway_app.test_client() as client:
            with caplog.at_level(logging.INFO):
                response = client.get("/health")

                # Verify response is successful
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["status"] in ["healthy", "degraded"]
                assert data["service"] == "fogis-api-client"

                # Verify optimized logging - should have exactly one health check log
                health_logs = [
                    record for record in caplog.records if "Health check" in record.message and record.levelname == "INFO"
                ]

                assert len(health_logs) == 1, f"Expected 1 health check log, got {len(health_logs)}"

                log_message = health_logs[0].message
                assert log_message.startswith("✅ Health check OK (")
                assert log_message.endswith("s)")
                assert "duration" not in log_message.lower() or "(" in log_message

    def test_wrapper_health_check_optimized_logging(self, caplog):
        """Test that wrapper health check generates single optimized log line."""
        with wrapper_app.test_client() as client:
            with caplog.at_level(logging.INFO):
                response = client.get("/health")

                # Verify response is successful
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["status"] == "healthy"
                assert data["service"] == "fogis-api-client"

                # Verify optimized logging - should have exactly one health check log
                health_logs = [
                    record for record in caplog.records if "Health check" in record.message and record.levelname == "INFO"
                ]

                assert len(health_logs) == 1, f"Expected 1 health check log, got {len(health_logs)}"

                log_message = health_logs[0].message
                assert log_message.startswith("✅ Health check OK (")
                assert log_message.endswith("s)")

    def test_gateway_health_check_error_logging(self, caplog):
        """Test that gateway health check error generates single optimized error log."""
        with gateway_app.test_client() as client:
            with caplog.at_level(logging.ERROR):
                # Mock an exception in the health check
                with patch("fogis_api_gateway.datetime") as mock_datetime:
                    mock_datetime.now.side_effect = Exception("Test error")

                    response = client.get("/health")

                    # Verify response still returns 200 (for Docker health checks)
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data["status"] == "warning"

                    # Verify optimized error logging
                    error_logs = [
                        record
                        for record in caplog.records
                        if "Health check FAILED" in record.message and record.levelname == "ERROR"
                    ]

                    assert len(error_logs) == 1, f"Expected 1 error log, got {len(error_logs)}"

                    log_message = error_logs[0].message
                    assert log_message.startswith("❌ Health check FAILED (")
                    assert "Test error" in log_message

    def test_wrapper_health_check_error_logging(self, caplog):
        """Test that wrapper health check error generates single optimized error log."""
        with wrapper_app.test_client() as client:
            with caplog.at_level(logging.ERROR):
                # Mock an exception in the health check
                with patch("fogis_api_client_http_wrapper.datetime") as mock_datetime:
                    mock_datetime.now.side_effect = Exception("Test error")

                    response = client.get("/health")

                    # Verify response still returns 200 (for Docker health checks)
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data["status"] == "warning"

                    # Verify optimized error logging
                    error_logs = [
                        record
                        for record in caplog.records
                        if "Health check FAILED" in record.message and record.levelname == "ERROR"
                    ]

                    assert len(error_logs) == 1, f"Expected 1 error log, got {len(error_logs)}"

                    log_message = error_logs[0].message
                    assert log_message.startswith("❌ Health check FAILED (")
                    assert "Test error" in log_message

    def test_health_check_timing_accuracy(self, caplog):
        """Test that health check timing is accurate and properly formatted."""
        with gateway_app.test_client() as client:
            with caplog.at_level(logging.INFO):
                start_time = time.time()
                response = client.get("/health")
                end_time = time.time()

                assert response.status_code == 200

                # Verify timing is reasonable
                health_logs = [record for record in caplog.records if "Health check OK" in record.message]

                assert len(health_logs) == 1
                log_message = health_logs[0].message

                # Extract duration from log message
                import re

                duration_match = re.search(r"\((\d+\.\d+)s\)", log_message)
                assert duration_match, f"Duration not found in log: {log_message}"

                logged_duration = float(duration_match.group(1))
                actual_duration = end_time - start_time

                # Duration should be reasonable (within 1 second of actual)
                assert logged_duration <= actual_duration + 0.1
                assert logged_duration >= 0.0

    def test_no_verbose_logging_patterns(self, caplog):
        """Test that verbose logging patterns are not present."""
        with gateway_app.test_client() as client:
            with caplog.at_level(logging.INFO):
                response = client.get("/health")

                assert response.status_code == 200

                # Check that verbose patterns are NOT present
                all_messages = [record.message for record in caplog.records]

                # These patterns should NOT appear in optimized logging
                verbose_patterns = [
                    "Health check requested from",
                    "Request headers:",
                    "Health check response:",
                    "Debug endpoint",
                ]

                for pattern in verbose_patterns:
                    matching_logs = [msg for msg in all_messages if pattern in msg]
                    assert len(matching_logs) == 0, f"Found verbose pattern '{pattern}' in logs: {matching_logs}"

    def test_log_reduction_percentage(self, caplog):
        """Test that log reduction meets the 67% target."""
        with gateway_app.test_client() as client:
            with caplog.at_level(logging.INFO):
                # Make multiple health check requests
                for _ in range(5):
                    response = client.get("/health")
                    assert response.status_code == 200

                # Count health check related logs
                health_related_logs = [
                    record
                    for record in caplog.records
                    if any(keyword in record.message.lower() for keyword in ["health", "check", "✅", "❌"])
                ]

                # Should have exactly 5 optimized log entries (one per request)
                assert len(health_related_logs) == 5, f"Expected 5 health logs, got {len(health_related_logs)}"

                # Verify all are optimized format
                for log in health_related_logs:
                    assert log.message.startswith("✅ Health check OK (")
                    assert log.message.endswith("s)")

    def test_health_check_response_structure(self):
        """Test that optimized health check maintains proper response structure."""
        with gateway_app.test_client() as client:
            response = client.get("/health")

            assert response.status_code == 200
            data = json.loads(response.data)

            # Verify essential fields are present
            required_fields = ["status", "timestamp", "service", "version", "dependencies"]
            for field in required_fields:
                assert field in data, f"Required field '{field}' missing from response"

            # Verify service identification
            assert data["service"] == "fogis-api-client"
            assert data["status"] in ["healthy", "degraded"]

            # Verify dependencies check
            assert "dependencies" in data
            assert "fogis_client" in data["dependencies"]
            assert data["dependencies"]["fogis_client"] in ["available", "unavailable"]
