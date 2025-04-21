#!/bin/bash
# Script to verify Docker builds locally before pushing

set -e

echo "Verifying Docker builds locally..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Run dependency check first
echo "Running dependency check..."
./scripts/check_dependencies.py

# Build the development Docker image
echo "Building development Docker image..."
docker build -t fogis-api-client:dev -f Dockerfile.dev .

# Build the test Docker image
echo "Building test Docker image..."
docker build -t fogis-api-client:test -f Dockerfile.test .

# Build the production Docker image
echo "Building production Docker image..."
docker build -t fogis-api-client:prod -f Dockerfile .

echo "All Docker builds completed successfully!"
exit 0
