# Mock Server Examples

This document provides practical examples of using the mock server for development and testing.

## Basic Usage Examples

### Starting and Stopping the Mock Server

```bash
# Start the mock server
python -m fogis_api_client.cli.mock_server start

# Check if the mock server is running
python -m fogis_api_client.cli.mock_server status

# Stop the mock server
python -m fogis_api_client.cli.mock_server stop
```

### Using the Mock Server with the API Client

```python
from fogis_api_client import FogisApiClient

# Create a client that points to the mock server
client = FogisApiClient(
    username="test_user",
    password="test_password",
    base_url="http://localhost:5001/mdk"
)

# Login to the mock server
client.login()

# Fetch matches
matches = client.get_matches()
print(f"Found {len(matches)} matches")

# Fetch match details
match_id = matches[0]["matchid"]
match_details = client.get_match(match_id)
print(f"Match details: {match_details}")
```

### Testing Endpoints Directly

```bash
# Test the match list endpoint
python -m fogis_api_client.cli.mock_server test --endpoint /mdk/MatchWebMetoder.aspx/HamtaMatchLista --data '{}'

# Test the match details endpoint with a match ID
python -m fogis_api_client.cli.mock_server test --endpoint /mdk/MatchWebMetoder.aspx/HamtaMatch --data '{"matchid": 12345}'
```

## Development Workflows

### Local Development with Mock Server

This workflow is useful when developing new features without requiring real FOGIS credentials:

1. Start the mock server in a separate terminal:
   ```bash
   python -m fogis_api_client.cli.mock_server start
   ```

2. In your development environment, configure the client to use the mock server:
   ```python
   client = FogisApiClient(
       username="test_user",
       password="test_password",
       base_url="http://localhost:5001/mdk"
   )
   ```

3. Develop and test your feature using the mock server.

4. When you're done, stop the mock server:
   ```bash
   python -m fogis_api_client.cli.mock_server stop
   ```

### Integration Testing with Mock Server

This workflow is useful for running integration tests in CI/CD environments:

1. In your test file, use the `mock_api_urls` fixture to automatically start and stop the mock server:
   ```python
   def test_fetch_matches(mock_api_urls):
       # The mock_api_urls fixture starts the mock server and configures the client
       client = FogisApiClient(username="test_user", password="test_password")
       
       # Fetch matches
       matches = client.get_matches()
       
       # Assert the result
       assert len(matches) > 0
       assert "matchid" in matches[0]
   ```

2. Run the tests:
   ```bash
   pytest integration_tests/test_api_endpoints.py
   ```

### Debugging with Request History

This workflow is useful for debugging issues with API requests:

1. Start the mock server:
   ```bash
   python -m fogis_api_client.cli.mock_server start
   ```

2. Make some API requests using your client.

3. View the request history:
   ```bash
   python -m fogis_api_client.cli.mock_server history
   ```

4. Clear the request history if needed:
   ```bash
   python -m fogis_api_client.cli.mock_server history --clear
   ```

## Advanced Examples

### Customizing the Mock Server

#### Adding Custom Test Data

```python
# In your test file
from integration_tests.mock_fogis_server import MockFogisServer
from integration_tests.sample_data_factory import MockDataFactory

# Override the match list generator method
def custom_generate_match_list():
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
                }
            ]
        })
    }

# Replace the original method with your custom one
MockDataFactory.generate_match_list = custom_generate_match_list

# Start the mock server with your customized data
server = MockFogisServer()
server.run(threaded=True)

# Now your client will receive the custom data
client = FogisApiClient(
    username="test_user",
    password="test_password",
    base_url=f"http://localhost:{server.port}/mdk"
)
matches = client.get_matches()
# matches will contain your custom data

# Don't forget to stop the server when you're done
server.stop()
```

#### Disabling Request Validation

```python
# Start the mock server with request validation disabled
from integration_tests.mock_fogis_server import MockFogisServer

server = MockFogisServer()
server.validate_requests = False
server.run(threaded=True)

# Now you can send requests with any structure
# This is useful for testing error handling in your client

# Don't forget to stop the server when you're done
server.stop()
```

### Testing Error Scenarios

#### Testing Authentication Failures

```python
# Test with invalid credentials
client = FogisApiClient(
    username="invalid_user",
    password="invalid_password",
    base_url="http://localhost:5001/mdk"
)

try:
    client.login()
    print("Login succeeded (unexpected)")
except Exception as e:
    print(f"Login failed as expected: {e}")
```

#### Testing Server Errors

```python
# In your test file
from integration_tests.mock_fogis_server import MockFogisServer
import flask

# Create a custom route that returns an error
def add_error_endpoint(server):
    @server.app.route("/mdk/MatchWebMetoder.aspx/ErrorEndpoint", methods=["POST"])
    def error_endpoint():
        return flask.Response("Internal Server Error", status=500)

# Start the mock server with your custom endpoint
server = MockFogisServer()
add_error_endpoint(server)
server.run(threaded=True)

# Test how your client handles server errors
client = FogisApiClient(
    username="test_user",
    password="test_password",
    base_url=f"http://localhost:{server.port}/mdk"
)

try:
    # You would need to add this method to your client
    client.call_error_endpoint()
    print("Call succeeded (unexpected)")
except Exception as e:
    print(f"Call failed as expected: {e}")

# Don't forget to stop the server when you're done
server.stop()
```

## Common Development Tasks

### Testing a New API Endpoint

When adding support for a new FOGIS API endpoint, follow these steps:

1. Start the mock server:
   ```bash
   python -m fogis_api_client.cli.mock_server start
   ```

2. Implement the new endpoint in the mock server (see the [Mock Server Documentation](../mock_server.md) for details).

3. Implement the client method that calls the new endpoint.

4. Test the new method against the mock server:
   ```python
   client = FogisApiClient(
       username="test_user",
       password="test_password",
       base_url="http://localhost:5001/mdk"
   )
   
   result = client.new_endpoint_method()
   print(f"Result: {result}")
   ```

5. Add integration tests for the new endpoint.

6. Stop the mock server when you're done:
   ```bash
   python -m fogis_api_client.cli.mock_server stop
   ```

### Debugging Request Validation Issues

If your requests are failing validation, follow these steps:

1. View the request history to see what's being sent:
   ```bash
   python -m fogis_api_client.cli.mock_server history
   ```

2. Check the schema in `integration_tests/schemas/` to see what's expected.

3. Temporarily disable validation for debugging:
   ```bash
   python -m fogis_api_client.cli.mock_server validation --disable
   ```

4. Fix your client code to send the correct request structure.

5. Re-enable validation:
   ```bash
   python -m fogis_api_client.cli.mock_server validation --enable
   ```

## IDE Integration

### VSCode

Add these configurations to your `.vscode/launch.json` file:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run with Mock Server",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true,
            "env": {
                "FOGIS_API_BASE_URL": "http://localhost:5001/mdk",
                "FOGIS_USERNAME": "test_user",
                "FOGIS_PASSWORD": "test_password"
            },
            "preLaunchTask": "Start Mock Server"
        }
    ]
}
```

And add this to your `.vscode/tasks.json` file:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start Mock Server",
            "type": "shell",
            "command": "python -m fogis_api_client.cli.mock_server start --threaded",
            "isBackground": true,
            "problemMatcher": []
        }
    ]
}
```

### PyCharm

1. Create a Run Configuration for your script.
2. Add these environment variables:
   - `FOGIS_API_BASE_URL=http://localhost:5001/mdk`
   - `FOGIS_USERNAME=test_user`
   - `FOGIS_PASSWORD=test_password`
3. Add a "Before launch" task to start the mock server:
   - Click "Add" > "Run External Tool"
   - Create a new External Tool with:
     - Program: `python`
     - Arguments: `-m fogis_api_client.cli.mock_server start --threaded`
     - Working directory: `$ProjectFileDir$`
