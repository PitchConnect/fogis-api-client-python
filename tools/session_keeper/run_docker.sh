#!/bin/bash

# Helper script for running Fogis session tools in Docker

# Create data directory if it doesn't exist
mkdir -p data

# Check if .env file exists
if [ ! -f .env ]; then
  echo "Creating .env file from example..."
  cp .env.example .env
  echo "Please edit .env file with your credentials"
  exit 1
fi

# Function to show help
show_help() {
  echo "Fogis Session Tools Docker Helper"
  echo ""
  echo "Usage: ./run_docker.sh [command]"
  echo ""
  echo "Commands:"
  echo "  gui       Run the interactive GUI"
  echo "  keeper    Run the session keeper as a service"
  echo "  test      Run a session timeout test"
  echo "  status    Check the status of the session keeper"
  echo "  logs      View logs of the session keeper"
  echo "  stop      Stop all containers"
  echo "  help      Show this help message"
  echo ""
}

# Process command
case "$1" in
  gui)
    echo "Starting interactive GUI..."
    docker-compose run --rm session-gui
    ;;
  keeper)
    echo "Starting session keeper as a service..."
    docker-compose up -d session-keeper
    echo "Session keeper started. Check status with './run_docker.sh status'"
    ;;
  test)
    echo "Starting session timeout test..."
    docker-compose up -d timeout-test
    echo "Test started. View logs with './run_docker.sh logs test'"
    ;;
  status)
    echo "Checking session keeper status..."
    docker-compose exec session-keeper python /app/session_keeper/check_session_status.py
    ;;
  logs)
    if [ "$2" == "test" ]; then
      echo "Viewing timeout test logs..."
      docker-compose logs -f timeout-test
    else
      echo "Viewing session keeper logs..."
      docker-compose logs -f session-keeper
    fi
    ;;
  stop)
    echo "Stopping all containers..."
    docker-compose down
    ;;
  help|*)
    show_help
    ;;
esac
