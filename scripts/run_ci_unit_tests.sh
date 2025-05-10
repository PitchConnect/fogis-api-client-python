#!/bin/bash
set -e

# This script is used to run unit tests in CI environments

echo "Running unit tests in CI environment..."

# Build the test image if it doesn't exist
if [[ "$(docker images -q fogis-api-client:test 2> /dev/null)" == "" ]]; then
  echo "Building test Docker image..."
  docker build -t fogis-api-client:test -f Dockerfile.test .
fi

# Run the unit tests
echo "Running unit tests..."
docker run --rm fogis-api-client:test pytest tests -v

echo "Unit tests completed successfully."
