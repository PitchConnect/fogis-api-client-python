"""
Test command for the mock server CLI.

This module provides the command to test endpoints.
"""

import argparse
import json
import logging
from typing import Dict, Any, Optional

from fogis_api_client.cli.commands.base import Command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestCommand(Command):
    """
    Command to test endpoints.
    """

    name = "test"
    help = "Test an endpoint"
    description = "Send a test request to an endpoint"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add command-specific arguments to the parser.

        Args:
            parser: The argument parser
        """
        parser.add_argument(
            "endpoint",
            help="The endpoint to test (e.g., /mdk/Login.aspx)",
        )
        parser.add_argument(
            "--method",
            default="GET",
            choices=["GET", "POST", "PUT", "DELETE"],
            help="The HTTP method to use (default: GET)",
        )
        parser.add_argument(
            "--data",
            help="The data to send (JSON string)",
        )
        parser.add_argument(
            "--headers",
            help="The headers to send (JSON string)",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output in JSON format",
        )

    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the command.

        Args:
            args: The parsed arguments

        Returns:
            int: The exit code (0 for success, non-zero for failure)
        """
        if not self.client:
            logger.error("API client not set")
            return 1

        endpoint = args.endpoint
        method = args.method
        
        # Parse data and headers
        data: Optional[Dict[str, Any]] = None
        headers: Optional[Dict[str, str]] = None
        
        if args.data:
            try:
                data = json.loads(args.data)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON data: {e}")
                return 1
                
        if args.headers:
            try:
                headers = json.loads(args.headers)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON headers: {e}")
                return 1

        # Send the request
        response = self.client.test_endpoint(endpoint, method, data, headers)
        
        if args.json:
            print(json.dumps(response, indent=2))
        else:
            if response.get("status") == "success":
                print(f"Request to {endpoint} successful")
                print(f"Status code: {response.get('status_code')}")
                print("Response:")
                if response.get("json"):
                    print(json.dumps(response.get("json"), indent=2))
                else:
                    print(response.get("content"))
            else:
                print(f"Request failed: {response.get('message')}")
                return 1

        return 0
