# Contributing to FOGIS API Client

Thank you for your interest in contributing! This guide provides everything you need to get started with development.

## Getting Started

This project can be developed either locally in a Python virtual environment or using the provided Docker container. For most contributors, the local setup is simpler.

### Prerequisites

*   Python 3.8+
*   Git
*   Docker (Optional, for container-based development)

### 1. Set Up Your Environment (Local Development)

This is the recommended approach for most contributors.

**A. Use the Setup Script (Recommended)**

The setup script automates the process of creating a virtual environment and installing dependencies.

*   **On macOS/Linux:**
    ```bash
    ./scripts/setup_dev_env.sh
    ```
*   **On Windows (PowerShell):**
    ```powershell
    ./scripts/setup_dev_env.ps1
    ```

After the script completes, activate the virtual environment:
*   **On macOS/Linux:** `source .venv/bin/activate`
*   **On Windows:** `.venv\Scripts\activate`

**B. Manual Setup**

If you prefer to set up the environment manually:

1.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    Install the package in editable mode with all development dependencies.
    ```bash
    pip install -e ".[dev]"
    ```

3.  **Install pre-commit hooks:**
    This will run automated checks before each commit.
    ```bash
    pre-commit install
    ```

### 2. Running Tests

With your environment set up and activated, you can run the tests to ensure everything is working correctly.

*   **Run Unit Tests:**
    These tests are fast and don't require any external services.
    ```bash
    pytest tests/
    ```

*   **Run Integration Tests:**
    These tests run against a mock version of the FOGIS API. The test runner script will manage the mock server for you.
    ```bash
    python scripts/run_integration_tests_with_mock.py
    ```

### 3. Making Changes

1.  **Create a new branch:**
    ```bash
    git checkout -b your-feature-or-bugfix-branch
    ```

2.  **Make your code changes.**

3.  **Run tests frequently** to check your work.

4.  **Commit your changes.** The pre-commit hooks will automatically run linters and formatters.
    ```bash
    git commit -m "feat: Add new feature"
    ```

5.  **Push your branch and open a pull request.**

## Development Workflow

### Pre-commit Hooks

We use pre-commit hooks to enforce code style and catch simple errors. They are installed in the setup step and will run automatically when you commit. If a hook fails, it may modify files. Simply `git add` the modified files and commit again.

### Testing Strategy

*   **Unit Tests (`tests/`):** These should test individual functions and classes in isolation. They should be small and fast.
*   **Integration Tests (`integration_tests/`):** These test the client's interaction with the FOGIS API. To make this reliable and fast, we use a mock server (`integration_tests/mock_fogis_server.py`) that simulates the real API.
*   The `run_integration_tests_with_mock.py` script is the recommended way to run integration tests, as it handles starting and stopping the mock server automatically.

### Adding a New API Endpoint

When adding support for a new API endpoint, you will typically need to:

1.  Add a new method to the `FogisApiClient` in `fogis_api_client/fogis_api_client.py`. This method will contain the logic for calling the endpoint and processing the response.
2.  Add a corresponding method to the mock server in `integration_tests/mock_fogis_server.py` to simulate the new endpoint.
3.  Add integration tests for the new endpoint in `integration_tests/`.

## Docker-based Development (Optional)

If you prefer to work in a containerized environment:

1.  **Start the development container:**
    ```bash
    ./dev.sh
    ```
    This will build the Docker image and start the service with your local code mounted for live reloading.

2.  **Run commands inside the container:**
    You can run tests or other commands inside the running container.
    ```bash
    docker exec -it fogis-api-client-dev pytest tests/
    ```
