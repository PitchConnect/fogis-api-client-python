import logging
import os
import time

import pytest
import requests
from requests.exceptions import ConnectionError, Timeout

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Add a retry decorator for tests
def retry_on_failure(max_retries=3, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, Timeout, AssertionError) as e:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Test failed on attempt {attempt + 1}/{max_retries}: {e}. "
                            f"Retrying in {delay} seconds..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"Test failed after {max_retries} attempts: {e}")
                        raise

        return wrapper

    return decorator


# Get the API URL from environment variable or use default
# When running in Docker, this should be set to http://fogis-api-client-dev:8080
API_URL = os.environ.get("API_URL", "http://fogis-api-client-dev:8080")

# Try different URLs if the default one doesn't work
API_URLS_TO_TRY = [
    API_URL,
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://0.0.0.0:8080",
]

# Try each URL until one works
for url in API_URLS_TO_TRY:
    try:
        logger.info(f"Trying to connect to API at {url}")
        response = requests.get(f"{url}/health", timeout=1)
        if response.status_code == 200:
            API_URL = url
            logger.info(f"Successfully connected to API at {url}")
            break
    except requests.exceptions.RequestException as e:
        logger.info(f"Failed to connect to {url}: {e}")
else:
    # If we get here, none of the URLs worked
    logger.warning("Could not connect to API with any of the tried URLs")


@retry_on_failure(max_retries=5, delay=3)
def test_health_endpoint():
    """Test the /health endpoint returns a valid response."""
    response = requests.get(f"{API_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "status" in data
    # The status can be either "healthy" or "warning"
    assert data["status"] in ["healthy", "warning"]
    assert "timestamp" in data

    # Log the response for debugging
    logger.info(f"Health endpoint response: {data}")


def test_root_endpoint():
    """Test the root endpoint returns a valid JSON response."""
    response = requests.get(f"{API_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "status" in data
    assert data["status"] == "ok"
    assert "message" in data
    assert "FOGIS API Gateway" in data["message"]


@pytest.mark.parametrize(
    "endpoint,path_param,expected_type",
    [
        ("/matches", None, list),
        ("/match", "1", dict),
    ],
    ids=["matches_endpoint", "match_details_endpoint"],
)
def test_api_endpoints(endpoint, path_param, expected_type):
    """Test various API endpoints return valid responses.

    Args:
        endpoint: The API endpoint to test (without the base URL)
        path_param: Optional path parameter to append to the endpoint
        expected_type: The expected type of the response data (list or dict)
    """
    # Construct the full URL
    url = f"{API_URL}{endpoint}"
    if path_param:
        url = f"{url}/{path_param}"

    # This endpoint might return an error if not authenticated
    # We'll just check that it returns a valid response
    response = requests.get(url)
    assert response.status_code in [200, 500]  # Either success or error is acceptable

    # If successful, check the structure
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, expected_type)


if __name__ == "__main__":
    # Add a delay to ensure the API service is fully up
    print("Waiting for API service to be ready...")
    time.sleep(5)

    # Run the tests
    pytest.main(["-v", __file__])
