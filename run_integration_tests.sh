#!/bin/bash

# Create necessary directories if they don't exist
mkdir -p test-results

# Function to check if a container is healthy
check_container_health() {
    local container_name=$1
    local max_attempts=$2
    local delay=$3
    local endpoint=$4
    local port=$5

    echo "Checking if $container_name is healthy..."

    for ((i=1; i<=max_attempts; i++)); do
        # Check if container is running
        if ! docker ps | grep -q $container_name; then
            echo "$container_name is not running! Attempt $i/$max_attempts"
            sleep $delay
            continue
        fi

        # Check container health status
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' $container_name 2>/dev/null || echo "unhealthy")

        if [ "$HEALTH" = "healthy" ]; then
            echo "$container_name is healthy!"
            return 0
        fi

        # Try to access the endpoint if provided
        if [ -n "$endpoint" ] && [ -n "$port" ]; then
            RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port$endpoint || echo "failed")

            if [ "$RESPONSE" = "200" ]; then
                echo "$container_name is responding with 200 OK."
                return 0
            else
                echo "$container_name returned status $RESPONSE. Attempt $i/$max_attempts"
            fi
        else
            echo "$container_name health status: $HEALTH. Attempt $i/$max_attempts"
        fi

        sleep $delay
    done

    echo "$container_name is not healthy after $max_attempts attempts!"
    docker logs $container_name --tail 20
    return 1
}

# Create the network if it doesn't exist
docker network create fogis-network 2>/dev/null || true

# Remove any existing containers to ensure a clean start
echo "Stopping any existing containers..."
docker compose -f docker-compose.dev.yml down -v 2>/dev/null || true

# Start the services
echo "Starting services..."
docker compose -f docker-compose.dev.yml up -d fogis-api-client mock-fogis-server

# Check if the API service is healthy
check_container_health "fogis-api-client-dev" 10 15 "/" 8080
API_HEALTHY=$?

# Check if the mock server is healthy
check_container_health "mock-fogis-server" 10 5 "/health" 5000
MOCK_HEALTHY=$?

# Show service status
echo "\nService status:"
docker compose -f docker-compose.dev.yml ps

# Run the integration tests
echo "\nRunning integration tests..."
docker compose -f docker-compose.dev.yml run --rm integration-tests
TEST_EXIT_CODE=$?

echo "Integration tests completed with exit code: $TEST_EXIT_CODE"

# Return the test exit code
exit $TEST_EXIT_CODE
