#\!/bin/bash

# This script is used to run tests in CI environments
# It uses docker-compose.test.yml to orchestrate the mock server and test runner

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to cleanup on exit
cleanup() {
    local exit_code=$?
    print_info "Cleaning up Docker resources..."

    # Stop and remove containers
    $DOCKER_COMPOSE -f docker-compose.test.yml down -v 2>/dev/null || true

    # Show container logs if tests failed
    if [ $exit_code -ne 0 ]; then
        print_warning "Tests failed. Showing container logs:"
        echo ""
        print_info "=== Mock Server Logs ==="
        $DOCKER_COMPOSE -f docker-compose.test.yml logs mock-fogis-server 2>/dev/null || echo "No logs available"
        echo ""
        print_info "=== Test Runner Logs ==="
        $DOCKER_COMPOSE -f docker-compose.test.yml logs test-runner 2>/dev/null || echo "No logs available"
    fi

    print_info "Cleanup complete"
    exit $exit_code
}

# Set up trap to ensure cleanup runs on exit
trap cleanup EXIT INT TERM

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p test-results logs

# Parse command line arguments
TEST_FILES="${1:-}"
VERBOSE="${2:-}"

print_info "=========================================="
print_info "Running CI Tests with Containerized Mock Server"
print_info "=========================================="
echo ""

# Check if Docker is available
if \! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check for Docker Compose (V2 uses 'docker compose', V1 uses 'docker-compose')
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    print_success "Docker Compose V2 detected"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    print_success "Docker Compose V1 detected"
else
    print_error "Docker Compose is not installed or not available"
    exit 1
fi

print_success "Docker and Docker Compose are available"
echo ""

# Build the images
print_info "Building Docker images..."
$DOCKER_COMPOSE -f docker-compose.test.yml build --no-cache

if [ $? -ne 0 ]; then
    print_error "Failed to build Docker images"
    exit 1
fi

print_success "Docker images built successfully"
echo ""

# Start the mock server
print_info "Starting mock FOGIS server..."
$DOCKER_COMPOSE -f docker-compose.test.yml up -d mock-fogis-server

if [ $? -ne 0 ]; then
    print_error "Failed to start mock server"
    exit 1
fi

print_success "Mock server started"
echo ""

# Wait for mock server to be healthy
print_info "Waiting for mock server to be healthy..."
MAX_WAIT=60
WAIT_INTERVAL=2
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' mock-fogis-server-test 2>/dev/null || echo "unknown")

    if [ "$HEALTH_STATUS" = "healthy" ]; then
        print_success "Mock server is healthy"
        break
    fi

    echo -n "."
    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

echo ""

if [ "$HEALTH_STATUS" \!= "healthy" ]; then
    print_error "Mock server failed to become healthy within ${MAX_WAIT} seconds"
    print_info "Mock server status: $HEALTH_STATUS"
    print_info "Showing mock server logs:"
    $DOCKER_COMPOSE -f docker-compose.test.yml logs mock-fogis-server
    exit 1
fi

# Verify mock server is responding
print_info "Verifying mock server is responding..."
if $DOCKER_COMPOSE -f docker-compose.test.yml exec -T mock-fogis-server curl -f http://localhost:5001/health > /dev/null 2>&1; then
    print_success "Mock server is responding to health checks"
else
    print_warning "Mock server health check returned non-zero, but continuing..."
fi

echo ""

# Run unit tests first
print_info "=========================================="
print_info "Running Unit Tests"
print_info "=========================================="
echo ""

$DOCKER_COMPOSE -f docker-compose.test.yml run --rm test-runner pytest tests/ -v --tb=short

UNIT_TEST_EXIT_CODE=$?

if [ $UNIT_TEST_EXIT_CODE -eq 0 ]; then
    print_success "Unit tests passed"
else
    print_error "Unit tests failed with exit code: $UNIT_TEST_EXIT_CODE"
fi

echo ""

# Run integration tests
print_info "=========================================="
print_info "Running Integration Tests"
print_info "=========================================="
echo ""

# Build the test command
TEST_CMD="pytest integration_tests/ -v --tb=short --log-cli-level=INFO"

if [ -n "$TEST_FILES" ]; then
    print_info "Running specific test files: $TEST_FILES"
    TEST_CMD="pytest $TEST_FILES -v --tb=short --log-cli-level=INFO"
fi

if [ -n "$VERBOSE" ]; then
    TEST_CMD="$TEST_CMD -vv"
fi

# Run the integration tests
$DOCKER_COMPOSE -f docker-compose.test.yml run --rm test-runner $TEST_CMD

INTEGRATION_TEST_EXIT_CODE=$?

if [ $INTEGRATION_TEST_EXIT_CODE -eq 0 ]; then
    print_success "Integration tests passed"
else
    print_error "Integration tests failed with exit code: $INTEGRATION_TEST_EXIT_CODE"
fi

echo ""

# Summary
print_info "=========================================="
print_info "Test Summary"
print_info "=========================================="
echo ""

if [ $UNIT_TEST_EXIT_CODE -eq 0 ]; then
    print_success "Unit Tests: PASSED"
else
    print_error "Unit Tests: FAILED (exit code: $UNIT_TEST_EXIT_CODE)"
fi

if [ $INTEGRATION_TEST_EXIT_CODE -eq 0 ]; then
    print_success "Integration Tests: PASSED"
else
    print_error "Integration Tests: FAILED (exit code: $INTEGRATION_TEST_EXIT_CODE)"
fi

echo ""

# Exit with failure if any tests failed
if [ $UNIT_TEST_EXIT_CODE -ne 0 ] || [ $INTEGRATION_TEST_EXIT_CODE -ne 0 ]; then
    print_error "Some tests failed"
    exit 1
fi

print_success "All tests passed\!"
exit 0
