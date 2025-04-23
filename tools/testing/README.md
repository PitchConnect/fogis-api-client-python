# Fogis API Testing Tools

This directory contains tools for testing the Fogis API client.

## Tools

### run_local_tests.sh

A script to run both unit tests and integration tests locally. It handles Docker setup for integration tests and manages dependencies.

```bash
./run_local_tests.sh
```

This script:
1. Checks if Docker is installed and running
2. Installs required dependencies
3. Runs unit tests
4. Sets up Docker containers for integration tests
5. Runs integration tests
6. Cleans up Docker resources

## Usage

Simply run the script from the repository root:

```bash
./tools/testing/run_local_tests.sh
```

The script will handle all the necessary setup and cleanup.
