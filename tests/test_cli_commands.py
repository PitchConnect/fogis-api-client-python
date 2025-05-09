"""
Unit tests for the CLI commands.

This module contains unit tests for the CLI commands.
"""

import argparse
import unittest
from unittest.mock import MagicMock, patch

from fogis_api_client.cli.commands.base import Command
from fogis_api_client.cli.commands.start import StartCommand
from fogis_api_client.cli.commands.status import StatusCommand
from fogis_api_client.cli.commands.stop import StopCommand
from fogis_api_client.cli.commands.history import HistoryCommand
from fogis_api_client.cli.commands.validation import ValidationCommand
from fogis_api_client.cli.commands.test import TestCommand


class TestCliCommands(unittest.TestCase):
    """Test case for CLI commands."""

    def test_base_command(self):
        """Test the base command."""
        # The base command is abstract, so we need to create a concrete subclass
        class TestCommand(Command):
            name = "test"
            help = "Test command"
            description = "Test command description"

            def execute(self, args):
                return 0

        # Create a command instance
        command = TestCommand()

        # Test the name, help, and description
        self.assertEqual(command.name, "test")
        self.assertEqual(command.help, "Test command")
        self.assertEqual(command.description, "Test command description")

        # Test the set_client method
        client = MagicMock()
        command.set_client(client)
        self.assertEqual(command.client, client)

    def test_start_command(self):
        """Test the start command."""
        # Create a command instance
        command = StartCommand()

        # Test the name, help, and description
        self.assertEqual(command.name, "start")
        self.assertEqual(command.help, "Start the mock server")
        self.assertTrue(command.description)

        # Test the add_arguments method
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)
        args = parser.parse_args([])
        self.assertEqual(args.host, "localhost")
        self.assertEqual(args.port, 5001)
        self.assertFalse(args.threaded)
        self.assertFalse(args.wait)

    def test_status_command(self):
        """Test the status command."""
        # Create a command instance
        command = StatusCommand()

        # Test the name, help, and description
        self.assertEqual(command.name, "status")
        self.assertEqual(command.help, "Check the status of the mock server")
        self.assertTrue(command.description)

        # Test the add_arguments method
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)
        args = parser.parse_args([])
        self.assertFalse(args.json)

    def test_stop_command(self):
        """Test the stop command."""
        # Create a command instance
        command = StopCommand()

        # Test the name, help, and description
        self.assertEqual(command.name, "stop")
        self.assertEqual(command.help, "Stop the mock server")
        self.assertTrue(command.description)

    def test_history_command(self):
        """Test the history command."""
        # Create a command instance
        command = HistoryCommand()

        # Test the name, help, and description
        self.assertEqual(command.name, "history")
        self.assertEqual(command.help, "View and manage the request history")
        self.assertTrue(command.description)

        # Test the add_arguments method
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)
        
        # Test the view subcommand
        args = parser.parse_args(["view"])
        self.assertEqual(args.history_command, "view")
        self.assertEqual(args.limit, 10)
        self.assertFalse(args.json)
        
        # Test the clear subcommand
        args = parser.parse_args(["clear"])
        self.assertEqual(args.history_command, "clear")
        
        # Test the export subcommand
        args = parser.parse_args(["export", "history.json"])
        self.assertEqual(args.history_command, "export")
        self.assertEqual(args.file, "history.json")
        
        # Test the import subcommand
        args = parser.parse_args(["import", "history.json"])
        self.assertEqual(args.history_command, "import")
        self.assertEqual(args.file, "history.json")

    def test_validation_command(self):
        """Test the validation command."""
        # Create a command instance
        command = ValidationCommand()

        # Test the name, help, and description
        self.assertEqual(command.name, "validation")
        self.assertEqual(command.help, "Manage request validation")
        self.assertTrue(command.description)

        # Test the add_arguments method
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)
        
        # Test the status subcommand
        args = parser.parse_args(["status"])
        self.assertEqual(args.validation_command, "status")
        
        # Test the enable subcommand
        args = parser.parse_args(["enable"])
        self.assertEqual(args.validation_command, "enable")
        
        # Test the disable subcommand
        args = parser.parse_args(["disable"])
        self.assertEqual(args.validation_command, "disable")

    def test_test_command(self):
        """Test the test command."""
        # Create a command instance
        command = TestCommand()

        # Test the name, help, and description
        self.assertEqual(command.name, "test")
        self.assertEqual(command.help, "Test an endpoint")
        self.assertTrue(command.description)

        # Test the add_arguments method
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)
        args = parser.parse_args(["/mdk/Login.aspx"])
        self.assertEqual(args.endpoint, "/mdk/Login.aspx")
        self.assertEqual(args.method, "GET")
        self.assertIsNone(args.data)
        self.assertIsNone(args.headers)
        self.assertFalse(args.json)


if __name__ == "__main__":
    unittest.main()
