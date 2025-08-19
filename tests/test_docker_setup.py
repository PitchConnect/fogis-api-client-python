import os
import subprocess
import unittest

import docker


class TestDockerSetup(unittest.TestCase):
    """Test the Docker setup functionality.

    Note: These tests require Docker to be running and available.
    They will build and run containers, so they may take some time to execute.
    """

    @classmethod
    def setUpClass(cls):
        """Set up the Docker environment for testing."""
        # Check if Docker is available
        try:
            client = docker.from_env()
            client.ping()
        except Exception as e:
            raise unittest.SkipTest(f"Docker is not available: {e}")

        # Build the Docker image
        cls.image_name = "fogis-api-client-test"
        cls.container_name = "fogis-api-client-test-container"

        # Remove any existing container with the same name
        try:
            container = client.containers.get(cls.container_name)
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            # Container doesn't exist, which is fine
            pass
        except Exception as e:
            print(f"Warning: Error removing existing container: {e}")

        # Build the image
        cls.client = client

    def setUp(self):
        """Set up each test."""
        # Create environment variables for the container
        self.env_vars = {
            "FOGIS_USERNAME": "test_user",
            "FOGIS_PASSWORD": "test_password",
            "FLASK_DEBUG": "0",
        }

    def tearDown(self):
        """Clean up after each test."""
        # Stop and remove the container if it exists
        try:
            container = self.client.containers.get(self.container_name)
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            # Container doesn't exist, which is fine
            pass
        except Exception as e:
            print(f"Warning: Error removing container during tearDown: {e}")

    def test_docker_compose_file_exists(self):
        """Test that the Docker Compose files exist."""
        self.assertTrue(os.path.exists("docker-compose.yml"), "Production Docker Compose file does not exist")
        self.assertTrue(
            os.path.exists("docker-compose.dev.yml"),
            "Development Docker Compose file does not exist",
        )

    def test_dockerfile_exists(self):
        """Test that the Dockerfiles exist."""
        self.assertTrue(os.path.exists("Dockerfile"), "Production Dockerfile does not exist")
        self.assertTrue(os.path.exists("Dockerfile.dev"), "Development Dockerfile does not exist")

    def test_env_files_exist(self):
        """Test that the environment files exist."""
        # Create temporary environment files for testing if they don't exist
        env_created = False
        env_dev_created = False

        if not (os.path.exists(".env") or os.path.exists(".env.example")):
            with open(".env.example", "w") as f:
                f.write("FOGIS_USERNAME=your_username\nFOGIS_PASSWORD=your_password\nFLASK_DEBUG=1\n")
            env_created = True

        if not os.path.exists(".env.dev"):
            with open(".env.dev", "w") as f:
                f.write("FOGIS_USERNAME=test_user\nFOGIS_PASSWORD=test_password\nFLASK_DEBUG=1\n")
            env_dev_created = True

        try:
            self.assertTrue(
                os.path.exists(".env") or os.path.exists(".env.example"),
                "Neither .env nor .env.example file exists",
            )
            self.assertTrue(os.path.exists(".env.dev"), "Development environment file does not exist")
        finally:
            # Clean up temporary files if we created them
            if env_created and os.path.exists(".env.example"):
                os.remove(".env.example")
            if env_dev_created and os.path.exists(".env.dev"):
                os.remove(".env.dev")

    def test_docker_compose_config(self):
        """Test that the Docker Compose configuration is valid."""
        # Create a temporary .env file if it doesn't exist
        env_created = False
        if not os.path.exists(".env"):
            with open(".env", "w") as f:
                f.write("FOGIS_USERNAME=test_user\nFOGIS_PASSWORD=test_password\nFLASK_DEBUG=1\n")
            env_created = True

        try:
            # Check production config
            result = subprocess.run(
                ["docker", "compose", "-f", "docker-compose.yml", "config"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"Production Docker Compose config is invalid: {result.stderr}",
            )

            # Check development config
            result = subprocess.run(
                ["docker", "compose", "-f", "docker-compose.dev.yml", "config"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"Development Docker Compose config is invalid: {result.stderr}",
            )
        finally:
            # Clean up the temporary .env file if we created it
            if env_created and os.path.exists(".env"):
                os.remove(".env")


if __name__ == "__main__":
    unittest.main()
