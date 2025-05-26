# FOGIS API Client CLI Tools

This directory contains command-line interface (CLI) tools for the FOGIS API client.

## Available Tools

### Mock Server

The mock server CLI tool provides a convenient way to start and manage the mock FOGIS API server for development and testing.

#### Usage

```bash
# Show help
python -m fogis_api_client.cli.mock_server --help

# Start the mock server with default settings
python -m fogis_api_client.cli.mock_server start

# Specify host and port
python -m fogis_api_client.cli.mock_server start --host 0.0.0.0 --port 5001

# Check the status of the mock server
python -m fogis_api_client.cli.mock_server status

# Stop the mock server
python -m fogis_api_client.cli.mock_server stop
```

#### Global Options

- `--host HOST`: Host where the mock server is running (default: localhost)
- `--port PORT`: Port where the mock server is running (default: 5001)

#### Commands

##### Start

Start the mock FOGIS API server.

```bash
python -m fogis_api_client.cli.mock_server start [options]
```

Options:
- `--host HOST`: Host to bind the server to (default: localhost)
- `--port PORT`: Port to run the server on (default: 5001)
- `--threaded`: Run the server in a separate thread
- `--wait`: Wait for the server to start before returning

##### Stop

Stop the running mock FOGIS API server.

```bash
python -m fogis_api_client.cli.mock_server stop
```

##### Status

Check the status of the mock FOGIS API server.

```bash
python -m fogis_api_client.cli.mock_server status [options]
```

Options:
- `--json`: Output in JSON format

##### History

View and manage the request history.

```bash
python -m fogis_api_client.cli.mock_server history view [options]
python -m fogis_api_client.cli.mock_server history clear
python -m fogis_api_client.cli.mock_server history export <file>
python -m fogis_api_client.cli.mock_server history import <file>
```

Options for `view`:
- `--limit N`: Limit the number of requests to show (default: 10)
- `--json`: Output in JSON format

##### Validation

Manage request validation.

```bash
python -m fogis_api_client.cli.mock_server validation status
python -m fogis_api_client.cli.mock_server validation enable
python -m fogis_api_client.cli.mock_server validation disable
```

##### Test

Test an endpoint.

```bash
python -m fogis_api_client.cli.mock_server test <endpoint> [options]
```

Options:
- `--method METHOD`: The HTTP method to use (default: GET)
- `--data DATA`: The data to send (JSON string)
- `--headers HEADERS`: The headers to send (JSON string)
- `--json`: Output in JSON format

Example:
```bash
python -m fogis_api_client.cli.mock_server test /mdk/Login.aspx --method POST --data '{"ctl00$cphMain$tbUsername": "test_user", "ctl00$cphMain$tbPassword": "test_password"}'
```

#### Programmatic Usage

You can also use the mock server CLI tool programmatically:

```python
# Start the server
from fogis_api_client.cli.commands.start import StartCommand
from argparse import Namespace

command = StartCommand()
args = Namespace(host="localhost", port=5001, threaded=False, wait=False)
command.execute(args)

# Or use the backward-compatible function
from fogis_api_client.cli.mock_server import run_server

# Start the mock server with default settings
run_server()

# Specify host and port
run_server(host="0.0.0.0", port=5001)
```

### Integration with Pytest

The project includes a pytest plugin that makes it easy to use the mock server in tests. The plugin provides fixtures for automatically starting and stopping the mock server, as well as configuring the API client for testing.

To use the plugin, simply include the fixtures in your test functions:

```python
def test_some_functionality(mock_server_auto, mock_api_urls_auto):
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

See the [integration tests README](../../integration_tests/README.md) for more details on using the pytest plugin.
