# Quick Start Guide for New Developers

This guide provides step-by-step instructions to get you up and running with the FOGIS API Client project as quickly as possible.

## Prerequisites

- Python 3.8 or higher
- Git
- Docker (optional, for Docker-based development)

## Step 1: Clone the Repository

```bash
git clone https://github.com/timmybird/fogis_api_client_python.git
cd fogis_api_client_python
```

## Step 2: Set Up Development Environment

### Option 1: Using the Setup Script (Recommended)

On macOS/Linux:
```bash
./scripts/setup_dev_env.sh
```

On Windows (PowerShell):
```powershell
.\scripts\setup_dev_env.ps1
```

This script will:
1. Create a virtual environment (if it doesn't exist)
2. Install the package in development mode with all dev dependencies
3. Install pre-commit and set up the hooks

### Option 2: Manual Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install the package in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Step 3: Run Tests

### Unit Tests

```bash
python -m unittest discover tests
```

### Integration Tests

```bash
./scripts/run_integration_tests.sh
```

## Step 4: Start Development

### Option 1: Local Development

1. Activate the virtual environment:
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Make your changes to the code

3. Run tests to verify your changes:
   ```bash
   python -m unittest discover tests
   ./scripts/run_integration_tests.sh
   ```

### Option 2: Docker-based Development

1. Start the development environment:
   ```bash
   ./dev.sh
   ```

2. Make your changes to the code

3. Run tests inside the Docker container:
   ```bash
   docker exec -it fogis-api-client-dev python -m unittest discover tests
   ```

## Step 5: Create a Branch for Your Changes

```bash
git checkout -b feature/your-feature-name
```

## Step 6: Commit Your Changes

```bash
git add .
git commit -m "Add your feature"
```

## Step 7: Run Pre-Merge Checks

```bash
./pre-merge-check.sh
```

## Step 8: Push Your Changes

```bash
git push -u origin feature/your-feature-name
```

## Step 9: Create a Pull Request

1. Go to the [GitHub repository](https://github.com/timmybird/fogis_api_client_python)
2. Click on "Pull requests" > "New pull request"
3. Select your branch and create the pull request
4. Fill in the PR template with details about your changes

## Additional Resources

- [Full Documentation](docs/README.md)
- [API Reference](docs/api_reference.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Getting Started Guide](docs/getting_started.md)
