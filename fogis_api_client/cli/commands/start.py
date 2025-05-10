"""
Start command for the mock server CLI.

This module provides the command to start the mock server.
"""

import argparse
import logging
import time
from typing import Optional

from integration_tests.mock_fogis_server import MockFogisServer
from fogis_api_client.cli.commands.base import Command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StartCommand(Command):
    """
    Command to start the mock server.
    """

    name = "start"
    help = "Start the mock server"
    description = "Start the mock FOGIS API server for development and testing"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add command-specific arguments to the parser.

        Args:
            parser: The argument parser
        """
        parser.add_argument(
            "--host",
            default="localhost",
            help="Host to bind the server to (default: localhost)",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=5001,
            help="Port to run the server on (default: 5001)",
        )
        parser.add_argument(
            "--threaded",
            action="store_true",
            help="Run the server in a separate thread",
        )
        parser.add_argument(
            "--wait",
            action="store_true",
            help="Wait for the server to start before returning",
        )

    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the command.

        Args:
            args: The parsed arguments

        Returns:
            int: The exit code (0 for success, non-zero for failure)
        """
        host = args.host
        port = args.port
        threaded = args.threaded
        wait = args.wait

        logger.info(f"Starting mock FOGIS server on {host}:{port}")

        # Create and run the server
        server = MockFogisServer(host=host, port=port)
        
        if threaded:
            server.run(threaded=True)
            logger.info(f"Mock FOGIS server started in the background on {host}:{port}")
            
            if wait:
                # Wait for the server to start
                if self.client and self.client.wait_for_server():
                    logger.info("Server is running")
                else:
                    logger.error("Failed to start server")
                    return 1
        else:
            # Run the server in the foreground
            server.run(threaded=False)

        return 0
