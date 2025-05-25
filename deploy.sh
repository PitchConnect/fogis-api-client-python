#!/bin/bash

# FOGIS Services Deployment Script
# This script deploys all 5 containerized services with orchestration

set -e

echo "🚀 Starting FOGIS Services Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_success "Docker is running"

# Check if all required images exist
print_status "Checking Docker images..."
REQUIRED_IMAGES=(
    "match-list-change-detector:latest"
    "match-list-processor:latest"
    "fogis-calendar-phonebook-sync:latest"
    "team-logo-combiner:latest"
    "google-drive-service:latest"
)

for image in "${REQUIRED_IMAGES[@]}"; do
    if docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "$image"; then
        print_success "✓ $image found"
    else
        print_error "✗ $image not found. Please build the image first."
        exit 1
    fi
done

# Create necessary directories
print_status "Creating directory structure..."
mkdir -p data/{match-list-change-detector,match-list-processor,fogis-calendar-phonebook-sync,team-logo-combiner,google-drive-service}
mkdir -p logs/{match-list-change-detector,match-list-processor,fogis-calendar-phonebook-sync,team-logo-combiner,google-drive-service}
mkdir -p credentials

print_success "Directory structure created"

# Check for Google credentials
if [ ! -f "credentials/google-credentials.json" ]; then
    print_warning "Google credentials file not found at credentials/google-credentials.json"
    print_warning "Please add your Google service account credentials before starting services that require Google API access"
fi

# Stop any existing containers
print_status "Stopping existing containers..."
docker-compose -f docker-compose-master.yml down --remove-orphans 2>/dev/null || true

# Start the services
print_status "Starting FOGIS services..."
docker-compose -f docker-compose-master.yml up -d

# Wait for services to start
print_status "Waiting for services to start..."
sleep 10

# Check service health
print_status "Checking service health..."

SERVICES=(
    "match-list-change-detector:9080"
    "match-list-processor:9082"
    "fogis-calendar-phonebook-sync:9083"
    "team-logo-combiner:9084"
    "google-drive-service:9085"
)

for service in "${SERVICES[@]}"; do
    service_name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)

    if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
        print_success "✓ $service_name is healthy"
    else
        print_warning "⚠ $service_name health check failed (this may be normal during startup)"
    fi
done

print_success "🎉 Deployment completed!"

echo ""
echo "📊 Service Status:"
echo "===================="
docker-compose -f docker-compose-master.yml ps

echo ""
echo "🔗 Service URLs:"
echo "================"
echo "• Match List Change Detector: http://localhost:9080"
echo "• Match List Processor: http://localhost:9082"
echo "• Calendar/Phonebook Sync: http://localhost:9083"
echo "• Team Logo Combiner: http://localhost:9084"
echo "• Google Drive Service: http://localhost:9085"
echo "• Prometheus Metrics: http://localhost:9081"

echo ""
echo "📝 Next Steps:"
echo "=============="
echo "1. Add Google service account credentials to credentials/google-credentials.json"
echo "2. Update USER_REFEREE_NUMBER in .env file with your actual referee number"
echo "3. Monitor logs: docker-compose -f docker-compose-master.yml logs -f"
echo "4. The match-list-change-detector will run automatically every hour"

echo ""
print_success "All services are now running! 🚀"
