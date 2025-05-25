"""
Status command for the mock server CLI.

This module provides the command to check the status of the mock server.
"""

import argparse
import json
import logging
from typing import Dict, Any

from fogis_api_client.cli.commands.base import Command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StatusCommand(Command):
    """
    Command to check the status of the mock server.
    """

    name = "status"
    help = "Check the status of the mock server"
    description = "Check if the mock FOGIS API server is running"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add command-specific arguments to the parser.

        Args:
            parser: The argument parser
        """
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

        status = self.client.get_status()

        if args.json:
            print(json.dumps(status, indent=2))
        else:
            if status.get("status") == "running":
                print(f"Mock FOGIS server is running on {status.get('host')}:{status.get('port')}")
                print(f"Validation: {'enabled' if status.get('validation_enabled') else 'disabled'}")
                print(f"Request count: {status.get('request_count', 0)}")
            elif status.get("status") == "error":
                print(f"Error: {status.get('message')}")
                return 1
            else:
                print("Mock FOGIS server is not running")
                return 1

        return 0
