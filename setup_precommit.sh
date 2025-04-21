#!/bin/bash
# setup_precommit.sh - Script to set up pre-commit hooks and verify installation
set -e

echo "===== Setting up pre-commit hooks ====="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "Error: pip is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install development dependencies
echo "Installing development dependencies..."
pip install -e ".[dev]"

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Install additional dependencies required by hooks
echo "Installing additional dependencies for hooks..."
pip install types-requests pytest pytest-cov

# Verify installation by running hooks on all files
echo "Verifying installation by running hooks on a sample file..."
# Create a temporary file to test hooks
echo "def test_function():" > test_precommit.py
echo "    return True" >> test_precommit.py

# Run pre-commit on the test file
echo "Running pre-commit hooks..."
pre-commit run --files test_precommit.py || true

# Clean up test file
rm test_precommit.py

echo ""
echo "===== Pre-commit hooks setup complete ====="
echo ""
echo "Pre-commit hooks will now run automatically when you commit changes."
echo ""
echo "To run hooks manually on all files:"
echo "  pre-commit run --all-files"
echo ""
echo "To run a specific hook on all files:"
echo "  pre-commit run black --all-files"
echo ""
echo "Common issues and solutions:"
echo "  - If black or isort fail: They will automatically fix the issues, just add the changes and commit again"
echo "  - If flake8 fails: Fix the style issues manually according to the error messages"
echo "  - If mypy fails: Add proper type hints or use appropriate type ignores"
echo "  - If tests fail: Fix the failing tests before committing"
echo ""
echo "For more information, see the pre-commit configuration in .pre-commit-config.yaml"
