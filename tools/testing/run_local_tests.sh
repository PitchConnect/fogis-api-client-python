#!/bin/bash

# Function to check if Docker is installed and running
check_docker() {
  if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker to run integration tests."
    exit 1
  fi

  if ! docker info &> /dev/null; then
    echo "Docker daemon is not running. Please start Docker to run integration tests."
    exit 1
  fi

  echo "Docker is installed and running."
}

# Function to run unit tests
run_unit_tests() {
  echo "Running unit tests..."

  # Try to install the docker module for tests
  echo "Installing required dependencies..."
  pip3 install docker pytest pytest-cov --quiet || echo "Warning: Could not install all dependencies. Some tests might be skipped."

  # Run the tests with a pattern that excludes docker-related tests if the module isn't available
  if python3 -c "import docker" &> /dev/null; then
    echo "Docker module is available, running all tests."
    python3 -m unittest discover tests
  else
    echo "Docker module is not available, skipping docker-related tests."
    # Find all test files except test_docker_setup.py
    TEST_FILES=$(find tests -name "test_*.py" | grep -v "test_docker_setup.py")
    python3 -m unittest ${TEST_FILES}
  fi

  if [ $? -ne 0 ]; then
    echo "Unit tests failed."
    exit 1
  fi
  echo "Unit tests passed."
}

# Function to run integration tests using Docker
run_integration_tests() {
  echo "Running integration tests using Docker..."

  # Create the network if it doesn't exist
  docker network create fogis-network 2>/dev/null || true

  # Run the integration tests using the existing script
  ./run_integration_tests.sh

  # Store the exit code
  local exit_code=$?

  echo "Integration tests completed with exit code: $exit_code"
  return $exit_code
}

# Function to clean up Docker resources
cleanup() {
  echo "Cleaning up Docker resources..."
  docker compose -f docker-compose.dev.yml down -v
  echo "Cleanup completed."
}

# Main function
main() {
  echo "=== Starting test suite ==="

  # Check if Docker is available
  check_docker

  # Run unit tests
  run_unit_tests

  # Run integration tests
  run_integration_tests
  local integration_exit_code=$?

  # Clean up Docker resources
  cleanup

  echo "=== Test suite completed ==="

  # Return the integration tests exit code
  return $integration_exit_code
}

# Run the main function
main
exit $?
