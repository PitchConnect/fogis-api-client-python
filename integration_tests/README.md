# Integration Tests with Mock FOGIS API Server

This directory contains integration tests for the FOGIS API client using a mock server. These tests verify that the client can interact correctly with the API without requiring real credentials or internet access.

## Table of Contents

- [Overview](#overview)
- [Testing Architecture](#testing-architecture)
- [Components](#components)
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
- `test_with_mock_server.py`: General integration tests for the FOGIS API client
- `test_match_result_reporting.py`: Specific tests for match result reporting functionality

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

There are two ways to run the integration tests locally:

#### Using the Pytest Fixture (Automatic Mock Server)

The simplest way is to let the pytest fixture start the mock server automatically:

```bash
python -m pytest integration_tests/test_with_mock_server.py -v
python -m pytest integration_tests/test_match_result_reporting.py -v
```

This approach uses the `mock_fogis_server` fixture in `conftest.py` to start the mock server in a separate thread during test execution.

#### Using the Standalone Mock Server (Recommended for Development)

For development and debugging, it's often better to run the mock server separately:

1. Install the mock server dependencies:
   ```bash
   pip install -e ".[dev,mock-server]"
   ```

2. Start the mock server in a separate terminal:
   ```bash
   python scripts/run_mock_server.py
   ```

3. Run the integration tests:
   ```bash
   python -m pytest integration_tests
   ```

Running the mock server separately allows you to:
- Inspect the server logs in real-time
- Keep the server running between test runs
- Test individual API endpoints manually using tools like curl or Postman

## Request Validation

The request validator (`request_validator.py`) validates the structure of requests sent to the mock server. It ensures that requests contain all required fields and that the fields have the correct types and values.

### Validation Process

1. The mock server receives a request
2. The request is passed to the request validator
3. The validator checks the request against the expected schema
4. If the request is valid, the mock server processes it
5. If the request is invalid, the mock server returns an error response

### Schema Definition

The request validator uses a schema-based approach to validation. Schemas are defined for each endpoint and specify the required fields and their expected types and values.

Example schema for match result reporting:

```python
{
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
2. Overriding the base URLs to use the mock server
3. Clearing request history for better test isolation
4. Restoring the original URLs after the test completes, even if the test fails


Integration tests should follow this structure:

1. **Setup**: Configure the client to use the mock server
2. **Exercise**: Call the client's methods to interact with the API
3. **Verify**: Check that the client behaves as expected and sends correct requests
4. **Teardown**: Clean up any resources used by the test

### Example Test

```python
def test_report_match_result(self, mock_fogis_server: Dict[str, str], test_credentials: Dict[str, str]):
    """Test reporting match results."""
    # Setup: Configure the client to use the mock server
    FogisApiClient.BASE_URL = f"{mock_fogis_server['base_url']}/mdk"
    client = FogisApiClient(
        username=test_credentials["username"],
        password=test_credentials["password"],
    )

    # Exercise: Call the client's method to report a match result
    match_id = 12345
    result_data = cast(
        MatchResultDict,
        {
            "matchid": match_id,
            "hemmamal": 2,
            "bortamal": 1,
            "halvtidHemmamal": 1,
            "halvtidBortamal": 0,
        },
    )
    response = client.report_match_result(result_data)

    # Verify: Check that the response is as expected
    assert isinstance(response, dict)
    assert "success" in response
    assert response["success"] is True

    # Verify the request structure (optional)
    history_response = requests.get(f"{mock_fogis_server['base_url']}/request-history")
    history_data = history_response.json()
    match_result_requests = [req for req in history_data["history"]
                           if req["endpoint"] == "/MatchWebMetoder.aspx/SparaMatchresultatLista"]
    assert len(match_result_requests) > 0
```

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

If you encounter issues with the mock server or integration tests:

1. **Check the logs**: Look for error messages in the console output and server logs
2. **Verify server status**: Ensure the mock server is running on the expected port
3. **Check request validation**: Verify that your requests match the expected schema
4. **Inspect request history**: Use the `/request-history` endpoint to see what requests were sent
5. **Check route paths**: Ensure that the route paths in the mock server match those used by the client
6. **Verify sample data**: Make sure the sample data matches the structure expected by the client

### Common Issues

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
