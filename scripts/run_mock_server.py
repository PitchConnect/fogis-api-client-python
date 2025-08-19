#!/usr/bin/env python3
"""
Script to run the mock FOGIS API server locally.

This script provides a convenient way to start the mock server for local development
and testing without requiring Docker.

Usage:
    python scripts/run_mock_server.py [--host HOST] [--port PORT]

Options:
    --host HOST     Host to bind the server to (default: localhost)
    --port PORT     Port to run the server on (default: 5001)
"""

import argparse
import logging
import os
import sys

from integration_tests.mock_fogis_server import MockFogisServer

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the mock FOGIS API server")
    parser.add_argument("--host", default="localhost", help="Host to bind the server to (default: localhost)")
    parser.add_argument("--port", type=int, default=5001, help="Port to run the server on (default: 5001)")
    return parser.parse_args()


def main():
    """Run the mock server."""
    args = parse_args()
    logger.info(f"Starting mock FOGIS server on {args.host}:{args.port}")

    # Create and run the server
    server = MockFogisServer(host=args.host, port=args.port)
    server.run()


if __name__ == "__main__":
    main()
