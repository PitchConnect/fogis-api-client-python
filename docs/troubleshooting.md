# Troubleshooting

This guide provides solutions for common issues you might encounter when using the FOGIS API Client.

## Table of Contents

1. [Authentication Issues](#authentication-issues)
2. [API Request Errors](#api-request-errors)
3. [Data Errors](#data-errors)
4. [Match Reporting Issues](#match-reporting-issues)
5. [Performance Issues](#performance-issues)
6. [Docker Issues](#docker-issues)
7. [Mock Server Issues](#mock-server-issues)
8. [Common Error Messages](#common-error-messages)
9. [Frequently Asked Questions](#frequently-asked-questions)

## Authentication Issues

### Issue: Login Fails with Invalid Credentials

**Symptoms:**
- `FogisLoginError: Login failed: Invalid credentials or session issue`
- Unable to authenticate with the FOGIS API

**Possible Causes:**
- Incorrect username or password
- Account is locked or disabled
- FOGIS system is undergoing maintenance

**Solutions:**
1. Double-check your username and password for typos
2. Try resetting your FOGIS password
3. Check if your account is locked by trying to log in to the FOGIS website
4. Wait and try again later if FOGIS is undergoing maintenance

**Example:**
```python
try:
    client = FogisApiClient(username="your_username", password="your_password")
    client.login()
except FogisLoginError as e:
    print(f"Login failed: {e}")
    # Check if it's a credentials issue
    if "Invalid credentials" in str(e):
        print("Please check your username and password")
    # Check if it's a session issue
    elif "session issue" in str(e):
        print("FOGIS may be undergoing maintenance, try again later")
```

### Issue: Session Expires Quickly

**Symptoms:**
- Authentication works initially but fails after a short period
- `FogisLoginError: Login failed: Session expired`

**Possible Causes:**
- FOGIS session timeout settings
- Multiple clients using the same credentials
- Network issues causing session interruptions

**Solutions:**
1. Implement session validation before making requests
2. Re-authenticate when the session expires
3. Use cookie-based authentication for longer sessions

**Example:**
```python
def make_api_request_with_retry(client, request_func, *args, **kwargs):
    try:
        return request_func(*args, **kwargs)
    except FogisLoginError:
        # Session expired, try to re-authenticate
        print("Session expired, re-authenticating...")
        client.login()
        # Retry the request
        return request_func(*args, **kwargs)

# Usage
client = FogisApiClient(username="your_username", password="your_password")
matches = make_api_request_with_retry(client, client.fetch_matches_list_json)
```

### Issue: Cookie-Based Authentication Fails

**Symptoms:**
- `FogisLoginError: Login failed: No credentials provided and no cookies available`
- Unable to authenticate with saved cookies

**Possible Causes:**
- Cookies have expired
- Cookies are invalid or corrupted
- FOGIS has changed its authentication mechanism

**Solutions:**
1. Validate cookies before using them
2. Fall back to username/password authentication if cookies fail
3. Implement a mechanism to refresh cookies periodically

**Example:**
```python
# Try cookie-based authentication first
try:
    client = FogisApiClient(cookies=saved_cookies)
    if client.validate_cookies():
        print("Cookie authentication successful")
    else:
        # Fall back to username/password
        print("Cookies invalid, falling back to credentials")
        client = FogisApiClient(username="your_username", password="your_password")
        client.login()
        # Save the new cookies
        new_cookies = client.get_cookies()
except Exception as e:
    print(f"Authentication error: {e}")
```

## API Request Errors

### Issue: Network Connection Errors

**Symptoms:**
- `FogisAPIRequestError: API request failed: ConnectionError`
- Intermittent failures when making API requests

**Possible Causes:**
- Network connectivity issues
- FOGIS API server is down or unreachable
- Firewall or proxy blocking the connection

**Solutions:**
1. Implement retry logic with exponential backoff
2. Check your network connection
3. Verify that the FOGIS API is accessible from your network

**Example:**
```python
import time
from requests.exceptions import ConnectionError

def api_request_with_retry(client, request_func, *args, max_retries=3, **kwargs):
    retries = 0
    while retries < max_retries:
        try:
            return request_func(*args, **kwargs)
        except FogisAPIRequestError as e:
            if "ConnectionError" in str(e) and retries < max_retries - 1:
                wait_time = 2 ** retries  # Exponential backoff
                print(f"Connection error, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                retries += 1
            else:
                raise
```

### Issue: Timeout Errors

**Symptoms:**
- `FogisAPIRequestError: API request failed: ReadTimeout`
- Requests take a long time and eventually fail

**Possible Causes:**
- FOGIS API is slow to respond
- Network latency issues
- Large data sets being requested

**Solutions:**
1. Increase the timeout value for requests
2. Break large requests into smaller chunks
3. Implement retry logic for timeout errors

**Example:**
```python
from fogis_api_client import FogisApiClient

# Create a client with a custom timeout
client = FogisApiClient(username="your_username", password="your_password")
client.session.timeout = 30  # Increase timeout to 30 seconds

# Or for a specific request
try:
    # Get a large match list with a longer timeout
    all_matches = client.fetch_matches_list_json()
except FogisAPIRequestError as e:
    if "ReadTimeout" in str(e):
        print("Request timed out. Try breaking it into smaller date ranges.")
```

### Issue: Rate Limiting

**Symptoms:**
- `FogisAPIRequestError: API request failed: 429 Too Many Requests`
- Multiple requests fail in quick succession

**Possible Causes:**
- Too many requests in a short period
- FOGIS API rate limits being enforced
- Multiple instances of the client making requests simultaneously

**Solutions:**
1. Implement rate limiting in your application
2. Add delays between requests
3. Use a single instance of the client for all requests

**Example:**
```python
import time

def rate_limited_request(client, request_func, *args, **kwargs):
    try:
        return request_func(*args, **kwargs)
    except FogisAPIRequestError as e:
        if "429" in str(e):
            print("Rate limited, waiting before retrying...")
            time.sleep(5)  # Wait 5 seconds before retrying
            return request_func(*args, **kwargs)
        else:
            raise
```

## Data Errors

### Issue: Missing or Invalid Data

**Symptoms:**
- `FogisDataError: Expected dictionary response but got NoneType: None`
- `FogisDataError: Invalid response data: 'matcher' key not found`
- Data returned from the API is incomplete or malformed

**Possible Causes:**
- API changes in the FOGIS system
- Incorrect parameters in the request
- Data not available for the requested resource

**Solutions:**
1. Check that the parameters in your request are correct
2. Verify that the data exists in the FOGIS system
3. Add defensive programming to handle missing data

**Example:**
```python
try:
    match = client.fetch_match_json(match_id)

    # Defensive programming to handle potentially missing data
    home_team = match.get('hemmalag', 'Unknown')
    away_team = match.get('bortalag', 'Unknown')
    match_date = match.get('datum', 'Unknown')

    print(f"Match: {home_team} vs {away_team} on {match_date}")
except FogisDataError as e:
    print(f"Data error: {e}")
    if "Expected dictionary" in str(e):
        print(f"Match with ID {match_id} might not exist")
```

### Issue: JSON Parsing Errors

**Symptoms:**
- `FogisDataError: Failed to parse API response: Expecting value: line 1 column 1 (char 0)`
- Unexpected data format in the response

**Possible Causes:**
- API returning non-JSON responses (e.g., HTML error pages)
- Malformed JSON in the response
- Character encoding issues

**Solutions:**
1. Check if the FOGIS API is returning error pages
2. Verify that your request is properly formatted
3. Add error handling for JSON parsing failures

**Example:**
```python
try:
    matches = client.fetch_matches_list_json()
except FogisDataError as e:
    if "Failed to parse API response" in str(e):
        print("The API returned a non-JSON response. FOGIS might be down or returning an error page.")
        # You could try to extract information from the error response
        # or implement a fallback mechanism
```

### Issue: Unexpected Data Types

**Symptoms:**
- `TypeError: string indices must be integers`
- `AttributeError: 'str' object has no attribute 'get'`
- Errors when processing data returned from the API

**Possible Causes:**
- API response format has changed
- Incorrect assumptions about data types
- Edge cases in the data

**Solutions:**
1. Add type checking for API responses
2. Use defensive programming techniques
3. Update your code to handle different data formats

**Example:**
```python
def safe_process_match(match):
    if not isinstance(match, dict):
        print(f"Warning: Expected match to be a dictionary, got {type(match)}")
        return None

    try:
        return {
            'id': match.get('matchid'),
            'home_team': match.get('hemmalag', 'Unknown'),
            'away_team': match.get('bortalag', 'Unknown'),
            'date': match.get('datum', 'Unknown'),
            'score': f"{match.get('hemmamal', 0)}-{match.get('bortamal', 0)}"
        }
    except Exception as e:
        print(f"Error processing match data: {e}")
        return None

# Usage
matches = client.fetch_matches_list_json()
processed_matches = [m for m in (safe_process_match(match) for match in matches) if m is not None]
```

## Match Reporting Issues

### Issue: Unable to Report Events

**Symptoms:**
- `FogisAPIRequestError: API request failed: 400 Bad Request`
- Event reporting fails with error messages

**Possible Causes:**
- Missing required fields in the event data
- Invalid event type code
- Match is not in a reportable state
- Incorrect player or team IDs

**Solutions:**
1. Check that all required fields are included in the event data
2. Verify that the event type code is valid
3. Ensure the match is in a reportable state
4. Double-check player and team IDs

**Example:**
```python
# Validate event data before reporting
def validate_event_data(event_data):
    required_fields = ["matchid", "handelsekod", "minut", "lagid"]
    missing_fields = [field for field in required_fields if field not in event_data]

    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    # Check if event type is valid
    if event_data["handelsekod"] not in EVENT_TYPES:
        raise ValueError(f"Invalid event type code: {event_data['handelsekod']}")

    # For goal events, check score fields
    if EVENT_TYPES[event_data["handelsekod"]].get("goal", False):
        if "resultatHemma" not in event_data or "resultatBorta" not in event_data:
            raise ValueError("Goal events must include resultatHemma and resultatBorta")

    return True

# Usage
try:
    validate_event_data(event_data)
    response = client.report_match_event(event_data)
except ValueError as e:
    print(f"Invalid event data: {e}")
except FogisAPIRequestError as e:
    print(f"API error: {e}")
```

### Issue: Unable to Mark Reporting as Finished

**Symptoms:**
- `FogisAPIRequestError: API request failed: 400 Bad Request`
- Unable to complete the match reporting process

**Possible Causes:**
- Match result has not been reported
- Required events are missing
- Match is already marked as finished
- Insufficient permissions

**Solutions:**
1. Ensure the match result has been reported
2. Check that all required events have been reported
3. Verify that the match is not already marked as finished
4. Check your account permissions

**Example:**
```python
def complete_match_reporting(client, match_id, result_data):
    try:
        # First, report the match result
        result_response = client.report_match_result(result_data)
        if not result_response.get('success', False):
            print("Failed to report match result")
            return False

        # Then, mark reporting as finished
        finish_response = client.mark_reporting_finished(match_id)
        if finish_response.get('success', False):
            print("Match reporting completed successfully")
            return True
        else:
            print("Failed to mark reporting as finished")
            return False
    except FogisAPIRequestError as e:
        print(f"API error: {e}")
        return False
```

### Issue: Inconsistent Match Results

**Symptoms:**
- Match result does not match the reported goals
- Warning messages about inconsistent data

**Possible Causes:**
- Goals reported with incorrect scores
- Match result reported with different scores than the goals
- Events reported out of order

**Solutions:**
1. Ensure goal events update the score correctly
2. Make sure the final match result matches the last goal event
3. Report events in chronological order

**Example:**
```python
def report_goal_with_updated_score(client, match_id, team_id, player_id, minute, period, is_home_team):
    # First, get current events to calculate the current score
    events = client.fetch_match_events_json(match_id)
    goals = [e for e in events if e.get('mal', False)]

    # Calculate current score
    home_goals = sum(1 for g in goals if g.get('lagid') == home_team_id)
    away_goals = sum(1 for g in goals if g.get('lagid') == away_team_id)

    # Update score based on which team scored
    if is_home_team:
        home_goals += 1
    else:
        away_goals += 1

    # Create the goal event with the updated score
    goal_event = {
        "matchid": match_id,
        "handelsekod": 6,  # Regular goal
        "minut": minute,
        "lagid": team_id,
        "personid": player_id,
        "period": period,
        "resultatHemma": home_goals,
        "resultatBorta": away_goals
    }

    # Report the goal
    return client.report_match_event(goal_event)
```

## Performance Issues

### Issue: Slow API Responses

**Symptoms:**
- API requests take a long time to complete
- Timeouts or performance degradation

**Possible Causes:**
- Network latency
- FOGIS API server load
- Large data sets being requested

**Solutions:**
1. Implement caching for frequently accessed data
2. Use more specific queries to reduce data size
3. Implement asynchronous requests for parallel processing

## Docker Issues

### Issue: Volume Mounting Problems

**Symptoms:**
- `FileNotFoundError: [Errno 2] No such file or directory: '/app/your_script.py'`
- Unable to access files from the host machine

**Possible Causes:**
- Incorrect volume mounting syntax
- Relative paths instead of absolute paths
- Permissions issues on the host directory

**Solutions:**
1. Use absolute paths for volume mounting
2. Verify the host directory exists
3. Check file permissions on the host directory

**Example:**
```bash
# Correct volume mounting (using absolute path)
docker run --rm -v "$(pwd):/app" timmybird/fogis_api_client_python:latest python /app/your_script.py

# On Windows PowerShell
docker run --rm -v "${PWD}:/app" timmybird/fogis_api_client_python:latest python /app/your_script.py

# On Windows Command Prompt
docker run --rm -v "%cd%:/app" timmybird/fogis_api_client_python:latest python /app/your_script.py
```

### Issue: Environment Variable Problems

**Symptoms:**
- `FogisLoginError: Login failed: No credentials provided and no cookies available`
- Authentication fails when using environment variables

**Possible Causes:**
- Environment variables not passed to the container
- Incorrect environment variable names
- Quotes or special characters in passwords not properly escaped

**Solutions:**
1. Verify environment variables are passed correctly with `-e` flags
2. Check for typos in environment variable names
3. Properly escape special characters in passwords

**Example:**
```bash
# Passing environment variables correctly
docker run --rm -v "$(pwd):/app" \
  -e FOGIS_USERNAME="your_username" \
  -e FOGIS_PASSWORD="your_password" \
  timmybird/fogis_api_client_python:latest \
  python /app/your_script.py

# For passwords with special characters, use single quotes around the password
docker run --rm -v "$(pwd):/app" \
  -e FOGIS_USERNAME="your_username" \
  -e FOGIS_PASSWORD='your$pecial@password' \
  timmybird/fogis_api_client_python:latest \
  python /app/your_script.py
```

### Issue: Docker Image Not Found

**Symptoms:**
- `Error: No such image: timmybird/fogis_api_client_python:latest`
- Unable to run the Docker container

**Possible Causes:**
- Image not pulled from Docker Hub
- Typo in the image name
- Network connectivity issues

**Solutions:**
1. Pull the image explicitly before running
2. Check for typos in the image name
3. Verify network connectivity to Docker Hub

**Example:**
```bash
# Pull the image explicitly
docker pull timmybird/fogis_api_client_python:latest

# Verify the image is available
docker images | grep fogis_api_client
```

### Issue: Permission Denied in Container

**Symptoms:**
- `PermissionError: [Errno 13] Permission denied`
- Unable to write to mounted volumes

**Possible Causes:**
- File ownership issues in the container
- Read-only mounted volumes
- SELinux or AppArmor restrictions

**Solutions:**
1. Check file permissions on the host
2. Run the container with the same user ID as the host user
3. Temporarily disable SELinux or AppArmor for testing

**Example:**
```bash
# Run the container with the current user's UID
docker run --rm -v "$(pwd):/app" \
  --user "$(id -u):$(id -g)" \
  timmybird/fogis_api_client_python:latest \
  python /app/your_script.py
```

## Mock Server Issues

### Issue: Mock Server Won't Start

**Symptoms:**
- `OSError: [Errno 98] Address already in use`
- `ConnectionRefusedError: [Errno 111] Connection refused`
- Error when trying to start the mock server

**Possible Causes:**
- Port already in use by another process
- Missing dependencies
- Python path issues

**Solutions:**
1. Try a different port:
   ```bash
   python -m fogis_api_client.cli.mock_server start --port 5002
   ```

2. Check if the port is already in use:
   ```bash
   # On Linux/macOS
   lsof -i :5001

   # On Windows
   netstat -ano | findstr :5001
   ```

3. Ensure you've installed the package with mock server dependencies:
   ```bash
   pip install -e ".[dev,mock-server]"
   ```

4. Make sure you're running the command from the project root directory

**Example:**
```python
# Try a different port programmatically
from integration_tests.mock_fogis_server import MockFogisServer

try:
    server = MockFogisServer(port=5001)
    server.run(threaded=True)
except OSError:
    print("Port 5001 is already in use, trying port 5002...")
    server = MockFogisServer(port=5002)
    server.run(threaded=True)
```

### Issue: Authentication Failures with Mock Server

**Symptoms:**
- Tests fail with authentication errors
- `AuthenticationError: Failed to login` when using the mock server

**Possible Causes:**
- Using incorrect test credentials
- Cookie handling issues
- Session management problems

**Solutions:**
1. Use the default test credentials:
   ```python
   client = FogisApiClient(
       username="test_user",
       password="test_password",
       base_url="http://localhost:5001/mdk"
   )
   ```

2. Ensure your client is properly handling the authentication cookies

3. Check that the mock server is running and accessible:
   ```bash
   python -m fogis_api_client.cli.mock_server status
   ```

**Example:**
```python
# Verify the mock server is running before testing
import requests

def is_mock_server_running(host="localhost", port=5001):
    try:
        response = requests.get(f"http://{host}:{port}/mdk/Login.aspx")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

# Check if the server is running
if not is_mock_server_running():
    print("Mock server is not running. Starting it...")
    # Start the server
```

### Issue: Request Validation Errors

**Symptoms:**
- Requests fail with validation errors
- `{"d": {"success": false, "error": "Invalid request structure"}}`
- Integration tests fail with validation errors

**Possible Causes:**
- Request doesn't match the expected schema
- Missing required fields
- Incorrect data types
- Schema validation is too strict

**Solutions:**
1. Check the request structure against the schema in `integration_tests/schemas/`

2. View the request history to see what's being sent:
   ```bash
   python -m fogis_api_client.cli.mock_server history
   ```

3. Temporarily disable validation for debugging:
   ```bash
   python -m fogis_api_client.cli.mock_server validation --disable
   ```

4. Update the schema if the API has changed

**Example:**
```python
# Disable validation programmatically for debugging
from integration_tests.mock_fogis_server import MockFogisServer

server = MockFogisServer()
server.validate_requests = False  # Disable validation
server.run(threaded=True)

# Now you can send requests without validation
# This is useful for debugging
```

### Issue: Integration Tests Failing with Mock Server

**Symptoms:**
- Integration tests fail when run against the mock server
- `ConnectionRefusedError: [Errno 111] Connection refused`
- Tests pass locally but fail in CI/CD

**Possible Causes:**
- Mock server not running
- Wrong URL configuration
- Request validation failures
- Response handling issues

**Solutions:**
1. Use the `mock_api_urls` fixture to automatically start and stop the server:
   ```python
   def test_fetch_matches(mock_api_urls):
       client = FogisApiClient(username="test_user", password="test_password")
       matches = client.get_matches()
       assert len(matches) > 0
   ```

2. Check URL configuration:
   ```python
   # Make sure the base URL is correct
   client = FogisApiClient(
       username="test_user",
       password="test_password",
       base_url="http://localhost:5001/mdk"  # Correct URL for mock server
   )
   ```

3. Disable validation for debugging:
   ```bash
   python -m fogis_api_client.cli.mock_server validation --disable
   ```

4. Check Docker networking in CI/CD:
   ```yaml
   # In GitHub Actions workflow
   services:
     mock-server:
       image: fogis-mock-server:latest
       ports:
         - 5001:5001
   ```

**Example:**
```python
# Helper function to ensure mock server is running
def ensure_mock_server_running():
    import subprocess
    import time

    # Check if server is running
    try:
        result = subprocess.run(
            ["python", "-m", "fogis_api_client.cli.mock_server", "status"],
            capture_output=True,
            text=True
        )
        if "Mock server is running" in result.stdout:
            return True
    except Exception:
        pass

    # Start the server if not running
    subprocess.run(
        ["python", "-m", "fogis_api_client.cli.mock_server", "start", "--threaded"],
        capture_output=True
    )

    # Wait for server to start
    time.sleep(2)
    return True
```

## Common Error Messages

### "Login failed: Invalid credentials or session issue"

**Cause:** Authentication failed due to incorrect credentials or session problems.

**Solution:**
1. Double-check your username and password
2. Try logging in to the FOGIS website to verify your credentials
3. If your credentials are correct, the FOGIS system might be experiencing issues

### "Expected dictionary response but got NoneType: None"

**Cause:** The API returned None instead of the expected dictionary, often because the requested resource doesn't exist.

**Solution:**
1. Verify that the ID you're using (match ID, team ID, etc.) is correct
2. Check if the resource exists in the FOGIS system
3. Add error handling for missing resources

### "API request failed: ConnectionError"

**Cause:** Network connectivity issues prevented the request from reaching the FOGIS API.

**Solution:**
1. Check your internet connection
2. Verify that the FOGIS API is accessible
3. Implement retry logic with exponential backoff

### "Invalid response data: 'matcher' key not found"

**Cause:** The API response doesn't contain the expected 'matcher' key, possibly due to API changes or errors.

**Solution:**
1. Check if the FOGIS API has changed its response format
2. Verify that your request is properly formatted
3. Add defensive programming to handle missing keys

### "Failed to parse API response: Expecting value: line 1 column 1 (char 0)"

**Cause:** The API returned a non-JSON response, possibly an HTML error page.

**Solution:**
1. Check if the FOGIS API is returning error pages
2. Verify that your request is properly formatted
3. Add error handling for non-JSON responses

## Frequently Asked Questions

### How do I handle session expiration?

**Answer:** Implement a retry mechanism that re-authenticates when a session expires:

```python
def api_request_with_session_retry(client, request_func, *args, **kwargs):
    try:
        return request_func(*args, **kwargs)
    except FogisLoginError:
        # Session expired, re-authenticate
        print("Session expired, re-authenticating...")
        client.login()
        # Retry the request
        return request_func(*args, **kwargs)
```

### How can I improve performance when fetching large data sets?

**Answer:** Use filtering, pagination, and caching:

1. **Filtering:** Use date ranges or other filters to reduce the amount of data
2. **Pagination:** Process data in smaller chunks
3. **Caching:** Cache frequently accessed data to reduce API calls

### How do I report multiple events efficiently?

**Answer:** Use a batch processing approach:

```python
def report_multiple_events(client, events):
    results = []
    for event in events:
        try:
            response = client.report_match_event(event)
            results.append({
                'event': event,
                'success': response.get('success', False),
                'event_id': response.get('matchhandelseid'),
                'error': None
            })
        except Exception as e:
            results.append({
                'event': event,
                'success': False,
                'event_id': None,
                'error': str(e)
            })

    # Summarize results
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful

    print(f"Reported {successful} events successfully, {failed} failed")

    # Return details for further processing
    return results
```

### How do I handle API changes?

**Answer:** Implement version checking and defensive programming:

1. Check for API changes by monitoring response formats
2. Use defensive programming techniques like `get()` with default values
3. Implement feature detection instead of assuming specific API behavior

### How do I troubleshoot "Invalid event type code" errors?

**Answer:** Verify that you're using valid event type codes from the EVENT_TYPES dictionary:

```python
from fogis_api_client import EVENT_TYPES

# Print all available event types
for code, details in EVENT_TYPES.items():
    print(f"Code: {code}, Name: {details['name']}, Goal: {details['goal']}")

# Check if a specific code is valid
event_code = 6  # Regular goal
if event_code in EVENT_TYPES:
    print(f"Valid event type: {EVENT_TYPES[event_code]['name']}")
else:
    print(f"Invalid event type code: {event_code}")
```

### How do I use the mock server for development?

**Answer:** The mock server provides a simulated FOGIS API environment for development without requiring real credentials:

1. **Install the dependencies**:
   ```bash
   pip install -e ".[dev,mock-server]"
   ```

2. **Start the mock server**:
   ```bash
   python -m fogis_api_client.cli.mock_server start
   ```

3. **Configure your client to use the mock server**:
   ```python
   client = FogisApiClient(
       username="test_user",
       password="test_password",
       base_url="http://localhost:5001/mdk"
   )
   ```

4. **Develop and test your code against the mock server**

5. **Stop the mock server when you're done**:
   ```bash
   python -m fogis_api_client.cli.mock_server stop
   ```

### How do I add a new endpoint to the mock server?

**Answer:** To add a new endpoint to the mock server:

1. **Identify the endpoint details** (URL path, HTTP method, request/response structure)

2. **Add the endpoint to `mock_fogis_server.py`**:
   ```python
   @self.app.route("/mdk/MatchWebMetoder.aspx/NewEndpoint", methods=["POST"])
   def new_endpoint():
       auth_result = self._check_auth()
       if auth_result is not True:
           return auth_result

       # Get data from request
       data = request.json or {}

       # Generate response data
       response_data = {"success": True, "data": {"field1": "value1"}}

       # Return the response
       return jsonify({"d": json.dumps(response_data)})
   ```

3. **Add a data generator method to `sample_data_factory.py`** if needed

4. **Add a request schema in `integration_tests/schemas/`** for validation

5. **Update the request validator** to use the new schema

6. **Add integration tests** for the new endpoint

For more details, see the [Mock Server Documentation](docs/mock_server.md#extending-the-mock-server).

### How do I run integration tests with the mock server in CI/CD?

**Answer:** To run integration tests with the mock server in CI/CD:

1. **Add the mock server to your GitHub Actions workflow**:
   ```yaml
   jobs:
     integration-tests:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2

         - name: Set up Python
           uses: actions/setup-python@v2
           with:
             python-version: '3.9'

         - name: Install dependencies
           run: |
             python -m pip install --upgrade pip
             pip install -e ".[dev,mock-server]"

         - name: Start mock server
           run: |
             python -m fogis_api_client.cli.mock_server start --threaded

         - name: Run integration tests
           run: |
             pytest integration_tests/
   ```

2. **Use the `mock_api_urls` fixture in your tests**:
   ```python
   def test_fetch_matches(mock_api_urls):
       client = FogisApiClient(username="test_user", password="test_password")
       matches = client.get_matches()
       assert len(matches) > 0
   ```

3. **Or use Docker Compose**:
   ```yaml
   services:
     mock-server:
       build:
         context: .
         dockerfile: Dockerfile.mock
       ports:
         - "5001:5001"
   ```
