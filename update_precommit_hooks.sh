#!/bin/bash
# Script to update pre-commit hooks to match CI/CD configuration
set -e

echo "===== Updating pre-commit hooks to match CI/CD ====="

# Check if Python is installed
if command -v python3 &> /dev/null; then
    PY=python3
elif command -v python &> /dev/null; then
    PY=python
else
    echo "Error: Python (python3) is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "Error: pip/pip3 is required but not installed."
    exit 1
fi

# Install required dependencies
echo "Installing required dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install google-generativeai pyyaml python-dotenv --quiet
else
    pip install google-generativeai pyyaml python-dotenv --quiet
fi

# Check if GOOGLE_GEMINI_API_KEY is set
if [ -z "$GOOGLE_GEMINI_API_KEY" ]; then
    echo "Warning: GOOGLE_GEMINI_API_KEY environment variable is not set."
    echo "The script will use fallback implementations without AI assistance."
    echo "To enable AI-powered hook generation, set the API key with:"
    echo "export GOOGLE_GEMINI_API_KEY=your_api_key"
    echo ""
fi

# Run the dynamic pre-commit hook generator
echo "Running dynamic pre-commit hook generator..."
$PY scripts/dynamic_precommit_generator.py --install

echo ""
echo "===== Pre-commit hooks updated successfully ====="
echo ""
echo "Your pre-commit hooks now match the CI/CD configuration."
echo "This ensures that checks that pass locally will also pass in CI."
echo ""
echo "To run all hooks manually:"
echo "  pre-commit run --all-files"
echo ""
