# FOGIS API Client CLI Tools

This directory contains command-line interface (CLI) tools for the FOGIS API client.

## Available Tools

### Mock Server

The mock server CLI tool provides a convenient way to start and manage the mock FOGIS API server for development and testing.

#### Usage

```bash
# Start the mock server with default settings
python -m fogis_api_client.cli.mock_server

# Specify host and port
python -m fogis_api_client.cli.mock_server --host 0.0.0.0 --port 5001

# Show help
python -m fogis_api_client.cli.mock_server --help
```

#### Options

- `--host HOST`: Host to bind the server to (default: localhost)
- `--port PORT`: Port to run the server on (default: 5001)

#### Programmatic Usage

You can also use the mock server CLI tool programmatically:

```python
from fogis_api_client.cli.mock_server import run_server

# Start the mock server with default settings
run_server()

# Specify host and port
run_server(host="0.0.0.0", port=5001)
```
