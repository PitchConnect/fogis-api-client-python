# Testing with Containerized Mock Server

This guide explains how to run tests using the containerized mock FOGIS API server. The containerized setup provides an isolated, consistent test environment that works the same way locally and in CI/CD.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Running Tests](#running-tests)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## Overview

The containerized test setup consists of two main components:

1. **Mock FOGIS Server** (`mock-fogis-server-test`): A Flask-based mock API server that simulates the FOGIS API
2. **Test Runner** (`test-runner`): A container that executes pytest tests against the mock server

These components are orchestrated using `docker-compose.test.yml`, which handles:
- Building the Docker images
- Setting up networking between containers
- Managing service dependencies and health checks
- Mounting test files and collecting results

### Benefits

✅ **Isolation**: Each test run gets a fresh mock server instance
✅ **Consistency**: Same environment locally, in CI, and for all developers
✅ **No Manual Setup**: No need to manually start the mock server
✅ **Easy Debugging**: Access to container logs and health endpoints
✅ **CI/CD Ready**: Seamlessly integrates with GitHub Actions

## Quick Start

### Prerequisites

- Docker (version 20.10 or later)
- Docker Compose (version 2.0 or later)

### Run All Tests

```bash
# Run all integration tests with containerized mock server
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Or use the CI test script
./run_ci_tests.sh
```

### Run Specific Tests

```bash
# Run a specific test file
docker-compose -f docker-compose.test.yml run --rm test-runner \
  pytest integration_tests/test_with_mock_server.py -v

# Run a specific test function
docker-compose -f docker-compose.test.yml run --rm test-runner \
  pytest integration_tests/test_with_mock_server.py::test_login -v

# Run tests matching a pattern
docker-compose -f docker-compose.test.yml run --rm test-runner \
  pytest integration_tests/ -k "match" -v
```

### Clean Up

```bash
# Stop and remove containers, networks, and volumes
docker-compose -f docker-compose.test.yml down -v
```

## Architecture

### Network Configuration

The test setup uses a dedicated Docker network (`fogis-test-network`) for container-to-container communication:

```
┌─────────────────────────────────────────┐
│     fogis-test-network (bridge)         │
│                                         │
│  ┌──────────────────┐                  │
│  │ mock-fogis-server│                  │
│  │   (port 5001)    │◄─────────┐       │
│  └──────────────────┘          │       │
│                                 │       │
│  ┌──────────────────┐          │       │
│  │   test-runner    │──────────┘       │
│  │  (runs pytest)   │                  │
│  └──────────────────┘                  │
│                                         │
└─────────────────────────────────────────┘
         │
         │ Port 5001 exposed
         │ (for debugging)
         ▼
    Host Machine
```

### Service Dependencies

The test runner depends on the mock server being healthy:

```yaml
test-runner:
  depends_on:
    mock-fogis-server:
      condition: service_healthy
```

This ensures tests don't start until the mock server is ready to accept requests.

### Health Checks

The mock server includes a health check endpoint (`/health`) that Docker monitors:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
  interval: 5s
  timeout: 3s
  retries: 5
  start_period: 10s
```

## Running Tests

### Using Docker Compose Directly

#### Run All Integration Tests

```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

The `--abort-on-container-exit` flag ensures that all containers stop when the test runner finishes.

#### Run Unit Tests Only

```bash
docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/ -v
```

#### Run with Coverage

```bash
docker-compose -f docker-compose.test.yml run --rm test-runner \
  pytest integration_tests/ --cov=fogis_api_client --cov-report=html
```

Coverage reports will be available in the `htmlcov/` directory.

#### Run in Verbose Mode

```bash
docker-compose -f docker-compose.test.yml run --rm test-runner \
  pytest integration_tests/ -vv --log-cli-level=DEBUG
```

### Using the CI Test Script

The `run_ci_tests.sh` script provides a more user-friendly interface:

```bash
# Run all tests
./run_ci_tests.sh

# Run specific test files
./run_ci_tests.sh "integration_tests/test_with_mock_server.py"

# Run with verbose output
./run_ci_tests.sh "" "-vv"
```

The script provides:
- Colored output for better readability
- Automatic cleanup on exit
- Health check verification
- Detailed error reporting
- Test summary

### Viewing Logs

#### View Mock Server Logs

```bash
# Follow logs in real-time
docker-compose -f docker-compose.test.yml logs -f mock-fogis-server

# View last 50 lines
docker-compose -f docker-compose.test.yml logs --tail=50 mock-fogis-server
```

#### View Test Runner Logs

```bash
docker-compose -f docker-compose.test.yml logs test-runner
```

#### View All Logs

```bash
docker-compose -f docker-compose.test.yml logs
```

## Environment Variables

### Test Runner Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_SERVER_URL` | `http://mock-fogis-server:5001` | URL of the mock server |
| `FOGIS_USERNAME` | `test_user` | Test username for authentication |
| `FOGIS_PASSWORD` | `test_password` | Test password for authentication |
| `PYTHONUNBUFFERED` | `1` | Disable Python output buffering |
| `PYTHONDONTWRITEBYTECODE` | `1` | Prevent creation of `.pyc` files |
| `PYTEST_ADDOPTS` | `--color=yes` | Additional pytest options |

### Mock Server Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_SERVER_PORT` | `5001` | Port the mock server listens on |
| `FLASK_ENV` | `testing` | Flask environment mode |
| `PYTHONUNBUFFERED` | `1` | Disable Python output buffering |

### Overriding Environment Variables

You can override environment variables using the `-e` flag:

```bash
docker-compose -f docker-compose.test.yml run --rm \
  -e MOCK_SERVER_URL=http://custom-server:5001 \
  test-runner pytest integration_tests/ -v
```

## Troubleshooting

### Mock Server Not Starting

**Symptom**: Tests fail with "Failed to connect to mock server"

**Solutions**:

1. Check if the mock server container is running:
   ```bash
   docker-compose -f docker-compose.test.yml ps
   ```

2. Check mock server logs:
   ```bash
   docker-compose -f docker-compose.test.yml logs mock-fogis-server
   ```

3. Verify the mock server is healthy:
   ```bash
   docker inspect mock-fogis-server-test --format='{{.State.Health.Status}}'
   ```

4. Try rebuilding the images:
   ```bash
   docker-compose -f docker-compose.test.yml build --no-cache
   ```

### Port Already in Use

**Symptom**: Error message "port is already allocated"

**Solutions**:

1. Check what's using port 5001:
   ```bash
   lsof -i :5001  # On macOS/Linux
   netstat -ano | findstr :5001  # On Windows
   ```

2. Stop the conflicting service or change the port in `docker-compose.test.yml`:
   ```yaml
   ports:
     - "5002:5001"  # Map host port 5002 to container port 5001
   ```

### Tests Timing Out

**Symptom**: Tests hang or timeout waiting for mock server

**Solutions**:

1. Increase health check timeout in `docker-compose.test.yml`:
   ```yaml
   healthcheck:
     start_period: 30s  # Increase from 10s
     timeout: 10s       # Increase from 3s
   ```

2. Check network connectivity:
   ```bash
   docker-compose -f docker-compose.test.yml exec test-runner \
     curl -v http://mock-fogis-server:5001/health
   ```

### Permission Denied Errors

**Symptom**: Cannot write to test-results or logs directories

**Solutions**:

1. Ensure directories exist and have correct permissions:
   ```bash
   mkdir -p test-results logs
   chmod 777 test-results logs
   ```

2. Run with appropriate user permissions:
   ```bash
   docker-compose -f docker-compose.test.yml run --rm --user $(id -u):$(id -g) test-runner
   ```

### Stale Containers or Networks

**Symptom**: Errors about existing containers or networks

**Solutions**:

1. Clean up all test resources:
   ```bash
   docker-compose -f docker-compose.test.yml down -v
   ```

2. Remove orphaned containers:
   ```bash
   docker-compose -f docker-compose.test.yml down --remove-orphans
   ```

3. Prune Docker system (use with caution):
   ```bash
   docker system prune -f
   ```

## Advanced Usage

### Running Tests in Parallel

```bash
docker-compose -f docker-compose.test.yml run --rm test-runner \
  pytest integration_tests/ -n auto
```

Note: Requires `pytest-xdist` to be installed in the test container.

### Interactive Debugging

Start a shell in the test container:

```bash
docker-compose -f docker-compose.test.yml run --rm test-runner /bin/bash
```

Then run tests manually:

```bash
pytest integration_tests/test_with_mock_server.py -v --pdb
```

### Custom Test Commands

Override the default command:

```bash
docker-compose -f docker-compose.test.yml run --rm test-runner \
  python -m pytest integration_tests/ --maxfail=1 --tb=short
```

### Accessing Mock Server from Host

The mock server is accessible from your host machine at `http://localhost:5001`:

```bash
# Check health
curl http://localhost:5001/health

# View Swagger UI
open http://localhost:5001/swagger  # macOS
xdg-open http://localhost:5001/swagger  # Linux
```

### Using with CI/CD

The setup is designed to work seamlessly in CI/CD environments. See `.github/workflows/integration-tests.yml` for an example GitHub Actions workflow.

Key considerations for CI:
- Use `--abort-on-container-exit` to ensure proper exit codes
- Collect test results and logs as artifacts
- Use `--no-cache` when building images to ensure fresh builds
- Set appropriate timeouts for health checks

## See Also

- [Mock Server Documentation](mock_server.md)
- [Integration Tests README](../integration_tests/README.md)
- [Contributing Guide](../CONTRIBUTING.md)
