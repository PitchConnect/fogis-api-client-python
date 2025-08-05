#!/usr/bin/env python3
"""
Script to check the health of Docker containers.

This script checks the health of Docker containers used in the integration tests.
It can be used to diagnose issues with the Docker setup.
"""

import json
import subprocess
import sys
from typing import Dict, List, Optional


def run_command(command: List[str]) -> str:
    """Run a command and return its output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command)}: {e}")
        print(f"Stderr: {e.stderr}")
        return ""


def get_containers() -> List[Dict]:
    """Get a list of all containers."""
    output = run_command(["docker", "ps", "-a", "--format", "{{json .}}"])
    if not output:
        return []

    containers = []
    for line in output.strip().split("\n"):
        if line:
            try:
                containers.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Error parsing container info: {line}")

    return containers


def get_container_logs(container_id: str) -> str:
    """Get logs for a container."""
    return run_command(["docker", "logs", container_id])


def get_container_health(container_id: str) -> Optional[Dict]:
    """Get health status for a container."""
    output = run_command(["docker", "inspect", "--format", "{{json .State.Health}}", container_id])
    if not output:
        return None

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print(f"Error parsing health info: {output}")
        return None


def get_network_info(network_name: str) -> Optional[Dict]:
    """Get information about a Docker network."""
    output = run_command(["docker", "network", "inspect", network_name])
    if not output:
        return None

    try:
        return json.loads(output)[0]
    except (json.JSONDecodeError, IndexError):
        print(f"Error parsing network info: {output}")
        return None


def check_dns_resolution() -> None:
    """Check DNS resolution between containers."""
    print("\n=== DNS Resolution Tests ===")

    # Get all containers
    containers = get_containers()
    if not containers:
        print("No containers found.")
        return

    # Get container names
    container_names = [container.get("Names", "") for container in containers]

    # For each container, try to resolve other containers
    for container in containers:
        container_id = container.get("ID", "")
        container_name = container.get("Names", "")

        print(f"\nTesting DNS resolution from {container_name}:")

        # Try to resolve localhost
        cmd = ["docker", "exec", container_id, "ping", "-c", "1", "localhost"]
        result = run_command(cmd)
        print(f"  localhost: {'Success' if 'bytes from' in result else 'Failed'}")

        # Try to resolve other containers
        for other_name in container_names:
            if other_name != container_name:
                cmd = ["docker", "exec", container_id, "ping", "-c", "1", other_name]
                result = run_command(cmd)
                print(f"  {other_name}: {'Success' if 'bytes from' in result else 'Failed'}")


def check_network_connectivity() -> None:
    """Check network connectivity between containers."""
    print("\n=== Network Connectivity Tests ===")

    # Get all containers
    containers = get_containers()
    if not containers:
        print("No containers found.")
        return

    # Get container IPs
    container_ips = {}
    for container in containers:
        container_id = container.get("ID", "")
        container_name = container.get("Names", "")

        # Get container IP
        cmd = ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", container_id]
        ip = run_command(cmd).strip()
        if ip:
            container_ips[container_name] = ip

    print("Container IPs:")
    for name, ip in container_ips.items():
        print(f"  {name}: {ip}")

    # For each container, try to connect to other containers
    for container in containers:
        container_id = container.get("ID", "")
        container_name = container.get("Names", "")

        print(f"\nTesting connectivity from {container_name}:")

        # Try to connect to other containers by IP
        for other_name, other_ip in container_ips.items():
            if other_name != container_name:
                cmd = [
                    "docker",
                    "exec",
                    container_id,
                    "curl",
                    "-s",
                    "-o",
                    "/dev/null",
                    "-w",
                    "%{http_code}",
                    f"http://{other_ip}:8080/health",
                ]
                result = run_command(cmd)
                print(f"  {other_name} ({other_ip}): {result}")


def main() -> int:
    """Run the health checks."""
    print("Checking Docker container health...")

    # Get all containers
    containers = get_containers()
    if not containers:
        print("No containers found.")
        return 1

    # Check each container
    for container in containers:
        container_id = container.get("ID", "")
        container_name = container.get("Names", "")
        container_status = container.get("Status", "")

        print(f"\n=== Container: {container_name} ({container_id}) ===")
        print(f"Status: {container_status}")

        # Get container IP
        cmd = ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", container_id]
        ip = run_command(cmd).strip()
        print(f"IP Address: {ip}")

        # Get health status
        health = get_container_health(container_id)
        if health:
            print(f"Health status: {health.get('Status', 'unknown')}")
            if health.get("Status") != "healthy":
                print("Last health check logs:")
                for log in health.get("Log", [])[-3:]:  # Show last 3 health check logs
                    print(f"  {log.get('Output', '')}")

        # Get container logs (last 10 lines)
        logs = get_container_logs(container_id)
        if logs:
            print("Last 10 log lines:")
            for line in logs.strip().split("\n")[-10:]:
                print(f"  {line}")

        # Check environment variables
        cmd = ["docker", "exec", container_id, "env"]
        env_vars = run_command(cmd)
        print("\nEnvironment variables:")
        for line in env_vars.strip().split("\n")[:10]:  # Show first 10 env vars
            print(f"  {line}")

    # Check network
    print("\n=== Network: fogis-network ===")
    network_info = get_network_info("fogis-network")
    if network_info:
        print(f"Driver: {network_info.get('Driver', 'unknown')}")
        print(f"Containers:")
        for container_id, container_info in network_info.get("Containers", {}).items():
            print(f"  {container_info.get('Name', 'unknown')}: {container_info.get('IPv4Address', 'unknown')}")
    else:
        print("Network not found or error getting network info.")

    # Check DNS resolution
    try:
        check_dns_resolution()
    except Exception as e:
        print(f"Error checking DNS resolution: {e}")

    # Check network connectivity
    try:
        check_network_connectivity()
    except Exception as e:
        print(f"Error checking network connectivity: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
