"""
Base command for the mock server CLI.

This module provides the base command class for the mock server CLI.
"""

import abc
import argparse
from typing import Any, Dict, List, Optional

from fogis_api_client.cli.api_client import MockServerApiClient


class Command(abc.ABC):
    """
    Base class for CLI commands.
    """

    name: str = ""
    help: str = ""
    description: str = ""

    def __init__(self):
        """Initialize the command."""
        self.client: Optional[MockServerApiClient] = None

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add command-specific arguments to the parser.

        Args:
            parser: The argument parser
        """
        pass

    @abc.abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the command.

        Args:
            args: The parsed arguments

        Returns:
            int: The exit code (0 for success, non-zero for failure)
        """
        pass

    def set_client(self, client: MockServerApiClient) -> None:
        """
        Set the API client.

        Args:
            client: The API client
        """
        self.client = client
