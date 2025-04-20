#!/bin/bash
# Script to check dependencies in the CI/CD pipeline

set -e

echo "Running CI/CD dependency check..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Install required packages for checking
pip install marshmallow>=3.26.0 apispec>=6.0.0 flask>=2.0.0

# Run the dependency check script
python scripts/check_dependencies.py

# If we get here, the dependency check passed
echo "CI/CD dependency check passed!"
exit 0
