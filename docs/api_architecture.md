# API Architecture

This document provides a detailed explanation of the FOGIS API Client architecture, focusing on the separation between public and internal APIs.

## Overview

The FOGIS API Client is designed with a clean architecture that separates the public API (what users interact with) from the internal implementation details (how we communicate with the FOGIS server). This separation provides several benefits:

1. **Stability**: The public API can remain stable even when the FOGIS server API changes
2. **Usability**: The public API can focus on providing a user-friendly interface
3. **Compatibility**: The internal API ensures compatibility with the FOGIS server requirements
4. **Maintainability**: Changes to server communication don't affect the public interface

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Application                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Public API Layer                          │
│                      (FogisApiClient class)                      │
│                                                                  │
│  • Provides user-friendly methods                                │
│  • Uses simple, consistent data structures                       │
│  • Handles high-level error reporting                            │
│  • Manages authentication automatically                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Adapter Layer                            │
│                                                                  │
│  • Converts between public and internal data formats             │
│  • Transforms flat structures to nested when needed              │
│  • Applies default values for optional fields                    │
│  • Ensures type consistency                                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Internal API Layer                         │
│                    (InternalApiClient class)                     │
│                                                                  │
│  • Handles low-level communication with FOGIS server             │
│  • Implements exact API contracts required by server             │
│  • Validates requests and responses                              │
│  • Manages session details                                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          FOGIS Server                            │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Public API Layer

The public API layer is implemented in `fogis_api_client/public_api_client.py` and provides a user-friendly interface for interacting with the FOGIS API. This is what users of the library directly interact with.

Key characteristics:
- Simple, intuitive method names
- Consistent data structures
- Automatic authentication
- Comprehensive error handling
- Type hints for better IDE support

Example usage:
```python
from fogis_api_client import FogisApiClient

# Create a client instance
client = FogisApiClient(username="your_username", password="your_password")

# Get matches to report
matches = client.get_matches_to_report()

# Report a match result
result = {
    "matchid": 123456,
    "hemmamal": 2,
    "bortamal": 1,
    "halvtidHemmamal": 1,
    "halvtidBortamal": 0
}
client.report_match_result(result)
```

### 2. Adapter Layer

The adapter layer is implemented in `fogis_api_client/internal/adapters.py` and is responsible for converting between the public API data formats (what users work with) and the internal API data formats (what the FOGIS server expects).

Key functions:
- `convert_match_result_to_internal`: Converts a flat match result to the nested format expected by the server
- `convert_internal_to_match_result`: Converts a nested server response to a flat, user-friendly format
- `convert_event_to_internal`: Applies default values and ensures correct types for event data
- Other conversion functions for different data types

Example of data transformation:
```python
# Public API (flat format, user-friendly)
flat_result = {
    "matchid": 123456,
    "hemmamal": 2,
    "bortamal": 1,
    "halvtidHemmamal": 1,
    "halvtidBortamal": 0
}

# Internal API (nested format, server requirement)
nested_result = {
    "matchresultatListaJSON": [
        {
            "matchid": 123456,
            "matchresultattypid": 1,  # Full-time
            "matchlag1mal": 2,
            "matchlag2mal": 1,
            "wo": False,
            "ow": False,
            "ww": False
        },
        {
            "matchid": 123456,
            "matchresultattypid": 2,  # Half-time
            "matchlag1mal": 1,
            "matchlag2mal": 0,
            "wo": False,
            "ow": False,
            "ww": False
        }
    ]
}
```

### 3. Internal API Layer

The internal API layer is implemented in `fogis_api_client/internal/api_client.py` and handles the low-level communication with the FOGIS server. It ensures that the data sent to and received from the server matches the expected format.

Key components:
- `InternalApiClient`: Handles HTTP requests to the FOGIS server
- `api_contracts.py`: Defines JSON Schema for validating requests and responses
- `auth.py`: Handles authentication with the FOGIS server
- `types.py`: Defines TypedDict classes for internal data structures

This layer is not intended to be used directly by users of the library.

## Type System

The FOGIS API Client uses TypedDict classes to define the structure of data:

1. **Public Types** (in `fogis_api_client/types.py`):
   - `MatchDict`: Match information
   - `PlayerDict`: Player information
   - `EventDict`: Event information
   - `MatchResultDict`: Match result information

2. **Internal Types** (in `fogis_api_client/internal/types.py`):
   - `InternalMatchDict`: Internal match information
   - `InternalPlayerDict`: Internal player information
   - `InternalEventDict`: Internal event information
   - `InternalMatchResultDict`: Internal match result information

The adapter layer converts between these two type systems.

## API Contracts

The API contracts are defined in `fogis_api_client/internal/api_contracts.py` using JSON Schema. These schemas define the expected structure of data sent to and received from the FOGIS server.

The validation system ensures that:
1. Requests match the expected format before sending to the server
2. Responses match the expected format before processing
3. API contracts are maintained during development

## How to Extend the API

When adding new functionality to the FOGIS API Client, follow these steps:

1. **Understand the FOGIS server API**:
   - Determine the endpoint URL
   - Identify the required request format
   - Understand the response format

2. **Add internal API support**:
   - Add JSON Schema definitions to `api_contracts.py`
   - Add TypedDict classes to `internal/types.py` if needed
   - Implement the method in `InternalApiClient`

3. **Add adapter functions**:
   - Create conversion functions in `internal/adapters.py`
   - Ensure proper type conversion and validation

4. **Add public API method**:
   - Implement a user-friendly method in `FogisApiClient`
   - Add comprehensive documentation
   - Include type hints

5. **Add tests**:
   - Unit tests for each layer
   - Integration tests for the complete flow

### Example: Adding a New Endpoint

Let's say we want to add support for a new endpoint that retrieves referee assignments:

1. **Add internal API method**:
```python
def get_referee_assignments(self, referee_id: int) -> List[Dict[str, Any]]:
    """
    Get referee assignments for a specific referee.

    Args:
        referee_id: The ID of the referee

    Returns:
        List[Dict[str, Any]]: Referee assignments

    Raises:
        InternalApiError: If the request fails
    """
    url = f"{self.BASE_URL}/RefereeWebMetoder.aspx/GetRefereeAssignments"
    payload = {"refereeid": referee_id}

    response_data = self.api_request(url, payload)

    if not isinstance(response_data, list):
        error_msg = f"Invalid referee assignments response: {response_data}"
        self.logger.error(error_msg)
        raise InternalApiError(error_msg)

    return response_data
```

2. **Add adapter function**:
```python
def convert_internal_to_referee_assignment(
    internal_assignment: Dict[str, Any]
) -> RefereeAssignmentDict:
    """
    Converts an internal referee assignment to the public format.

    Args:
        internal_assignment: Referee assignment data from the API

    Returns:
        RefereeAssignmentDict: Referee assignment in the public format
    """
    # For now, the formats are the same, so we just cast
    return cast(RefereeAssignmentDict, internal_assignment)
```

3. **Add public API method**:
```python
def get_referee_assignments(self) -> List[RefereeAssignmentDict]:
    """
    Get referee assignments for the logged-in referee.

    Returns:
        List[RefereeAssignmentDict]: List of referee assignments

    Raises:
        FogisAPIRequestError: If the API request fails
        FogisLoginError: If not logged in or session expired
    """
    # Ensure we're logged in
    if not self.cookies:
        self.login()

    try:
        # Get the referee ID from the session (implementation detail)
        referee_id = self._get_referee_id()

        # Use the internal API client to get referee assignments
        internal_assignments = self.internal_client.get_referee_assignments(referee_id)

        # Convert to public format
        return [
            convert_internal_to_referee_assignment(assignment)
            for assignment in internal_assignments
        ]
    except InternalApiError as e:
        error_msg = f"Failed to get referee assignments: {e}"
        self.logger.error(error_msg)
        raise FogisAPIRequestError(error_msg) from e
```

## Best Practices

When working with the FOGIS API Client, follow these best practices:

1. **Never use the internal API directly**:
   ```python
   # Don't do this
   from fogis_api_client.internal.api_client import InternalApiClient

   # Do this instead
   from fogis_api_client import FogisApiClient
   ```

2. **Use the adapter functions for data conversion**:
   ```python
   # Don't manually convert between formats
   # Do use the adapter functions
   from fogis_api_client.internal.adapters import convert_match_result_to_internal
   ```

3. **Add validation for new endpoints**:
   ```python
   # Add JSON Schema definitions for new endpoints
   REQUEST_SCHEMAS["/NewEndpoint"] = NEW_ENDPOINT_SCHEMA
   ```

4. **Keep the public API stable**:
   - Avoid breaking changes to the public API
   - Use deprecation warnings before removing features
   - Add new features in a backward-compatible way

5. **Document all changes**:
   - Update docstrings with detailed information
   - Add examples for new features
   - Update this architecture document when necessary

## Conclusion

The separation between public and internal APIs in the FOGIS API Client provides a robust architecture that is both user-friendly and maintainable. By understanding this separation, you can effectively use and extend the library while maintaining compatibility with the FOGIS server.
