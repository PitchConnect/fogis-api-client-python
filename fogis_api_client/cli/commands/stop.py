"""
Stop command for the mock server CLI.

This module provides the command to stop the mock server.
"""

import argparse
import logging

from fogis_api_client.cli.commands.base import Command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StopCommand(Command):
    """
    Command to stop the mock server.
    """

    name = "stop"
    help = "Stop the mock server"
    description = "Stop the running mock FOGIS API server"

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

        # Check if the server is running
        status = self.client.get_status()
        if status.get("status") != "running":
            logger.error("Mock FOGIS server is not running")
            return 1

        # Shutdown the server
        response = self.client.shutdown_server()
        if response.get("status") == "success":
            logger.info("Mock FOGIS server stopped")
            return 0
        else:
            logger.error(f"Failed to stop server: {response.get('message')}")
            return 1
