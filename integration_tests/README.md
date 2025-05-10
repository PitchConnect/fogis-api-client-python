# Integration Tests with Mock FOGIS API Server

This directory contains integration tests for the FOGIS API client using a mock server. These tests verify that the client can interact correctly with the API without requiring real credentials or internet access.

## Table of Contents

- [Overview](#overview)
- [Testing Architecture](#testing-architecture)
- [Components](#components)
- [Supported API Endpoints](#supported-api-endpoints)
- [Running the Tests](#running-the-tests)
- [Request Validation](#request-validation)
- [Adding New Tests](#adding-new-tests)
- [Extending the Mock Server](#extending-the-mock-server)
- [Troubleshooting](#troubleshooting)
- [Future Work](#future-work)

## Overview

The integration tests use a Flask-based mock server that simulates the FOGIS API endpoints. The mock server provides responses that match the structure of the real API, allowing us to test the client's functionality without making actual API calls.

These tests are essential for verifying that:

1. The client sends correctly structured requests to the API
2. The client correctly handles API responses
3. The client's behavior matches the expected behavior in real-world scenarios
4. Changes to the client don't break compatibility with the API

## Testing Architecture

The integration testing architecture consists of the following components:

1. **Mock FOGIS Server**: A Flask-based server that simulates the behavior of the real FOGIS API.
2. **Request Validator**: A module that validates the structure of requests sent to the mock server.
3. **Integration Tests**: Pytest-based tests that exercise the client's functionality against the mock server.
4. **Sample Data Factory**: A module that generates sample data for use in tests.

Here's a diagram of how these components interact:

```
+----------------+       +----------------+       +----------------+
|                |       |                |       |                |
| Integration    | ----> | FOGIS API      | ----> | Mock FOGIS     |
| Tests          |       | Client         |       | Server         |
|                |       |                |       |                |
+----------------+       +----------------+       +-------+--------+
                                                         |
                                                         v
                                                  +----------------+
                                                  |                |
                                                  | Request        |
                                                  | Validator      |
                                                  |                |
                                                  +----------------+
```

## Components

- `mock_fogis_server.py`: Implementation of the mock FOGIS API server
- `request_validator.py`: Validates the structure of requests sent to the mock server
- `sample_data_factory.py`: Generates sample data for use in tests
- `conftest.py`: Pytest fixtures for setting up the mock server and test environment
- `pytest_plugin.py`: Pytest plugin for automatically managing the mock server lifecycle
- `test_with_mock_server.py`: General integration tests for the FOGIS API client
- `test_match_result_reporting.py`: Specific tests for match result reporting functionality

## Supported API Endpoints

The mock server currently supports the following API endpoints:

### Match Data Endpoints
- `/MatchWebMetoder.aspx/GetMatch`: Get match details
- `/MatchWebMetoder.aspx/GetMatchdeltagareLista`: Get match players list
- `/MatchWebMetoder.aspx/GetMatchfunktionarerLista`: Get match officials list
- `/MatchWebMetoder.aspx/GetMatchhandelselista`: Get match events list
- `/MatchWebMetoder.aspx/GetMatchresultat`: Get match result
- `/MatchWebMetoder.aspx/GetMatchresultatlista`: Get match result list
- `/MatchWebMetoder.aspx/GetMatcherAttRapportera`: Get matches to report

### Match Reporting Endpoints
- `/MatchWebMetoder.aspx/SparaMatchhandelse`: Save match event
- `/MatchWebMetoder.aspx/RaderaMatchhandelse`: Delete match event
- `/MatchWebMetoder.aspx/SparaMatchresultatLista`: Save match result list
- `/MatchWebMetoder.aspx/SparaMatchGodkannDomarrapport`: Mark match reporting as finished
- `/MatchWebMetoder.aspx/SparaMatchdeltagare`: Save match participant
- `/MatchWebMetoder.aspx/SparaMatchlagledare`: Save team official action

## Running the Tests

### Prerequisites

- Docker and Docker Compose installed
- Python 3.9 or higher
- Virtual environment with dependencies installed

### Running Tests with Docker

The recommended way to run the integration tests is using the provided script:

```bash
./run_integration_tests.sh
```

This script will:

1. Start the Docker Compose environment with the mock server and API client
2. Run the integration tests
3. Stop the Docker Compose environment

### Running Tests Locally

There are several ways to run the integration tests locally:

#### Using the Improved Integration Test Script (Recommended)

The easiest way is to use the new integration test script that automatically manages the mock server:

```bash
python scripts/run_integration_tests_with_mock.py
```

This script will:
1. Start the mock server if it's not already running
2. Run all integration tests
3. Provide a clean output

You can also run specific tests:

```bash
# Run a specific test file
python scripts/run_integration_tests_with_mock.py --test-file test_with_mock_server.py

# Run a specific test
python scripts/run_integration_tests_with_mock.py --test-name test_login

# Enable verbose output
python scripts/run_integration_tests_with_mock.py --verbose
```

#### Using the Pytest Plugin (Automatic Mock Server)

You can also use the new pytest plugin that automatically manages the mock server:

```bash
python -m pytest integration_tests/test_with_mock_server.py -v
python -m pytest integration_tests/test_match_result_reporting.py -v
```

This approach uses the `mock_server_auto` fixture in the pytest plugin to start the mock server in a separate thread during test execution.

#### Using the CLI Tool (Manual Mock Server)

Alternatively, you can start the mock server manually using the CLI tool:

```bash
# Start the mock server
python -m fogis_api_client.cli.mock_server start

# Run the tests
python -m pytest integration_tests/test_with_mock_server.py -v

# Stop the mock server
python -m fogis_api_client.cli.mock_server stop
```

This approach is useful for debugging, as you can inspect the server logs and request history.

#### Using IDE Integration

The project now includes configuration files for VSCode and PyCharm that make it easy to run integration tests from your IDE:

**VSCode**:
1. Open the project in VSCode
2. Go to the Run and Debug panel
3. Select "Python: Run Integration Tests" from the dropdown
4. Click the Run button

**PyCharm**:
1. Open the project in PyCharm
2. Go to the Run configurations dropdown
3. Select "Run Integration Tests"
4. Click the Run button

## Pytest Plugin

The project includes a pytest plugin (`pytest_plugin.py`) that makes it easy to use the mock server in tests. The plugin provides the following fixtures:

- `mock_server_auto`: Automatically starts and stops the mock server
- `mock_api_urls_auto`: Temporarily overrides API URLs to point to the mock server
- `clear_request_history_auto`: Clears the request history before and after each test
- `fogis_test_client_auto`: Provides a configured FogisApiClient for testing

To use these fixtures in your tests, simply include them as parameters:

```python
def test_some_functionality(mock_server_auto, mock_api_urls_auto, clear_request_history_auto):
    # Create a client
    client = FogisApiClient(
        username="test_user",
        password="test_password",
    )

    # Test the functionality
    result = client.some_method()

    # Verify the result
    assert result is not None
```

Or use the combined fixture for simplicity:

```python
def test_some_functionality(fogis_test_client_auto):
    # Test the functionality
    result = fogis_test_client_auto.some_method()

    # Verify the result
    assert result is not None
```

## Request Validation

The mock server validates requests to ensure they match the expected structure. This helps catch issues with the client's request formatting early.

Request validation is controlled by the `RequestValidator` class in `request_validator.py`. It defines schemas for each endpoint and validates requests against these schemas.

Example schema:

```python
SCHEMAS = {
    "/MatchWebMetoder.aspx/SparaMatchresultatLista": {
        "required_fields": ["matchresultatListaJSON"],
        "nested_fields": {
            "matchresultatListaJSON": [
                {
                    "required_fields": [
                        "matchid",
                        "matchresultattypid",
                        "matchlag1mal",
                        "matchlag2mal",
                        "wo",
                        "ow",
                        "ww",
                    ]
                }
            ]
        },
    }
}
```

## Adding New Tests

To add new tests, follow these steps:

1. **Identify the endpoint to test**: Determine which API endpoint you want to test.
2. **Check the mock server**: Ensure that the mock server implements the endpoint. If not, add it.
3. **Define the request schema**: Add a schema for the endpoint in the request validator.
4. **Create a test file**: Create a new test file or add tests to an existing file.
5. **Implement the tests**: Write tests that exercise the endpoint's functionality.

### Test Structure

Each test should use the `mock_api_urls` fixture to handle API URL overrides. This fixture temporarily overrides the API URLs to point to the mock server and restores them after the test completes. It also clears the request history at the beginning of each test for better isolation.

Example test structure:

```python
def test_some_functionality(self, mock_fogis_server, test_credentials, mock_api_urls):
    """Test some functionality."""
    # Create a client with test credentials
    client = FogisApiClient(
        username=test_credentials["username"],
        password=test_credentials["password"],
    )

    # Test the functionality
    result = client.some_method()

    # Verify the result
    assert result is not None
```

The `mock_api_urls` fixture handles:
1. Storing the original base URLs
2. Setting the base URLs to point to the mock server
3. Clearing the request history
4. Restoring the original base URLs after the test

## Extending the Mock Server

To add support for new API endpoints:

1. **Add a schema**: Define a schema for the endpoint in the `RequestValidator.SCHEMAS` dictionary.
2. **Add a route handler**: Add a new route handler in the `_register_routes` method of the `MockFogisServer` class.
3. **Create sample data**: Add sample data for the endpoint in the `MockDataFactory` class.
4. **Implement validation**: Add validation logic in the route handler using the `_validate_and_log_request` method.

Example:

```python
# In request_validator.py
SCHEMAS = {
    "/MatchWebMetoder.aspx/NewEndpoint": {
        "required_fields": ["field1", "field2"],
        "nested_fields": {
            "field1": {
                "required_fields": ["subfield1", "subfield2"]
            }
        }
    }
}

# In mock_fogis_server.py
@self.app.route("/mdk/MatchWebMetoder.aspx/NewEndpoint", methods=["POST"])
def new_endpoint():
    auth_result = self._check_auth()
    if auth_result is not True:
        return auth_result

    # Get data from request
    data = request.json or {}

    # Validate and log the request
    endpoint = "/MatchWebMetoder.aspx/NewEndpoint"
    is_valid, error_msg = self._validate_and_log_request(endpoint, data)
    if not is_valid:
        return jsonify({"d": json.dumps({"success": False, "error": error_msg})}), 400

    # Return sample data
    return jsonify({"d": json.dumps({"success": True, "data": self.data_factory.get_sample_data_for_endpoint()})})
```

## Troubleshooting

Common issues and their solutions:

- **Authentication failures**: Check that the mock server is correctly handling authentication
- **Schema validation errors**: Ensure your requests match the expected schema
- **Missing endpoints**: Add any missing endpoints to the mock server
- **Network issues**: Check that the client can connect to the mock server

## Notes

- The mock server runs in a separate process during tests
- The server is automatically started and stopped by the pytest fixtures
- The client's `BASE_URL` is temporarily overridden to point to the mock server
- Test credentials are provided by the `test_credentials` fixture
- Request validation can be disabled for debugging by setting `self.validate_requests = False` in the mock server

## Future Work

The current implementation focuses on match result reporting, but there are plans to expand the test coverage to include other endpoints. See the following issues for more details:

- [Issue #161](https://github.com/PitchConnect/fogis-api-client-python/issues/161): Expand integration test coverage to additional API endpoints
- [Issue #162](https://github.com/PitchConnect/fogis-api-client-python/issues/162): Improve integration testing documentation

Please refer to [CONTRIBUTING.md](https://github.com/PitchConnect/fogis-api-client-python/blob/develop/CONTRIBUTING.md) for development guidelines and contribution process.
