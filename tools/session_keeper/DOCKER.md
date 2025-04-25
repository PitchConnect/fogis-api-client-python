# Containerized Fogis Session Tools

This directory contains Docker configurations for running the Fogis session management tools in containers.

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Fogis account credentials

### Setup

1. Create a `.env` file in the `tools/session_keeper` directory:

```
FOGIS_USERNAME=your_username
FOGIS_PASSWORD=your_password
INTERVAL=1800  # Session check interval in seconds (optional, default: 1800)
```

2. Create a data directory for persistence:

```bash
mkdir -p tools/session_keeper/data
```

### Running the Interactive GUI

```bash
cd tools/session_keeper
docker-compose run --rm session-gui
```

This will start the interactive menu interface where you can:
- Login and save cookies
- Maintain a session
- Check session status
- Test session timeout
- Test cookie uniqueness

### Running the Session Keeper as a Service

```bash
cd tools/session_keeper
docker-compose up -d session-keeper
```

This will start a long-running service that maintains your Fogis session.

### Running a Session Timeout Test

```bash
cd tools/session_keeper
docker-compose up -d timeout-test
```

This will start a service that tests how long a session remains valid without activity.

## Container Services

The `docker-compose.yml` file defines three services:

### 1. session-gui

An interactive service that provides a text-based menu interface for all session management tools.

```bash
# Start the GUI
docker-compose run --rm session-gui

# Or with a specific command
docker-compose run --rm session-gui python /app/session_keeper/test_cookie_uniqueness.py --username "your_username" --password "your_password"
```

### 2. session-keeper

A long-running service that maintains your Fogis session by making periodic requests.

```bash
# Start the service
docker-compose up -d session-keeper

# View logs
docker-compose logs -f session-keeper

# Check status
docker-compose exec session-keeper python /app/session_keeper/check_session_status.py
```

### 3. timeout-test

A service that tests how long a session remains valid without activity.

```bash
# Start the test
docker-compose up -d timeout-test

# View logs
docker-compose logs -f timeout-test
```

## Data Persistence

All data (cookies, logs, status files) is stored in the `tools/session_keeper/data` directory, which is mounted as a volume in the containers. This ensures that your data persists across container restarts.

## Customization

### Environment Variables

You can customize the behavior of the containers by setting environment variables in the `.env` file:

- `FOGIS_USERNAME`: Your Fogis username
- `FOGIS_PASSWORD`: Your Fogis password
- `INTERVAL`: Session check interval in seconds (default: 1800)

### Custom Commands

You can run custom commands in the containers:

```bash
# Run a specific script
docker-compose run --rm session-gui python /app/session_keeper/fogis_session_keeper.py --help

# Execute a command in a running container
docker-compose exec session-keeper python /app/session_keeper/check_session_status.py
```

## Troubleshooting

### Container Fails to Start

If a container fails to start, check the logs:

```bash
docker-compose logs session-keeper
```

### Session Expires Too Quickly

If your session expires too quickly, try decreasing the check interval:

```bash
# Edit .env file
INTERVAL=900  # 15 minutes

# Restart the service
docker-compose restart session-keeper
```

### Data Not Persisting

Make sure the data directory exists and has the correct permissions:

```bash
mkdir -p tools/session_keeper/data
chmod 777 tools/session_keeper/data
```
