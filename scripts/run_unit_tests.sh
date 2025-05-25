#!/bin/bash
set -e

echo "Running unit tests..."

# Run the unit tests
python -m pytest tests/test_internal_api.py tests/test_adapters.py tests/test_api_compatibility.py -v

echo "Unit tests completed successfully."
