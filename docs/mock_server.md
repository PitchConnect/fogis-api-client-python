# Mock Server Documentation

## Overview

The mock server is a Flask-based implementation that simulates the FOGIS API for development and testing purposes. It allows you to:

- Develop and test against the FOGIS API without requiring real credentials
- Run integration tests in CI/CD environments
- Test error scenarios and edge cases
- Develop offline without internet connectivity
- Validate request structures against expected schemas

## Quick Start

### Installation

The mock server is included as a development dependency. Install it with:

```bash
# Install the package with development dependencies
pip install -e ".[dev,mock-server]"
```

### Starting the Mock Server

There are several ways to start the mock server:

#### 1. Using the CLI Tool

```bash
# Start the mock server with default settings
python -m fogis_api_client.cli.mock_server start

# Check if the mock server is running
python -m fogis_api_client.cli.mock_server status

# Stop the mock server
python -m fogis_api_client.cli.mock_server stop
```

#### 2. Using the Standalone Script

```bash
# Start the mock server
python scripts/run_mock_server.py

# With custom host and port
python scripts/run_mock_server.py --host 0.0.0.0 --port 8080
```

#### 3. Using Docker

```bash
# Build the Docker image
docker build -t fogis-mock-server -f Dockerfile.mock .

# Run the container
docker run -p 5001:5001 fogis-mock-server
```

#### 4. Programmatically in Python

```python
from integration_tests.mock_fogis_server import MockFogisServer

# Create and start the server
server = MockFogisServer(host="localhost", port=5001)
server.run(threaded=True)  # Run in a background thread

# Do something with the server...

# Stop the server
server.stop()
```

## Mock Server Architecture

The mock server consists of several components:

1. **Flask Application**: The core server that handles HTTP requests and responses
2. **Request Validator**: Validates incoming requests against expected schemas
3. **Sample Data Factory**: Generates realistic test data for responses
4. **CLI Interface**: Provides a command-line interface for managing the server

### Directory Structure

```
fogis-api-client-python/
├── fogis_api_client/
│   └── cli/
│       ├── commands/         # CLI command implementations
│       │   ├── start.py      # Start command
│       │   ├── stop.py       # Stop command
│       │   └── ...           # Other commands
│       ├── api_client.py     # Client for interacting with the mock server API
│       └── mock_server.py    # CLI entry point
├── integration_tests/
│   ├── mock_fogis_server.py  # Core mock server implementation
│   ├── request_validator.py  # Request validation logic
│   ├── sample_data_factory.py # Test data generation
│   └── schemas/              # JSON schemas for request validation
└── scripts/
    └── run_mock_server.py    # Standalone script to run the server
```

## Supported Endpoints

The mock server implements the following FOGIS API endpoints:

### Authentication

- `/mdk/Login.aspx` - Login page and authentication

### Match Information

- `/mdk/MatchWebMetoder.aspx/HamtaMatchLista` - Fetch list of matches
- `/mdk/MatchWebMetoder.aspx/GetMatcherAttRapportera` - Fetch matches to report (new API)
- `/mdk/MatchWebMetoder.aspx/HamtaMatch` - Fetch match details
- `/mdk/MatchWebMetoder.aspx/GetMatch` - Fetch match details (new API)
- `/mdk/MatchWebMetoder.aspx/HamtaMatchSpelare` - Fetch match players
- `/mdk/MatchWebMetoder.aspx/GetMatchdeltagareLista` - Fetch match players (new API)
- `/mdk/MatchWebMetoder.aspx/HamtaMatchFunktionarer` - Fetch match officials
- `/mdk/MatchWebMetoder.aspx/GetMatchfunktionarerLista` - Fetch match officials (new API)
- `/mdk/MatchWebMetoder.aspx/HamtaMatchHandelser` - Fetch match events
- `/mdk/MatchWebMetoder.aspx/GetMatchhandelselista` - Fetch match events (new API)
- `/mdk/MatchWebMetoder.aspx/GetMatchresultatlista` - Fetch match results

### Team Information

- `/mdk/MatchWebMetoder.aspx/GetMatchdeltagareListaForMatchlag` - Fetch team players
- `/mdk/MatchWebMetoder.aspx/GetMatchlagledareListaForMatchlag` - Fetch team officials

### Reporting

- `/mdk/MatchWebMetoder.aspx/SparaMatchhandelse` - Report match event
- `/mdk/MatchWebMetoder.aspx/RensaMatchhandelser` - Clear match events
- `/mdk/Fogis/Match/ClearMatchEvents` - Clear match events (new API)
- `/mdk/Fogis/Match/SparaMatchGodkannDomarrapport` - Mark reporting as finished

## CLI Commands

The mock server CLI provides the following commands:

### start

Starts the mock server.

```bash
python -m fogis_api_client.cli.mock_server start [--host HOST] [--port PORT] [--threaded] [--wait]
```

Options:
- `--host HOST`: Host to bind the server to (default: localhost)
- `--port PORT`: Port to run the server on (default: 5001)
- `--threaded`: Run the server in a background thread
- `--wait`: Wait for the server to start before returning

### stop

Stops the mock server.

```bash
python -m fogis_api_client.cli.mock_server stop [--host HOST] [--port PORT]
```

### status

Checks the status of the mock server.

```bash
python -m fogis_api_client.cli.mock_server status [--host HOST] [--port PORT]
```

### history

Views and manages the request history.

```bash
python -m fogis_api_client.cli.mock_server history [--host HOST] [--port PORT] [--clear]
```

Options:
- `--clear`: Clear the request history

### validation

Manages request validation.

```bash
python -m fogis_api_client.cli.mock_server validation [--host HOST] [--port PORT] [--enable | --disable]
```

Options:
- `--enable`: Enable request validation
- `--disable`: Disable request validation

### test

Tests an endpoint.

```bash
python -m fogis_api_client.cli.mock_server test [--host HOST] [--port PORT] --endpoint ENDPOINT [--data DATA]
```

Options:
- `--endpoint ENDPOINT`: Endpoint to test (e.g., /mdk/MatchWebMetoder.aspx/HamtaMatchLista)
- `--data DATA`: JSON data to send with the request

## Extending the Mock Server

### Adding a New Endpoint

To add a new endpoint to the mock server, follow these steps:

1. **Identify the endpoint details**:
   - URL path (e.g., `/mdk/MatchWebMetoder.aspx/NewEndpoint`)
   - HTTP method (GET, POST, etc.)
   - Request parameters and structure
   - Response structure

2. **Add the endpoint to `mock_fogis_server.py`**:

```python
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

    # Generate response data using the factory
    response_data = MockDataFactory.generate_new_endpoint_data()

    # Return the response
    return jsonify({"d": json.dumps(response_data)})
```

3. **Add a data generator method to `sample_data_factory.py`**:

```python
@staticmethod
def generate_new_endpoint_data():
    """Generate sample data for the new endpoint."""
    return {
        "success": True,
        "data": {
            "field1": "value1",
            "field2": "value2",
            # Add more fields as needed
        }
    }
```

4. **Add a request schema in `integration_tests/schemas/`**:

Create a new JSON schema file (e.g., `new_endpoint_request.json`) that defines the expected structure of requests to this endpoint.

5. **Update the request validator to use the new schema**:

In `request_validator.py`, add the new endpoint to the `ENDPOINT_SCHEMAS` dictionary:

```python
ENDPOINT_SCHEMAS = {
    # Existing endpoints...
    "/MatchWebMetoder.aspx/NewEndpoint": "new_endpoint_request.json",
}
```

6. **Add integration tests for the new endpoint**:

Create a new test function in an appropriate test file:

```python
def test_new_endpoint(mock_api_urls):
    """Test the new endpoint."""
    # Create a client
    client = FogisApiClient(username="test_user", password="test_password")

    # Call the endpoint
    result = client.new_endpoint_method()

    # Assert the result
    assert result["success"] is True
    assert "field1" in result["data"]
    assert "field2" in result["data"]
```

### Customizing Response Data

The `MockDataFactory` class in `sample_data_factory.py` is responsible for generating sample data for the mock server responses. You can customize the data by modifying the existing generator methods or adding new ones.

For example, to customize the match list data:

```python
@staticmethod
def generate_match_list():
    """Generate a sample match list."""
    return {
        "d": json.dumps({
            "matchlista": [
                {
                    "matchid": 12345,
                    "hemmalag": "Custom Team A",
                    "bortalag": "Custom Team B",
                    "datum": "2025-05-15",
                    "tid": "19:00",
                    "status": "Ej rapporterad",
                    # Add more fields as needed
                },
                # Add more matches as needed
            ]
        })
    }
```

## Troubleshooting

### Common Issues

#### Mock Server Won't Start

**Symptoms**: Error when trying to start the mock server.

**Possible causes and solutions**:
- **Port already in use**: Try a different port with `--port` option
- **Missing dependencies**: Ensure you've installed the package with `pip install -e ".[dev,mock-server]"`
- **Python path issues**: Make sure you're running the command from the project root

#### Authentication Failures

**Symptoms**: Tests fail with authentication errors.

**Possible causes and solutions**:
- **Invalid credentials**: The mock server accepts `test_user` / `test_password` by default
- **Cookie handling**: Ensure your client is properly handling the authentication cookies
- **Session management**: The mock server uses Flask sessions, which require a secret key

#### Request Validation Errors

**Symptoms**: Requests fail with validation errors.

**Possible causes and solutions**:
- **Invalid request structure**: Check that your request matches the expected schema
- **Missing fields**: Ensure all required fields are included in the request
- **Wrong data types**: Verify that field values have the correct data types
- **Disable validation**: For debugging, you can disable validation with `python -m fogis_api_client.cli.mock_server validation --disable`

#### Integration Tests Failing

**Symptoms**: Integration tests fail when run against the mock server.

**Possible causes and solutions**:
- **Server not running**: Ensure the mock server is running before running tests
- **Wrong URL**: Check that the tests are using the correct URL for the mock server
- **Request validation**: Verify that the requests match the expected schemas
- **Response handling**: Check that the client correctly handles the mock server responses

### Debugging Tips

1. **Enable debug logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **View request history**:
   ```bash
   python -m fogis_api_client.cli.mock_server history
   ```

3. **Disable request validation for debugging**:
   ```bash
   python -m fogis_api_client.cli.mock_server validation --disable
   ```

4. **Test endpoints directly**:
   ```bash
   python -m fogis_api_client.cli.mock_server test --endpoint /mdk/MatchWebMetoder.aspx/HamtaMatchLista --data '{}'
   ```

5. **Use the Flask debug mode**:
   ```python
   server = MockFogisServer()
   server.app.debug = True
   server.run()
   ```

## Contributing to the Mock Server

### Contribution Guidelines

When contributing to the mock server, please follow these guidelines:

1. **Follow the project's coding style**:
   - Use PEP 8 for Python code
   - Add docstrings to all functions and classes
   - Include type hints for function parameters and return values

2. **Write tests for your changes**:
   - Add unit tests for new functionality
   - Update existing tests if necessary
   - Ensure all tests pass before submitting a PR

3. **Document your changes**:
   - Update this documentation file if necessary
   - Add comments to explain complex code
   - Update the README if your changes affect the user experience

4. **Submit a pull request**:
   - Provide a clear description of your changes
   - Reference any related issues
   - Follow the PR template

### Development Workflow

1. **Set up your development environment**:
   ```bash
   # Clone the repository
   git clone https://github.com/PitchConnect/fogis-api-client-python.git
   cd fogis-api-client-python

   # Install development dependencies
   pip install -e ".[dev,mock-server]"
   ```

2. **Make your changes**:
   - Create a new branch for your feature or bug fix
   - Implement your changes
   - Add or update tests as necessary
   - Update documentation as necessary

3. **Test your changes**:
   ```bash
   # Run the unit tests
   pytest tests

   # Run the integration tests
   pytest integration_tests
   ```

4. **Submit a pull request**:
   - Push your branch to GitHub
   - Create a pull request
   - Respond to review comments

### Best Practices

- **Keep the mock server lightweight**: Avoid adding unnecessary dependencies
- **Maintain compatibility**: Ensure the mock server behaves like the real FOGIS API
- **Use realistic data**: Generate sample data that resembles real API responses
- **Handle edge cases**: Implement error handling and edge cases
- **Document your changes**: Keep the documentation up to date

For more information on contributing to the project, see the [CONTRIBUTING.md](../CONTRIBUTING.md) file.
