"""
History command for the mock server CLI.

This module provides the command to view and manage the request history.
"""

import argparse
import json
import logging
import os
from typing import Dict, List, Any

from fogis_api_client.cli.commands.base import Command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoryCommand(Command):
    """
    Command to view and manage the request history.
    """

    name = "history"
    help = "View and manage the request history"
    description = "View, export, import, or clear the request history"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add command-specific arguments to the parser.

        Args:
            parser: The argument parser
        """
        subparsers = parser.add_subparsers(dest="history_command", help="History command")

        # View history
        view_parser = subparsers.add_parser("view", help="View the request history")
        view_parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Limit the number of requests to show (default: 10)",
        )
        view_parser.add_argument(
            "--json",
            action="store_true",
            help="Output in JSON format",
        )

        # Clear history
        clear_parser = subparsers.add_parser("clear", help="Clear the request history")

        # Export history
        export_parser = subparsers.add_parser("export", help="Export the request history to a file")
        export_parser.add_argument(
            "file",
            help="File to export the history to",
        )

        # Import history
        import_parser = subparsers.add_parser("import", help="Import the request history from a file")
        import_parser.add_argument(
            "file",
            help="File to import the history from",
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

        if args.history_command == "view":
            return self._view_history(args)
        elif args.history_command == "clear":
            return self._clear_history(args)
        elif args.history_command == "export":
            return self._export_history(args)
        elif args.history_command == "import":
            return self._import_history(args)
        else:
            logger.error("Unknown history command")
            return 1

    def _view_history(self, args: argparse.Namespace) -> int:
        """
        View the request history.

        Args:
            args: The parsed arguments

        Returns:
            int: The exit code (0 for success, non-zero for failure)
        """
        history = self.client.get_history()
        
        if not history:
            print("No requests in history")
            return 0

        # Limit the number of requests to show
        if args.limit > 0:
            history = history[-args.limit:]

        if args.json:
            print(json.dumps(history, indent=2))
        else:
            for i, request in enumerate(history):
                print(f"Request {i+1}:")
                print(f"  Timestamp: {request.get('timestamp')}")
                print(f"  Method: {request.get('method')}")
                print(f"  Endpoint: {request.get('endpoint')}")
                print(f"  Path: {request.get('path')}")
                print()

        return 0

    def _clear_history(self, args: argparse.Namespace) -> int:
        """
        Clear the request history.

        Args:
            args: The parsed arguments

        Returns:
            int: The exit code (0 for success, non-zero for failure)
        """
        response = self.client.clear_history()
        if response.get("status") == "success":
            print("Request history cleared")
            return 0
        else:
            logger.error(f"Failed to clear history: {response.get('message')}")
            return 1

    def _export_history(self, args: argparse.Namespace) -> int:
        """
        Export the request history to a file.

        Args:
            args: The parsed arguments

        Returns:
            int: The exit code (0 for success, non-zero for failure)
        """
        history = self.client.get_history()
        
        try:
            with open(args.file, "w") as f:
                json.dump(history, f, indent=2)
            print(f"Request history exported to {args.file}")
            return 0
        except Exception as e:
            logger.error(f"Failed to export history: {e}")
            return 1

    def _import_history(self, args: argparse.Namespace) -> int:
        """
        Import the request history from a file.

        Args:
            args: The parsed arguments

        Returns:
            int: The exit code (0 for success, non-zero for failure)
        """
        try:
            if not os.path.exists(args.file):
                logger.error(f"File not found: {args.file}")
                return 1
                
            with open(args.file, "r") as f:
                history = json.load(f)
                
            # TODO: Implement importing history to the server
            logger.error("Importing history is not yet implemented")
            return 1
        except Exception as e:
            logger.error(f"Failed to import history: {e}")
            return 1
