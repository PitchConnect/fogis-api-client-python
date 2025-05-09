"""
API client for communicating with the mock server.

This module provides a client for communicating with the mock server's REST API.
It is used by the CLI to send commands to the server.
"""

import json
import logging
import requests
import time
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockServerApiClient:
    """
    Client for communicating with the mock server's REST API.
    """

    def __init__(self, host: str = "localhost", port: int = 5001):
        """
        Initialize the client.

        Args:
            host: The host where the mock server is running
            port: The port where the mock server is running
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    def get_status(self) -> Dict[str, Any]:
        """
        Get the server status.

        Returns:
            Dict[str, Any]: The server status
        """
        try:
            response = requests.get(f"{self.base_url}/api/cli/status")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get server status: {e}")
            return {"status": "error", "message": str(e)}

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the request history.

        Returns:
            List[Dict[str, Any]]: The request history
        """
        try:
            response = requests.get(f"{self.base_url}/api/cli/history")
            response.raise_for_status()
            return response.json().get("history", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get request history: {e}")
            return []

    def clear_history(self) -> Dict[str, Any]:
        """
        Clear the request history.

        Returns:
            Dict[str, Any]: The response from the server
        """
        try:
            response = requests.delete(f"{self.base_url}/api/cli/history")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to clear request history: {e}")
            return {"status": "error", "message": str(e)}

    def get_validation_status(self) -> bool:
        """
        Get the validation status.

        Returns:
            bool: True if validation is enabled, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/cli/validation")
            response.raise_for_status()
            return response.json().get("validation_enabled", True)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get validation status: {e}")
            return True

    def set_validation_status(self, enabled: bool) -> Dict[str, Any]:
        """
        Set the validation status.

        Args:
            enabled: True to enable validation, False to disable it

        Returns:
            Dict[str, Any]: The response from the server
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/cli/validation",
                json={"enabled": enabled},
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to set validation status: {e}")
            return {"status": "error", "message": str(e)}

    def shutdown_server(self) -> Dict[str, Any]:
        """
        Shutdown the server.

        Returns:
            Dict[str, Any]: The response from the server
        """
        try:
            response = requests.post(f"{self.base_url}/api/cli/shutdown")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to shutdown server: {e}")
            return {"status": "error", "message": str(e)}

    def wait_for_server(self, timeout: int = 10) -> bool:
        """
        Wait for the server to start.

        Args:
            timeout: The maximum time to wait in seconds

        Returns:
            bool: True if the server is running, False otherwise
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                status = self.get_status()
                if status.get("status") == "running":
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.5)
        return False

    def test_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Test an endpoint.

        Args:
            endpoint: The endpoint to test
            method: The HTTP method to use
            data: The data to send
            headers: The headers to send

        Returns:
            Dict[str, Any]: The response from the server
        """
        try:
            url = f"{self.base_url}{endpoint}"
            method = method.upper()
            
            if method == "GET":
                response = requests.get(url, params=data, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, json=data, headers=headers)
            else:
                return {"status": "error", "message": f"Unsupported method: {method}"}
            
            return {
                "status": "success",
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text,
                "json": response.json() if response.headers.get("content-type") == "application/json" else None,
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to test endpoint: {e}")
            return {"status": "error", "message": str(e)}
