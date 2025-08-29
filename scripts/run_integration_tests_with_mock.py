#!/usr/bin/env python3
"""
Script to run integration tests with the mock FOGIS API server.

This script provides a convenient way to run integration tests with the mock server.
It automatically starts the mock server if it's not already running, runs the tests,
and provides a clean output.

Usage:
    python scripts/run_integration_tests_with_mock.py [options]

Options:
    --verbose, -v     Enable verbose output
    --test-file FILE  Run tests from a specific file
    --test-name TEST  Run a specific test
    --no-auto-start   Don't automatically start the mock server
    --help, -h        Show this help message
"""

import argparse
import logging
import os
import subprocess
import sys
from typing import List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the mock server manager
from integration_tests.pytest_plugin import MockServerManager  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run integration tests with the mock FOGIS API server")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--test-file", help="Run tests from a specific file")
    parser.add_argument("--test-name", help="Run a specific test")
    parser.add_argument("--no-auto-start", action="store_true", help="Don't automatically start the mock server")
    return parser.parse_args()


def build_pytest_command(args: argparse.Namespace) -> List[str]:
    """
    Build the pytest command based on the arguments.

    Args:
        args: The parsed arguments

    Returns:
        List[str]: The pytest command as a list of strings
    """
    # Use the current Python interpreter to avoid 'python' vs 'python3' inconsistencies
    command = [sys.executable, "-m", "pytest"]

    # Add verbosity
    if args.verbose:
        command.append("-v")

    # Add test file if specified
    if args.test_file:
        if os.path.exists(args.test_file):
            command.append(args.test_file)
        else:
            # Try to find the file in the integration_tests directory
            test_file = os.path.join("integration_tests", args.test_file)
            if os.path.exists(test_file):
                command.append(test_file)
            else:
                logger.error(f"Test file not found: {args.test_file}")
                sys.exit(1)
    else:
        # Run all integration tests by default, excluding external API endpoint tests
        command.append("integration_tests")
        command.extend(["-k", "not api_endpoints"])

    # Add test name if specified
    if args.test_name:
        command.append(f"-k {args.test_name}")

    return command


def start_mock_server() -> None:
    """
    Start the mock server if it's not already running.
    """
    logger.info("Starting mock server...")
    manager = MockServerManager.get_instance()
    manager.start_server()


def run_tests(command: List[str]) -> int:
    """
    Run the tests with the given command.

    Args:
        command: The pytest command as a list of strings

    Returns:
        int: The exit code from pytest
    """
    logger.info(f"Running tests with command: {' '.join(command)}")
    return subprocess.call(command)


def main() -> int:
    """
    Run the script.

    Returns:
        int: The exit code (0 for success, non-zero for failure)
    """
    # Parse arguments
    args = parse_args()

    # Start the mock server if needed
    if not args.no_auto_start:
        start_mock_server()

    # Build the pytest command
    command = build_pytest_command(args)

    # Run the tests
    return run_tests(command)


if __name__ == "__main__":
    sys.exit(main())
