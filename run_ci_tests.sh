#!/bin/bash

# This script is used to run integration tests in CI environments

set -e

# Create the Docker network
echo "Creating Docker network..."
docker network create fogis-network 2>/dev/null || true

# Start the services
echo "Starting services..."
docker compose -f docker-compose.ci.yml up -d fogis-api-client mock-fogis-server

# Wait for services to start
echo "Waiting for services to start..."
sleep 15

# Show running containers
echo "Running containers:"
docker ps

# Run the integration tests
echo "Running integration tests..."
docker compose -f docker-compose.ci.yml run --rm integration-tests

# Store the exit code
TEST_EXIT_CODE=$?

# Show Docker logs if tests failed
if [ $TEST_EXIT_CODE -ne 0 ]; then
  echo "Integration tests failed with exit code $TEST_EXIT_CODE"
  echo "Mock server logs:"
  docker logs mock-fogis-server || true
  echo "API server logs:"
  docker logs fogis-api-client-dev || true
fi

# Return the original exit code
exit $TEST_EXIT_CODE
