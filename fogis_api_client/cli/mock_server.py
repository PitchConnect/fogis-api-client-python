#!/usr/bin/env python3
"""
CLI tool for running the mock FOGIS API server.

This module provides a command-line interface for starting and managing
the mock FOGIS API server for development and testing.

Usage:
    python -m fogis_api_client.cli.mock_server [--host HOST] [--port PORT]
"""

import argparse
import logging
import os
import sys
from typing import Optional

# Add the project root to the Python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the mock server
from integration_tests.mock_fogis_server import MockFogisServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the mock FOGIS API server")
    parser.add_argument(
        "--host", default="localhost", help="Host to bind the server to (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=5001, help="Port to run the server on (default: 5001)"
    )
    return parser.parse_args()


def run_server(host: Optional[str] = None, port: Optional[int] = None):
    """
    Run the mock FOGIS API server.

    Args:
        host: Host to bind the server to (default: localhost)
        port: Port to run the server on (default: 5001)
    """
    # Use command line arguments if provided, otherwise use defaults
    args = parse_args()
    host = host or args.host
    port = port or args.port

    logger.info(f"Starting mock FOGIS server on {host}:{port}")
    
    # Create and run the server
    server = MockFogisServer(host=host, port=port)
    server.run()


def main():
    """Run the mock server from the command line."""
    run_server()


if __name__ == "__main__":
    main()
