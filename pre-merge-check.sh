#!/bin/bash
set -e

echo "Running pre-merge checks..."

# Check if we're on a feature branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" == "main" ]]; then
    echo "Error: You should run this check from a feature branch, not main."
    exit 1
fi

# Fetch latest main
echo "Fetching latest main branch..."
git fetch origin main

# Run unit tests
echo "Running unit tests..."
python3 -m pytest tests/test_internal_api.py tests/test_adapters.py tests/test_api_compatibility.py -v

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "Docker is available. Running Docker build tests..."

    # Build the Docker image
    docker build -t fogis-api-client-test -f Dockerfile.test .

    echo "Docker tests completed."
else
    echo "Docker is not available. Skipping Docker build tests."
fi

echo "Pre-merge checks completed. You can now create a PR and merge your changes."
