"""
Tests for CLI API client functionality.

This module tests the MockServerApiClient to improve code coverage
for the CLI API client components.
"""

from unittest.mock import Mock, patch

from fogis_api_client.cli.api_client import MockServerApiClient


class TestMockServerApiClient:
    """Test suite for MockServerApiClient."""

    def test_init_default_values(self):
        """Test client initialization with default values."""
        client = MockServerApiClient()
        assert client.host == "localhost"
        assert client.port == 5001
        assert client.base_url == "http://localhost:5001"

    def test_init_custom_values(self):
        """Test client initialization with custom values."""
        client = MockServerApiClient(host="example.com", port=8080)
        assert client.host == "example.com"
        assert client.port == 8080
        assert client.base_url == "http://example.com:8080"

    @patch("fogis_api_client.cli.api_client.requests.get")
    def test_get_status_success(self, mock_get):
        """Test successful status retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "running", "uptime": 123}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = MockServerApiClient()
        result = client.get_status()

        assert result == {"status": "running", "uptime": 123}
        mock_get.assert_called_once_with("http://localhost:5001/api/cli/status", timeout=0.8)

    def test_get_status_connection_error(self):
        """Test status retrieval with connection error returns error dict."""
        client = MockServerApiClient()

        # This will fail because no server is running, but should return error dict
        result = client.get_status()

        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "message" in result

    def test_get_history_connection_error(self):
        """Test history retrieval with connection error returns empty list."""
        client = MockServerApiClient()

        # This will fail because no server is running, but should return empty list
        result = client.get_history()

        assert isinstance(result, list)
        assert result == []

    def test_clear_history_connection_error(self):
        """Test history clearing with connection error returns error dict."""
        client = MockServerApiClient()

        # This will fail because no server is running, but should return error dict
        result = client.clear_history()

        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "message" in result

    def test_get_validation_status_connection_error(self):
        """Test validation status retrieval with connection error returns True."""
        client = MockServerApiClient()

        # This will fail because no server is running, but should return True (default)
        result = client.get_validation_status()

        assert result is True

    def test_set_validation_status_connection_error(self):
        """Test validation status setting with connection error returns error dict."""
        client = MockServerApiClient()

        # This will fail because no server is running, but should return error dict
        result = client.set_validation_status(False)

        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "message" in result

    def test_test_endpoint_connection_error(self):
        """Test endpoint testing with connection error returns error dict."""
        client = MockServerApiClient()

        # This will fail because no server is running, but should return error dict
        result = client.test_endpoint("/api/test", "GET")

        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "message" in result

    def test_base_url_construction(self):
        """Test base URL construction with different inputs."""
        # Test with IP address
        client = MockServerApiClient(host="192.168.1.1", port=3000)
        assert client.base_url == "http://192.168.1.1:3000"

        # Test with domain name
        client = MockServerApiClient(host="api.example.com", port=443)
        assert client.base_url == "http://api.example.com:443"

        # Test with localhost
        client = MockServerApiClient(host="localhost", port=8080)
        assert client.base_url == "http://localhost:8080"

    def test_test_endpoint_different_methods(self):
        """Test endpoint testing with different HTTP methods."""
        client = MockServerApiClient()

        # Test GET method
        result = client.test_endpoint("/api/test", "GET")
        assert isinstance(result, dict)
        assert result["status"] == "error"  # Will fail due to no server

        # Test POST method
        result = client.test_endpoint("/api/test", "POST", {"data": "test"})
        assert isinstance(result, dict)
        assert result["status"] == "error"  # Will fail due to no server

        # Test PUT method
        result = client.test_endpoint("/api/test", "PUT", {"data": "test"})
        assert isinstance(result, dict)
        assert result["status"] == "error"  # Will fail due to no server

        # Test DELETE method
        result = client.test_endpoint("/api/test", "DELETE")
        assert isinstance(result, dict)
        assert result["status"] == "error"  # Will fail due to no server

    def test_test_endpoint_unsupported_method(self):
        """Test endpoint testing with unsupported HTTP method."""
        client = MockServerApiClient()

        # Test unsupported method
        result = client.test_endpoint("/api/test", "PATCH")
        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "Unsupported method" in result["message"]
