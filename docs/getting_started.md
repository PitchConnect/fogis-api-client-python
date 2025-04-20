# Getting Started with FOGIS API Client

This guide will help you get started with the FOGIS API Client library for interacting with the Swedish Football Association's FOGIS system.

## Installation

### Using pip

The simplest way to install the FOGIS API Client is using pip:

```bash
pip install fogis-api-client-timmyBird
```

### From Source

If you prefer to install from source:

```bash
git clone https://github.com/timmybird/fogis_api_client_python.git
cd fogis_api_client_python
pip install -e .
```

## Basic Configuration

### Setting Up Logging

The FOGIS API Client provides enhanced logging utilities that make it easy to configure logging for your application:

```python
from fogis_api_client import configure_logging

# Basic configuration with INFO level
configure_logging(level="INFO")

# For more detailed logs during development
configure_logging(
    level="DEBUG",
    format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Log to both console and file
configure_logging(
    level="INFO",
    log_to_console=True,
    log_to_file=True,
    log_file="fogis_api.log"
)
```

#### Advanced Logging Features

The FOGIS API Client also provides additional logging utilities:

```python
from fogis_api_client import get_logger, set_log_level, add_sensitive_filter

# Get a logger for a specific module
logger = get_logger("my_module")
logger.info("This is an info message")

# Change log level dynamically
set_log_level("DEBUG")

# Add a filter to mask sensitive information in logs
add_sensitive_filter()
logger.info("Password: secret123")  # Will log "Password: ********"
```

The sensitive filter automatically masks passwords, authentication tokens, and session IDs to prevent them from appearing in log files.

## Authentication Methods

The FOGIS API Client supports two authentication methods:

### 1. Username and Password Authentication

This is the simplest method, but requires storing credentials:

```python
from fogis_api_client import FogisApiClient

# Initialize with username and password
client = FogisApiClient(
    username="your_fogis_username",
    password="your_fogis_password"
)

# The client implements lazy login - it will authenticate automatically when needed
# You can also explicitly login if you want to pre-authenticate
client.login()
```

### 2. Cookie-Based Authentication (Recommended)

For improved security, you can authenticate using cookies instead of storing credentials:

```python
from fogis_api_client import FogisApiClient

# First, get cookies from a logged-in session
client = FogisApiClient(username="your_username", password="your_password")
client.login()
cookies = client.get_cookies()  # Save these cookies securely

# Later, in another session, use the saved cookies
client = FogisApiClient(cookies=cookies)
# No need to call login() - already authenticated with cookies
```

#### Validating Cookies

You can check if the cookies are still valid:

```python
client = FogisApiClient(cookies=cookies)
if client.validate_cookies():
    print("Cookies are valid")
else:
    print("Cookies have expired, need to login with credentials again")
```

## Environment Variables

For security, you can use environment variables for credentials:

```python
import os
from fogis_api_client import FogisApiClient

# Get credentials from environment variables
username = os.environ.get("FOGIS_USERNAME")
password = os.environ.get("FOGIS_PASSWORD")

client = FogisApiClient(username=username, password=password)
```

## Basic Usage Examples

### Fetching Match List

```python
from fogis_api_client import FogisApiClient, FogisLoginError, FogisAPIRequestError

try:
    client = FogisApiClient(username="your_username", password="your_password")
    matches = client.fetch_matches_list_json()

    if matches:
        print(f"Found {len(matches)} matches.")
        for match in matches:
            print(f"{match['datum']} - {match['hemmalag']} vs {match['bortalag']}")
    else:
        print("No matches found.")

except FogisLoginError as e:
    print(f"Login failed: {e}")
except FogisAPIRequestError as e:
    print(f"API request error: {e}")
```

### Fetching Match Details

```python
try:
    match_id = 123456  # Replace with actual match ID
    match = client.fetch_match_json(match_id)

    print(f"Match: {match['hemmalag']} vs {match['bortalag']}")
    print(f"Date: {match['datum']}")
    print(f"Venue: {match['arena']}")

except FogisAPIRequestError as e:
    print(f"API request error: {e}")
```

## Docker Usage

The FOGIS API Client can be run inside a Docker container, which provides a consistent environment and simplifies deployment.

### Using the Pre-built Docker Image

```bash
# Pull the Docker image
docker pull timmybird/fogis_api_client_python:latest

# Run a script using the Docker image
docker run --rm -v $(pwd):/app timmybird/fogis_api_client_python:latest python /app/your_script.py
```

### Building the Docker Image Locally

```bash
# Clone the repository
git clone https://github.com/timmybird/fogis_api_client_python.git
cd fogis_api_client_python

# Build the Docker image
docker build -t fogis_api_client .

# Run a script using the local image
docker run --rm -v $(pwd):/app fogis_api_client python /app/your_script.py
```

### Example Docker Script

Create a file named `docker_example.py` with the following content:

```python
import os
import logging
from fogis_api_client import FogisApiClient

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get credentials from environment variables
username = os.environ.get("FOGIS_USERNAME")
password = os.environ.get("FOGIS_PASSWORD")

# Initialize the client
client = FogisApiClient(username=username, password=password)

# Fetch matches
matches = client.fetch_matches_list_json()
print(f"Found {len(matches)} matches")

# Display the next 3 matches
for match in matches[:3]:
    print(f"{match['datum']} {match['tid']}: {match['hemmalag']} vs {match['bortalag']}")
```

Run the script with Docker, passing the credentials as environment variables:

```bash
docker run --rm -v $(pwd):/app \
  -e FOGIS_USERNAME="your_username" \
  -e FOGIS_PASSWORD="your_password" \
  timmybird/fogis_api_client_python:latest \
  python /app/docker_example.py
```

### Development with Docker

For development purposes, you can use the provided development script:

```bash
# Start the development environment
./dev.sh

# Inside the container, you can run tests and develop
python -m unittest discover tests
```

### Development Environment Setup

We provide setup scripts to make it easy to set up your development environment:

On macOS/Linux:
```bash
./scripts/setup_dev_env.sh
```

On Windows (PowerShell):
```powershell
.\scripts\setup_dev_env.ps1
```

These scripts will:
1. Create a virtual environment (if it doesn't exist)
2. Install the package in development mode with all dev dependencies
3. Install pre-commit and set up the hooks

For more details, see the [Development Setup](../README.md#development-setup) section in the README.

## Next Steps

- Explore the [API Reference](api_reference.md) for detailed information about all available methods
- Check out the [User Guides](user_guides/README.md) for step-by-step instructions for common tasks
- See the [Troubleshooting](troubleshooting.md) section if you encounter any issues
