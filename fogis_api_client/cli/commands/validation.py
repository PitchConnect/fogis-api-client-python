"""
Validation command for the mock server CLI.

This module provides the command to manage request validation.
"""

import argparse
import logging

from fogis_api_client.cli.commands.base import Command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationCommand(Command):
    """
    Command to manage request validation.
    """

    name = "validation"
    help = "Manage request validation"
    description = "Enable or disable request validation"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add command-specific arguments to the parser.

        Args:
            parser: The argument parser
        """
        subparsers = parser.add_subparsers(dest="validation_command", help="Validation command")

        # Get validation status
        status_parser = subparsers.add_parser("status", help="Get the validation status")

        # Enable validation
        enable_parser = subparsers.add_parser("enable", help="Enable request validation")

        # Disable validation
        disable_parser = subparsers.add_parser("disable", help="Disable request validation")

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

        if args.validation_command == "status":
            return self._get_validation_status(args)
        elif args.validation_command == "enable":
            return self._set_validation_status(args, True)
        elif args.validation_command == "disable":
            return self._set_validation_status(args, False)
        else:
            logger.error("Unknown validation command")
            return 1

    def _get_validation_status(self, args: argparse.Namespace) -> int:
        """
        Get the validation status.

        Args:
            args: The parsed arguments

        Returns:
            int: The exit code (0 for success, non-zero for failure)
        """
        enabled = self.client.get_validation_status()
        print(f"Request validation is {'enabled' if enabled else 'disabled'}")
        return 0

    def _set_validation_status(self, args: argparse.Namespace, enabled: bool) -> int:
        """
        Set the validation status.

        Args:
            args: The parsed arguments
            enabled: True to enable validation, False to disable it

        Returns:
            int: The exit code (0 for success, non-zero for failure)
        """
        response = self.client.set_validation_status(enabled)
        if response.get("status") == "success":
            print(f"Request validation {'enabled' if enabled else 'disabled'}")
            return 0
        else:
            logger.error(f"Failed to set validation status: {response.get('message')}")
            return 1
