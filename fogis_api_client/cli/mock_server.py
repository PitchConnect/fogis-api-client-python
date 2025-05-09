#!/usr/bin/env python3
"""
CLI tool for running the mock FOGIS API server.

This module provides a command-line interface for starting and managing
the mock FOGIS API server for development and testing.

Usage:
    python -m fogis_api_client.cli.mock_server [command] [options]

Commands:
    start       Start the mock server
    stop        Stop the mock server
    status      Check the status of the mock server
    history     View and manage the request history
    validation  Manage request validation
    test        Test an endpoint
"""

import argparse
import importlib
import inspect
import logging
import os
import sys
from typing import Dict, List, Type, Optional

# Add the project root to the Python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the API client
from fogis_api_client.cli.api_client import MockServerApiClient
from fogis_api_client.cli.commands.base import Command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def discover_commands() -> Dict[str, Type[Command]]:
    """
    Discover available commands.

    Returns:
        Dict[str, Type[Command]]: A dictionary of command names to command classes
    """
    commands = {}

    # Import command modules
    command_modules = [
        "fogis_api_client.cli.commands.start",
        "fogis_api_client.cli.commands.stop",
        "fogis_api_client.cli.commands.status",
        "fogis_api_client.cli.commands.history",
        "fogis_api_client.cli.commands.validation",
        "fogis_api_client.cli.commands.test",
    ]

    for module_name in command_modules:
        try:
            module = importlib.import_module(module_name)

            # Find command classes in the module
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and issubclass(obj, Command) and obj != Command):
                    commands[obj.name] = obj
        except ImportError as e:
            logger.warning(f"Failed to import command module {module_name}: {e}")

    return commands


def parse_args(commands: Dict[str, Type[Command]]):
    """
    Parse command line arguments.

    Args:
        commands: A dictionary of command names to command classes

    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(description="Mock FOGIS API server CLI")

    # Global options
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host where the mock server is running (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5001,
        help="Port where the mock server is running (default: 5001)",
    )

    # Add subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Add each command's subparser
    for name, command_class in commands.items():
        command_parser = subparsers.add_parser(
            name,
            help=command_class.help,
            description=command_class.description,
        )

        # Let the command add its arguments
        command = command_class()
        command.add_arguments(command_parser)

    return parser.parse_args()


def main():
    """
    Run the CLI.

    Returns:
        int: The exit code (0 for success, non-zero for failure)
    """
    # Discover available commands
    commands = discover_commands()

    # Parse arguments
    args = parse_args(commands)

    # If no command is specified, show help
    if not args.command:
        print("Error: No command specified")
        print("Run 'python -m fogis_api_client.cli.mock_server --help' for usage")
        return 1

    # Create the API client
    client = MockServerApiClient(host=args.host, port=args.port)

    # Create and execute the command
    command = commands[args.command]()
    command.set_client(client)

    return command.execute(args)


def run_server(host: Optional[str] = None, port: Optional[int] = None):
    """
    Run the mock FOGIS API server.

    This function is provided for backward compatibility.

    Args:
        host: Host to bind the server to (default: localhost)
        port: Port to run the server on (default: 5001)
    """
    # Import the start command
    from fogis_api_client.cli.commands.start import StartCommand

    # Create and execute the command
    command = StartCommand()

    # Create a namespace with the arguments
    args = argparse.Namespace()
    args.host = host or "localhost"
    args.port = port or 5001
    args.threaded = False
    args.wait = False

    # Execute the command
    return command.execute(args)


if __name__ == "__main__":
    sys.exit(main())
