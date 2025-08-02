# FOGIS API Client for Python

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/fogis-api-client-timmyBird.svg)](https://badge.fury.io/py/fogis-api-client-timmyBird)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive Python client library for interacting with the FOGIS API (Swedish Football Association). This library provides a simple, intuitive interface for referees and match officials to access match data, report results, manage events, and handle all aspects of match administration through the FOGIS system.

## 🎯 What is FOGIS?

FOGIS (Fotbollens Organisations- och Informationssystem) is the official system used by the Swedish Football Association (Svensk Fotboll) for managing football matches, referee assignments, and match reporting. This Python client provides programmatic access to FOGIS functionality.

## ✨ Key Features

- **🔐 Secure Authentication** - Support for both username/password and cookie-based authentication
- **⚽ Match Management** - Fetch match lists, get match details, and report results
- **📊 Advanced Filtering** - Powerful filtering system for matches by date, status, age category, gender, and more
- **🎯 Event Reporting** - Report goals, cards, substitutions, and other match events
- **👥 Team & Player Data** - Access team rosters, player information, and official details
- **🔄 Real-time Updates** - Mark matches as finished and update match status
- **🛡️ Type Safety** - Full type hints and TypedDict definitions for better IDE support
- **📝 Comprehensive Logging** - Built-in logging with sensitive data filtering
- **🧪 Testing Support** - Includes mock server for testing and development
- **🐳 Docker Ready** - Full Docker support for containerized deployments

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install fogis-api-client-timmyBird

# Or install with development dependencies
pip install fogis-api-client-timmyBird[dev]

# Or install with mock server support
pip install fogis-api-client-timmyBird[mock-server]
```

### Basic Usage

```python
from fogis_api_client import FogisApiClient, configure_logging

# Configure logging (optional)
configure_logging(level="INFO")

# Initialize the client
client = FogisApiClient(username="your_username", password="your_password")

# Fetch your assigned matches
matches = client.fetch_matches_list_json()
print(f"Found {len(matches)} matches")

# Display upcoming matches
for match in matches[:3]:
    print(f"{match['datum']} {match['tid']}: {match['hemmalag']} vs {match['bortalag']}")
```

### Using Filters for Historic Data

```python
from fogis_api_client import FogisApiClient, MatchListFilter
from fogis_api_client.enums import MatchStatus, AgeCategory
from datetime import datetime, timedelta

client = FogisApiClient(username="your_username", password="your_password")

# Create a filter for historic data
filter = MatchListFilter()
last_month = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
today = datetime.now().strftime('%Y-%m-%d')

# Fetch completed matches from the last month
historic_matches = (filter
    .start_date(last_month)
    .end_date(today)
    .include_statuses([MatchStatus.COMPLETED])
    .fetch_filtered_matches(client))

print(f"Found {len(historic_matches)} completed matches in the last month")
```


## 📖 Table of Contents

- [Installation](#-installation)
- [Authentication](#-authentication)
- [Basic Usage](#-basic-usage)
- [Advanced Filtering](#-advanced-filtering)
- [Match Management](#-match-management)
- [Event Reporting](#-event-reporting)
- [Error Handling](#-error-handling)
- [Docker Support](#-docker-support)
- [Development](#-development)
- [API Reference](#-api-reference)
- [Contributing](#-contributing)
- [License](#-license)

## 🔧 Installation

### From PyPI (Recommended)

```bash
pip install fogis-api-client-timmyBird
```

### From Source

```bash
git clone https://github.com/PitchConnect/fogis-api-client-python.git
cd fogis-api-client-python
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/PitchConnect/fogis-api-client-python.git
cd fogis-api-client-python
pip install -e ".[dev]"
```

## 🔐 Authentication

The FOGIS API Client supports two authentication methods:

### 1. Username and Password (Recommended for Development)

```python
from fogis_api_client import FogisApiClient

client = FogisApiClient(username="your_username", password="your_password")
# Authentication happens automatically on first API call (lazy login)
```

### 2. Cookie-based Authentication (Recommended for Production)

```python
# First, get cookies from a logged-in session
client = FogisApiClient(username="your_username", password="your_password")
cookies = client.login()  # Explicitly authenticate and get cookies

# Save cookies securely for later use
# Later, use saved cookies (more secure - no credentials in memory)
client = FogisApiClient(cookies=cookies)

# Validate cookies before use
if client.validate_cookies():
    matches = client.fetch_matches_list_json()
else:
    print("Cookies expired, need to re-authenticate")
```

## 🎯 Basic Usage

### Fetching Matches

```python
from fogis_api_client import FogisApiClient, FogisLoginError, FogisAPIRequestError

try:
    client = FogisApiClient(username="your_username", password="your_password")

    # Get all assigned matches
    matches = client.fetch_matches_list_json()
    print(f"Found {len(matches)} matches")

    # Display match information
    for match in matches:
        print(f"Match {match['matchid']}: {match['hemmalag']} vs {match['bortalag']}")
        print(f"Date: {match['datum']} {match['tid']}")
        print(f"Venue: {match['arena']}")
        print("---")

except FogisLoginError as e:
    print(f"Authentication failed: {e}")
except FogisAPIRequestError as e:
    print(f"API request failed: {e}")
```

### Reporting Match Results

```python
# Report a match result
result = {
    "matchid": 123456,
    "hemmamal": 2,        # Home team goals
    "bortamal": 1,        # Away team goals
    "halvtidHemmamal": 1, # Half-time home goals
    "halvtidBortamal": 0  # Half-time away goals
}

response = client.report_match_result(result)
if response.get('success'):
    print("Match result reported successfully!")
```

### Getting Match Details

```python
# Get detailed information about a specific match
match_id = 123456
match_details = client.get_match(match_id)
players = client.get_team_players(match_details['hemmalagid'])
officials = client.get_match_officials(match_id)
```

## 🔍 Advanced Filtering

The FOGIS API Client includes a powerful filtering system for querying matches with specific criteria. See the [Filter Documentation](docs/filter_guide.md) for comprehensive examples.

### Basic Date Range Filtering

```python
from fogis_api_client import MatchListFilter
from datetime import datetime, timedelta

# Create a filter for the last 7 days
filter = MatchListFilter()
week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
today = datetime.now().strftime('%Y-%m-%d')

matches = (filter
    .start_date(week_ago)
    .end_date(today)
    .fetch_filtered_matches(client))
```

### Status and Category Filtering

```python
from fogis_api_client.enums import MatchStatus, AgeCategory, Gender

# Filter for completed youth matches
matches = (MatchListFilter()
    .include_statuses([MatchStatus.COMPLETED])
    .include_age_categories([AgeCategory.YOUTH])
    .include_genders([Gender.MALE])
    .fetch_filtered_matches(client))
```

### Complex Filtering Examples

```python
# Get all postponed or cancelled matches from last month
last_month = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

problematic_matches = (MatchListFilter()
    .start_date(last_month)
    .end_date(today)
    .include_statuses([MatchStatus.POSTPONED, MatchStatus.CANCELLED])
    .fetch_filtered_matches(client))

# Exclude veteran matches, include only outdoor football
outdoor_non_veteran = (MatchListFilter()
    .exclude_age_categories([AgeCategory.VETERANS])
    .include_football_types([FootballType.FOOTBALL])
    .fetch_filtered_matches(client))
```

## ⚽ Match Management

### Getting Match Information

```python
# Get a specific match by ID
match = client.get_match(123456)
print(f"Match: {match['hemmalag']} vs {match['bortalag']}")
print(f"Status: {match['status']}")

# Get match result details
result = client.get_match_result(123456)
print(f"Score: {result['hemmamal']}-{result['bortamal']}")

# Get match officials
officials = client.get_match_officials(123456)
for official in officials:
    print(f"{official['roll']}: {official['fornamn']} {official['efternamn']}")
```

### Team and Player Information

```python
# Get team players
team_id = 12345
players = client.get_team_players(team_id)
for player in players:
    print(f"#{player['trojnummer']} {player['fornamn']} {player['efternamn']}")

# Get team officials
team_officials = client.get_team_officials(team_id)
```

### Match Status Management

```python
# Mark a match report as finished
response = client.mark_reporting_finished(123456)
if response.get('success'):
    print("Match reporting marked as complete")
```

## 🎯 Event Reporting

### Reporting Goals and Cards

```python
from fogis_api_client import EVENT_TYPES

# Report a goal
goal_event = {
    "matchid": 123456,
    "handelsekod": 6,  # Regular goal (see EVENT_TYPES)
    "minut": 25,       # 25th minute
    "lagid": 12345,    # Team ID
    "personid": 67890, # Player ID
    "resultatHemma": 1,
    "resultatBorta": 0
}

response = client.report_match_event(goal_event)

# Report a yellow card
card_event = {
    "matchid": 123456,
    "handelsekod": 20,  # Yellow card
    "minut": 42,
    "lagid": 12345,
    "personid": 67890
}

response = client.report_match_event(card_event)
```

### Available Event Types

```python
from fogis_api_client import EVENT_TYPES

# Print all available event types
for code, details in EVENT_TYPES.items():
    print(f"Code {code}: {details['name']} (Goal: {details.get('goal', False)})")
```

### Managing Match Events

```python
# Get all events for a match
events = client.get_match_events(123456)

# Clear all events for a match (use with caution!)
response = client.clear_match_events(123456)
```

## 🛡️ Error Handling

The library provides specific exception types for different error scenarios:

```python
from fogis_api_client import (
    FogisApiClient,
    FogisLoginError,
    FogisAPIRequestError,
    FogisDataError
)

try:
    client = FogisApiClient(username="user", password="pass")
    matches = client.fetch_matches_list_json()

except FogisLoginError as e:
    # Authentication failed - check credentials
    print(f"Login failed: {e}")

except FogisAPIRequestError as e:
    # Network or server error
    print(f"API request failed: {e}")

except FogisDataError as e:
    # Data parsing or validation error
    print(f"Data error: {e}")

except Exception as e:
    # Unexpected error
    print(f"Unexpected error: {e}")
```

### Common Error Scenarios

- **FogisLoginError**: Invalid credentials, expired session, account locked
- **FogisAPIRequestError**: Network issues, server downtime, rate limiting
- **FogisDataError**: Invalid response format, missing required fields

## 📝 Logging

The library includes comprehensive logging with sensitive data filtering:

```python
from fogis_api_client import configure_logging, get_logger

# Configure logging for the entire library
configure_logging(level="INFO")

# Get a logger for your module
logger = get_logger("my_module")
logger.info("This will be logged")

# Sensitive information is automatically filtered
logger.info("Password: secret123")  # Logs as "Password: ********"
```

### Available Log Levels

```python
from fogis_api_client import get_log_levels

levels = get_log_levels()
print(levels)  # {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50}
```
## 🐳 Docker Support

The library includes comprehensive Docker support for both development and production use.

### Production Deployment

1. Create a `.env` file with your credentials:
   ```env
   FOGIS_USERNAME=your_fogis_username
   FOGIS_PASSWORD=your_fogis_password
   ```

2. Start the service:
   ```bash
   docker compose up -d
   ```

3. Access the API gateway at http://localhost:8080

### Development Environment

```bash
# Start development environment with hot reload
./dev.sh

# Run integration tests in Docker
./run_integration_tests.sh

# Build and test Docker images
./scripts/verify_docker_build.sh
```

### Available Docker Images

- **Production**: Optimized for deployment
- **Development**: Includes dev tools and hot reload
- **Testing**: Configured for running tests
- **Mock Server**: Standalone mock FOGIS API

### Docker Compose Services

```yaml
services:
  fogis-api-client:    # Main API client service
  mock-server:         # Mock FOGIS API for testing
  integration-tests:   # Test runner service
```
## 🧪 Development & Testing

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/PitchConnect/fogis-api-client-python.git
cd fogis-api-client-python

# Set up development environment
./scripts/setup_dev_env.sh  # On macOS/Linux
# or
.\scripts\setup_dev_env.ps1  # On Windows PowerShell
```

### Running Tests

```bash
# Run unit tests
python -m pytest tests/

# Run integration tests with mock server
python scripts/run_integration_tests_with_mock.py

# Run all tests with coverage
python -m pytest --cov=fogis_api_client

# Run specific test file
python -m pytest tests/test_match_list_filter.py -v
```

### Mock Server for Development

The library includes a mock FOGIS API server for development and testing:

```bash
# Start mock server
python -m fogis_api_client.cli.mock_server

# Use mock server in your code
client = FogisApiClient(username="test", password="test")
# Point to mock server (automatically detected in test environment)
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hooks to match CI/CD
./update_precommit_hooks.sh
```

### Code Quality

The project maintains high code quality standards:

- **Type hints**: Full type annotations throughout
- **Linting**: flake8, black, isort
- **Testing**: pytest with comprehensive coverage
- **Documentation**: Comprehensive docstrings and examples
## 📚 API Reference

### Core Classes

- **`FogisApiClient`**: Main client class for API interactions
- **`MatchListFilter`**: Advanced filtering for match queries
- **`EVENT_TYPES`**: Dictionary of available match event types

### Exception Classes

- **`FogisLoginError`**: Authentication failures
- **`FogisAPIRequestError`**: API request failures
- **`FogisDataError`**: Data parsing/validation failures

### Type Definitions

- **`MatchDict`**: Match data structure
- **`PlayerDict`**: Player information structure
- **`EventDict`**: Match event structure
- **`OfficialDict`**: Official information structure

### Enums

- **`MatchStatus`**: Match status values (COMPLETED, CANCELLED, etc.)
- **`AgeCategory`**: Age categories (YOUTH, SENIOR, etc.)
- **`Gender`**: Gender categories (MALE, FEMALE, MIXED)
- **`FootballType`**: Football types (FOOTBALL, FUTSAL)

For detailed API documentation, see:
- [API Reference](docs/api_reference.md)
- [Getting Started Guide](docs/getting_started.md)
- [Filter Guide](docs/filter_guide.md)
- [Architecture Overview](docs/architecture.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Set up development environment: `./scripts/setup_dev_env.sh`
4. Make your changes and add tests
5. Run pre-merge check: `./pre-merge-check.sh`
6. Commit and push your changes
7. Create a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive tests
- Update documentation for new features
- Ensure all tests pass before submitting PR

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Authentication Problems
```python
# Problem: FogisLoginError
# Solution: Check credentials and account status
try:
    client = FogisApiClient(username="user", password="pass")
    client.login()  # Test authentication explicitly
except FogisLoginError as e:
    print(f"Check your credentials: {e}")
```

#### Network and API Issues
```python
# Problem: FogisAPIRequestError
# Solution: Implement retry logic and check connectivity
import time
from fogis_api_client import FogisAPIRequestError

def fetch_with_retry(client, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.fetch_matches_list_json()
        except FogisAPIRequestError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise e
```

#### Data Validation Issues
```python
# Problem: FogisDataError
# Solution: Validate data before sending
def safe_report_result(client, result_data):
    required_fields = ['matchid', 'hemmamal', 'bortamal']
    if not all(field in result_data for field in required_fields):
        raise ValueError(f"Missing required fields: {required_fields}")

    return client.report_match_result(result_data)
```

For more detailed troubleshooting, see [docs/troubleshooting.md](docs/troubleshooting.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

## 🙏 Acknowledgments

- Swedish Football Association (Svensk Fotboll) for providing the FOGIS system
- All contributors who have helped improve this library
- The Python community for excellent tools and libraries

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/PitchConnect/fogis-api-client-python/issues)
- **Discussions**: [GitHub Discussions](https://github.com/PitchConnect/fogis-api-client-python/discussions)

---

**Made with ⚽ for the Swedish football community**
