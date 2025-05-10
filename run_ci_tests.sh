#!/bin/bash

# This script is used to run integration tests in CI environments

# Create the Docker network
echo "Creating Docker network..."
docker network create fogis-network || true

# Run the integration tests
echo "Running integration tests..."

# Start the Docker Compose environment
docker compose -f docker-compose.ci.yml up -d

# Wait for the mock server to be ready
echo "Waiting for mock server to be ready..."
sleep 20

# Check if the mock server is running
docker ps

# Run the integration tests
docker compose -f docker-compose.ci.yml run --rm integration-tests

# Store the exit code
INTEGRATION_TEST_EXIT_CODE=$?

# Print the logs for debugging
docker compose -f docker-compose.ci.yml logs

# Stop the Docker Compose environment
docker compose -f docker-compose.ci.yml down

# Return the integration test exit code
exit $INTEGRATION_TEST_EXIT_CODE
