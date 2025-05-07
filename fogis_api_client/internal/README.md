# Internal API Layer

This module contains the internal implementation details of the FOGIS API client.
It is not intended to be used directly by users of the library.

## Purpose

The internal API layer is responsible for:

1. Communicating with the FOGIS API server
2. Converting between public and internal data formats
3. Handling authentication and session management
4. Implementing the low-level API contracts

This separation allows the public API to focus on usability and type safety,
while the internal API ensures compatibility with the server requirements.

## Architecture

The internal API layer consists of the following components:

- `api_client.py`: The internal API client that handles communication with the FOGIS API server
- `api_contracts.py`: JSON Schema definitions for the API contracts
- `auth.py`: Authentication module for the FOGIS API client
- `types.py`: Internal type definitions for the FOGIS API client
- `adapters.py`: Adapters for converting between public and internal data formats

## Usage

The internal API layer is not intended to be used directly by users of the library.
Instead, users should use the public API client (`FogisApiClient`) which provides
a simpler, more user-friendly interface.

```python
# Don't do this
from fogis_api_client.internal.api_client import InternalApiClient

# Do this instead
from fogis_api_client import FogisApiClient
```

## Development

When developing the FOGIS API client, you should follow these guidelines:

1. Keep the public API stable and backward-compatible
2. Make changes to the internal API layer when necessary to accommodate server changes
3. Use the adapters to convert between public and internal data formats
4. Add tests for both the public and internal API layers
5. Document any changes to the internal API layer

## Testing

The internal API layer is tested using unit tests. You can run the tests with:

```bash
python -m pytest tests/test_internal_api.py
```
