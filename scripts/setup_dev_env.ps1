# Setup script for development environment (PowerShell)

Write-Host "Setting up development environment for fogis_api_client_python..."

# Check if Python is installed
try {
    python --version
} catch {
    Write-Host "Python is not installed or not in PATH. Please install Python and try again."
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
& .\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..."
pip install -e ".[dev]"

# Install pre-commit
Write-Host "Installing pre-commit..."
pip install pre-commit

# Install pre-commit hooks
Write-Host "Installing pre-commit hooks..."
pre-commit install

Write-Host "Development environment setup complete!"
Write-Host "To activate the virtual environment, run: .\.venv\Scripts\Activate.ps1"
