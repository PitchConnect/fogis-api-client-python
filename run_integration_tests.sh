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

    # Get container IP address
    local container_ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $container_name 2>/dev/null || echo "unknown")
    echo "Container $container_name IP address: $container_ip"

    for ((i=1; i<=max_attempts; i++)); do
        # Check if container is running
        if ! docker ps | grep -q $container_name; then
            echo "$container_name is not running! Attempt $i/$max_attempts"
            docker ps -a | grep $container_name || true
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
            # Try localhost first
            echo "Trying to access $container_name via localhost:$port$endpoint"
            RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port$endpoint || echo "failed")

            if [ "$RESPONSE" = "200" ]; then
                echo "$container_name is responding with 200 OK via localhost."
                return 0
            else
                echo "$container_name returned status $RESPONSE via localhost. Attempt $i/$max_attempts"

                # Try container IP if available
                if [ "$container_ip" != "unknown" ]; then
                    echo "Trying to access $container_name via $container_ip:$port$endpoint"
                    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://$container_ip:$port$endpoint || echo "failed")

                    if [ "$RESPONSE" = "200" ]; then
                        echo "$container_name is responding with 200 OK via container IP."
                        return 0
                    else
                        echo "$container_name returned status $RESPONSE via container IP. Attempt $i/$max_attempts"
                    fi
                fi

                # Try container name
                echo "Trying to access $container_name via $container_name:$port$endpoint"
                RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://$container_name:$port$endpoint || echo "failed")

                if [ "$RESPONSE" = "200" ]; then
                    echo "$container_name is responding with 200 OK via container name."
                    return 0
                else
                    echo "$container_name returned status $RESPONSE via container name. Attempt $i/$max_attempts"
                fi
            fi
        else
            echo "$container_name health status: $HEALTH. Attempt $i/$max_attempts"
        fi

        sleep $delay
    done

    echo "$container_name is not healthy after $max_attempts attempts!"
    echo "Container logs:"
    docker logs $container_name --tail 20
    echo "\nContainer inspection:"
    docker inspect $container_name | grep -A 10 Health || true
    return 1
}

# We don't need to create the network anymore as it's defined in docker-compose.dev.yml
# and will be created automatically when docker-compose up is run

# Remove any existing containers to ensure a clean start
echo "Stopping any existing containers..."
docker compose -f docker-compose.dev.yml down -v 2>/dev/null || true

# Start the services
echo "Starting services..."

# Check DNS resolution
echo "\nChecking DNS resolution:"
ping -c 1 google.com || true
ping -c 1 github.com || true
ping -c 1 localhost || true

# Create the network if it doesn't exist
echo "\nCreating Docker network..."
docker network create fogis-network 2>/dev/null || true

# Determine which docker-compose file to use
if [ "$CI" = "true" ]; then
    # Use the CI-specific docker-compose file in CI environments
    COMPOSE_FILE="docker-compose.ci.yml"
    echo "Running in CI environment, using $COMPOSE_FILE"
else
    # Use the development docker-compose file in local environments
    COMPOSE_FILE="docker-compose.dev.yml"
    echo "Running in local environment, using $COMPOSE_FILE"
fi

# Start the services
echo "\nStarting services..."
docker compose -f $COMPOSE_FILE up -d fogis-api-client mock-fogis-server

# Check if services are running
echo "\nRunning containers:"
docker ps

# Check network connectivity
echo "\nChecking network connectivity:"
docker network inspect fogis-network

# Wait a bit for services to start
sleep 5

# Check if the API service is healthy
check_container_health "fogis-api-client-dev" 10 15 "/" 8080
API_HEALTHY=$?

# Check if the mock server is healthy
check_container_health "mock-fogis-server" 10 5 "/health" 5000
MOCK_HEALTHY=$?

# Show service status
echo "\nService status:"
docker compose -f $COMPOSE_FILE ps

# Run the integration tests
echo "\nRunning integration tests..."
docker compose -f $COMPOSE_FILE run --rm integration-tests
TEST_EXIT_CODE=$?

echo "Integration tests completed with exit code: $TEST_EXIT_CODE"

# If tests failed, run the health check script
if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo "\nRunning Docker health check script..."
    if [ -f "scripts/check_docker_health.py" ]; then
        python3 scripts/check_docker_health.py
    else
        echo "Health check script not found. Skipping."
    fi
fi

# Return the test exit code
exit $TEST_EXIT_CODE
