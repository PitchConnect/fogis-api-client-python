# FOGIS API Client

[![PyPI version](https://badge.fury.io/py/fogis-api-client-timmyBird.svg)](https://badge.fury.io/py/fogis-api-client-timmyBird)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python client for interacting with the FOGIS API (Svenska Fotbollförbundet).

This is a test change for workflow automation testing after permission fixes.

## Features

* **Authentication Options**: Login with credentials or session cookies
* **Lazy Authentication**: Automatically authenticates when needed
* **Match Management**: Fetch match lists, details, and results
* **Event Reporting**: Report goals, cards, substitutions, and other match events
* **Team Information**: Access team players, officials, and match assignments
* **Type Safety**: Comprehensive type annotations for better IDE support
* **Error Handling**: Detailed error messages and exception handling
* **Logging**: Built-in logging for debugging and monitoring
* **Docker Support**: Easy deployment and development with Docker
* **Utility Tools**: Testing utilities and development tools
* **Clean Architecture**: Separation of public and internal APIs for better maintainability

## Architecture

The FOGIS API Client is designed with a clean architecture that separates the public API from the internal implementation details. This separation allows for better maintainability and makes it easier to adapt to changes in the FOGIS API without breaking the public interface.

### Public API

The public API is what users of the library interact with. It provides a simple, intuitive interface for common operations like fetching match lists, reporting events, and managing match results. The public API is designed to be stable and backward-compatible.

Key components:
- `FogisApiClient` class in `public_api_client.py` - The main entry point for users
- Public type definitions in `types.py` - User-friendly data structures
- Exception classes for clear error handling

### Internal API

The internal API handles the low-level communication with the FOGIS API server. It's responsible for:

1. Converting between public and internal data formats
2. Handling authentication and session management
3. Implementing the low-level API contracts
4. Validating request and response data

Key components:
- `InternalApiClient` class in `internal/api_client.py` - Handles server communication
- Adapter functions in `internal/adapters.py` - Convert between data formats
- API contracts in `internal/api_contracts.py` - Define and validate data structures
- Internal type definitions in `internal/types.py` - Match server requirements

### Adapter Pattern

The adapter pattern is used to convert between the user-friendly public API formats and the server-specific internal API formats. This allows us to:

1. Present a clean, consistent interface to users
2. Handle complex server requirements internally
3. Adapt to server changes without breaking the public API
4. Apply default values and transformations automatically

For detailed information about the API architecture, including diagrams, examples, and best practices, see the [API Architecture Documentation](docs/api_architecture.md).

## Installation

### Using pip

```bash
pip install fogis-api-client-timmyBird
```

### From Source

```bash
git clone https://github.com/timmybird/fogis_api_client_python.git
cd fogis_api_client_python
pip install -e .
```

### Using Docker

```bash
# Pull the Docker image
docker pull timmybird/fogis_api_client_python:latest

# Run a script using the Docker image
docker run --rm -v $(pwd):/app \
  -e FOGIS_USERNAME="your_username" \
  -e FOGIS_PASSWORD="your_password" \
  timmybird/fogis_api_client_python:latest \
  python /app/your_script.py
```

### Development with Docker

For development purposes, you can use the provided development script:

```bash
# Start the development environment
./dev.sh
```

This script will:
1. Create necessary directories (data, logs, test-results)
2. Create a default .env.dev file if it doesn't exist
3. Start the Docker development environment using docker-compose.dev.yml
4. Show logs from the containers

See the [Docker Usage](docs/getting_started.md#docker-usage) and [Development with Docker](docs/getting_started.md#development-with-docker) sections in the documentation for more details.

## Quick Start

For new developers, see the [QUICKSTART.md](QUICKSTART.md) guide for step-by-step instructions to get up and running quickly.

```python
from fogis_api_client import FogisApiClient, FogisLoginError, FogisAPIRequestError, configure_logging

# Configure logging with enhanced options
configure_logging(level="INFO")

# Initialize with credentials
client = FogisApiClient(username="your_username", password="your_password")

# Fetch matches (lazy login happens automatically)
try:
    matches = client.fetch_matches_list_json()
    print(f"Found {len(matches)} matches")

    # Display the next 3 matches
    for match in matches[:3]:
        print(f"{match['datum']} {match['tid']}: {match['hemmalag']} vs {match['bortalag']} at {match['arena']}")

except FogisLoginError as e:
    print(f"Authentication error: {e}")
except FogisAPIRequestError as e:
    print(f"API request error: {e}")
```

## Documentation

Comprehensive documentation is available in the [docs](docs/) directory:

* [Getting Started Guide](docs/getting_started.md)
* [API Reference](docs/api_reference.md)
* [User Guides](docs/user_guides/)
* [Architecture Overview](docs/architecture.md)
* [Troubleshooting](docs/troubleshooting.md)

## Integration Testing

This project includes comprehensive integration tests to verify that the client correctly interacts with the FOGIS API. These tests use a mock server to simulate the FOGIS API, allowing for reliable testing without requiring real credentials or internet access.

### Benefits of Integration Tests

- **Verify API Contracts**: Ensure the client adheres to the expected API contracts
- **Catch Regressions**: Detect breaking changes before they affect users
- **Test Edge Cases**: Validate behavior with various input combinations
- **No Real Credentials**: Test without needing actual FOGIS credentials
- **Fast and Reliable**: Tests run quickly and consistently in any environment

### Mock Server

The mock server simulates the FOGIS API for testing and development. You can use it in two ways:

#### Using the CLI Tool

```bash
# Install the mock server dependencies
pip install -e ".[mock-server]"

# Start the mock server
python -m fogis_api_client.cli.mock_server

# With custom host and port
python -m fogis_api_client.cli.mock_server --host 0.0.0.0 --port 5001
```

#### Using the Standalone Script

```bash
# Start the mock server
python scripts/run_mock_server.py
```

The mock server provides a simulated FOGIS API environment that you can use for:
- Running integration tests without Docker
- Developing and testing new features
- Debugging API interactions
- Testing client applications without real credentials

### Running Integration Tests

There are multiple ways to run integration tests:

#### Using Docker (Recommended for CI/CD)

```bash
./run_integration_tests.sh
```

This script will:
1. Start a Docker environment with the mock FOGIS server
2. Run all integration tests against the mock server
3. Report the results and clean up the environment

#### Using Local Mock Server (Recommended for Development)

```bash
# In terminal 1: Start the mock server
python -m fogis_api_client.cli.mock_server start

# In terminal 2: Run the tests
python -m pytest integration_tests
```

The mock server CLI provides many useful commands for development and testing:

```bash
# Show help
python -m fogis_api_client.cli.mock_server --help

# Check the status of the mock server
python -m fogis_api_client.cli.mock_server status

# View request history
python -m fogis_api_client.cli.mock_server history view

# Test an endpoint
python -m fogis_api_client.cli.mock_server test /mdk/Login.aspx --method POST

# Stop the mock server
python -m fogis_api_client.cli.mock_server stop
```

See the [CLI README](fogis_api_client/cli/README.md) for more details on the available commands.

You can also run specific test files directly:

```bash
python -m pytest integration_tests/test_match_result_reporting.py -v
```

### Adding New Tests

When implementing new features, it's recommended to add corresponding integration tests. See the [integration tests README](integration_tests/README.md) for detailed instructions on adding new tests and extending the mock server.

#### Usage

```python
import logging
from fogis_api_client.fogis_api_client import FogisApiClient, FogisLoginError, FogisAPIRequestError

logging.basicConfig(level=logging.INFO)

username = "your_fogis_username"
password = "your_fogis_password"

try:
    client = FogisApiClient(username, password)
    # No need to call login() explicitly - the client implements lazy login
    matches = client.fetch_matches_list_json()
    if matches:
        print(f"Found {len(matches)} matches.")
    else:
        print("No matches found.")
except FogisLoginError as e:
    print(f"Login failed: {e}")
except FogisAPIRequestError as e:
    print(f"API request error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

You can also call `login()` explicitly if you want to pre-authenticate:

```python
client = FogisApiClient(username, password)
client.login()  # Explicitly authenticate
# ... make API requests
```

#### Cookie-Based Authentication

For improved security, you can authenticate using cookies instead of storing credentials:

```python
# First, get cookies from a logged-in session
client = FogisApiClient(username, password)
client.login()
cookies = client.get_cookies()  # Save these cookies securely

# Later, in another session, use the saved cookies
client = FogisApiClient(cookies=cookies)
# No need to call login() - already authenticated with cookies
matches = client.fetch_matches_list_json()
```

You can validate if the cookies are still valid:

```python
client = FogisApiClient(cookies=cookies)
if client.validate_cookies():
    print("Cookies are valid")
else:
    print("Cookies have expired, need to login with credentials again")
```

---
#### Docker Support

The package includes Docker support for easy deployment and development:

##### Production Deployment

1. Create a `.env` file with your credentials:
   ```
   FOGIS_USERNAME=your_fogis_username
   FOGIS_PASSWORD=your_fogis_password
   ```

2. Start the service:
   ```bash
   docker compose up -d
   ```

3. Access the API at http://localhost:8080

##### Development Environment

For development, we provide a more comprehensive setup:

1. Start the development environment:
   ```bash
   ./dev.sh
   ```

2. Run integration tests:
   ```bash
   ./run_integration_tests.sh
   ```

For more details on the development environment, see [README.dev.md](README.dev.md).

---
#### API Endpoints

The FOGIS API Gateway provides the following endpoints:

##### Basic Endpoints
- `GET /` - Returns a test JSON response
- `GET /hello` - Returns a simple hello world message

##### Match Endpoints
- `GET /matches` - Returns a list of matches
- `POST /matches/filter` - Returns a filtered list of matches based on provided criteria
- `GET /match/<match_id>` - Returns details for a specific match
- `GET /match/<match_id>/result` - Returns result information for a specific match
- `GET /match/<match_id>/officials` - Returns officials information for a specific match
- `POST /match/<match_id>/finish` - Marks a match report as completed/finished

##### Match Events Endpoints
- `GET /match/<match_id>/events` - Returns events for a specific match
- `POST /match/<match_id>/events` - Reports a new event for a match
- `POST /match/<match_id>/events/clear` - Clears all events for a match

##### Team Endpoints
- `GET /team/<team_id>/players` - Returns player information for a specific team
- `GET /team/<team_id>/officials` - Returns officials information for a specific team

#### Query Parameters

Many endpoints support query parameters for filtering, sorting, and pagination:

##### `/matches` Endpoint
- `from_date` - Start date for filtering matches (format: YYYY-MM-DD)
- `to_date` - End date for filtering matches (format: YYYY-MM-DD)
- `limit` - Maximum number of matches to return
- `offset` - Number of matches to skip (for pagination)
- `sort_by` - Field to sort by (options: datum, hemmalag, bortalag, tavling)
- `order` - Sort order, 'asc' or 'desc'

##### `/match/<match_id>` Endpoint
- `include_events` - Whether to include events in the response (default: true)
- `include_players` - Whether to include players in the response (default: false)
- `include_officials` - Whether to include officials in the response (default: false)

##### `/match/<match_id>/events` Endpoint
- `type` - Filter events by type (e.g., 'goal', 'card', 'substitution')
- `player` - Filter events by player name
- `team` - Filter events by team name
- `limit` - Maximum number of events to return
- `offset` - Number of events to skip (for pagination)
- `sort_by` - Field to sort by (options: time, type, player, team)
- `order` - Sort order, 'asc' or 'desc'

##### `/team/<team_id>/players` Endpoint
- `name` - Filter players by name
- `position` - Filter players by position
- `number` - Filter players by jersey number
- `limit` - Maximum number of players to return
- `offset` - Number of players to skip (for pagination)
- `sort_by` - Field to sort by (options: name, position, number)
- `order` - Sort order, 'asc' or 'desc'

##### `/team/<team_id>/officials` Endpoint
- `name` - Filter officials by name
- `role` - Filter officials by role
- `limit` - Maximum number of officials to return
- `offset` - Number of officials to skip (for pagination)
- `sort_by` - Field to sort by (options: name, role)
- `order` - Sort order, 'asc' or 'desc'

##### Filter Parameters for `/matches/filter` Endpoint
The `/matches/filter` endpoint accepts the following parameters in the request body (JSON):
- `from_date` - Start date for filtering matches (format: YYYY-MM-DD)
- `to_date` - End date for filtering matches (format: YYYY-MM-DD)
- `status` - Match status (e.g., "upcoming", "completed")
- `age_category` - Age category for filtering matches
- `gender` - Gender for filtering matches
- `football_type` - Type of football (e.g., "indoor", "outdoor")

---
#### Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Run the pre-merge check to ensure all tests pass:
   ```bash
   ./pre-merge-check.sh
   ```
5. Commit your changes: `git commit -m "Add your feature"`
6. Push to the branch: `git push origin feature/your-feature-name`
7. Create a pull request

#### Development Setup

We provide setup scripts to make it easy to set up your development environment, including pre-commit hooks.

To set up pre-commit hooks that match our CI/CD pipeline:

```bash
./update_precommit_hooks.sh
```

This script will install pre-commit, generate hooks that match our CI/CD configuration, and install them automatically.

##### Using the Setup Script

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

##### Manual Setup

If you prefer to set up manually:

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

##### Pre-Commit Hooks

We use pre-commit hooks to ensure code quality. The hooks will automatically run before each commit, checking for:
- Code formatting (Black, isort)
- Linting issues (flake8)
- Type checking (mypy)
- Unit test failures
- Whether hooks need updating to match CI/CD

For more details on keeping hooks in sync with CI/CD, see [CONTRIBUTING.md](CONTRIBUTING.md#keeping-hooks-in-sync-with-cicd).

You can also run the hooks manually on all files:
```bash
pre-commit run --all-files
```

##### Verifying Docker Builds Locally

Before pushing changes that might affect Docker builds, you can verify them locally:

```bash
# Run the Docker verification hook
pre-commit run docker-verify --hook-stage manual

# Or run the script directly
./scripts/verify_docker_build.sh
```

This will build all Docker images locally and ensure they work correctly, preventing CI/CD pipeline failures.

##### Running Integration Tests

To run integration tests locally before pushing changes:

```bash
# Run the integration tests script
./scripts/run_integration_tests.sh
```

This script will:
1. Set up a virtual environment if needed
2. Install dependencies
3. Run the integration tests with the mock server

Running integration tests locally helps catch issues before they reach the CI/CD pipeline.

##### Dynamic Pre-commit Hook Generator

This project uses a dynamic pre-commit hook generator powered by Google's Gemini LLM to maintain consistent code quality and documentation standards.

```bash
# Generate pre-commit hooks interactively
python3 scripts/dynamic_precommit_generator.py

# Generate pre-commit hooks non-interactively
python3 scripts/dynamic_precommit_generator.py --non-interactive --install
```

See [scripts/README_DYNAMIC_HOOKS.md](scripts/README_DYNAMIC_HOOKS.md) for detailed documentation.

##### Pre-Merge Check

Before merging any changes, always run the pre-merge check script to ensure all tests pass:

```bash
./pre-merge-check.sh
```

This script:
- Runs all unit tests
- Builds and tests the Docker image (if Docker is available)
- Ensures your changes won't break existing functionality

## Troubleshooting

If you encounter issues while using the FOGIS API Client, check the [Troubleshooting Guide](docs/troubleshooting.md) for solutions to common problems.

### Common Issues

1. **Authentication Failures**
   - Check your credentials
   - Verify your account is active
   - Ensure you have the necessary permissions

2. **API Request Errors**
   - Check your network connection
   - Verify the FOGIS API is accessible
   - Ensure your request parameters are valid

3. **Data Errors**
   - Verify that the requested resource exists
   - Check for API changes
   - Ensure your data is properly formatted

4. **Match Reporting Issues**
   - Ensure all required fields are included
   - Verify that the match is in a reportable state
   - Check that player and team IDs are correct

5. **Performance Issues**
   - Implement caching for frequently accessed data
   - Use more specific queries to reduce data size
   - Process large data sets in chunks

## Error Handling

The package includes custom exceptions for common API errors:

- **FogisLoginError**: Raised when login fails due to invalid credentials, missing credentials, or session expiration.

- **FogisAPIRequestError**: Raised for general API request errors such as network issues, server errors, or invalid parameters.

- **FogisDataError**: Raised when there's an issue with the data from FOGIS, such as invalid response format, missing fields, or parsing errors.

## Utility Tools

The repository includes several utility tools to help with development and usage:

### Testing Utilities

Tools for running tests locally:

```bash
# Run all tests with proper Docker setup
./tools/testing/run_local_tests.sh
```

See [tools/testing/README.md](tools/testing/README.md) for more details.

## License

MIT License
