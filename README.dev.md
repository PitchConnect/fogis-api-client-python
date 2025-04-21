# Fogis API Client - Development Guide

This guide explains how to set up and use the development environment for the Fogis API Client.

## Development Environment

We provide a Docker-based development environment that makes it easy to develop and test the API client.

### Prerequisites

- Docker and Docker Compose
- Git

### Getting Started

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/fogis_api_client_python.git
   cd fogis_api_client_python
   ```

2. Create a `.env.dev` file with your development credentials:
   ```
   FOGIS_USERNAME=your_dev_username
   FOGIS_PASSWORD=your_dev_password
   FLASK_ENV=development
   FLASK_DEBUG=1
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Set up pre-commit hooks that match our CI/CD pipeline:
   ```bash
   ./update_precommit_hooks.sh
   ```

   This ensures your local checks match what runs in CI.

5. Start the development environment:
   ```bash
   ./dev.sh
   ```

   This will:
   - Build the Docker image for development
   - Start the container with the API client
   - Mount your local code into the container for live reloading
   - Show the logs from the container

6. Access the API at http://localhost:8080

### Running Integration Tests

To run the integration tests:

```
./run_integration_tests.sh
```

This will:
- Start the development environment if it's not already running
- Run the integration tests against the API
- Show the test results

### Development Workflow

1. Make changes to the code
2. The Flask server will automatically reload when you change Python files
3. Run the unit tests to verify your changes:
   ```bash
   python -m unittest discover tests
   ```
4. Run the integration tests to verify your changes:
   ```bash
   python -m pytest integration_tests
   ```
5. Run pre-commit hooks to ensure code quality:
   ```bash
   pre-commit run --all-files
   ```

   If the hooks indicate they need updating to match CI/CD, run:
   ```bash
   ./update_precommit_hooks.sh
   ```
6. Commit your changes when ready

### Docker Compose Configuration

The development environment uses `docker-compose.dev.yml`, which includes:

- Volume mounts for live code reloading
- Debug mode enabled
- Integration test service

### Project Structure

- `fogis_api_client/` - The main package
- `tests/` - Unit tests
- `integration_tests/` - Integration tests
- `docker-compose.dev.yml` - Development Docker Compose configuration
- `docker-compose.yml` - Production Docker Compose configuration
- `Dockerfile.dev` - Development Dockerfile
- `Dockerfile` - Production Dockerfile

## Contributing

1. Create a feature branch from develop:
   ```bash
   git checkout -b feature/your-feature-name develop
   ```

2. Make your changes

3. Run the tests:
   ```bash
   python -m unittest discover tests
   python -m pytest integration_tests
   ```

4. Run pre-commit hooks:
   ```bash
   pre-commit run --all-files
   ```

   If the hooks indicate they need updating to match CI/CD, run:
   ```bash
   ./update_precommit_hooks.sh
   ```

5. Push your branch and submit a pull request

For more detailed guidelines, please see [CONTRIBUTING.md](CONTRIBUTING.md).
