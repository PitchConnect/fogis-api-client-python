"""
Internal API layer for the FOGIS API client.

This module contains the internal implementation details of the FOGIS API client.
It is not intended to be used directly by users of the library.

The internal API layer is responsible for:
1. Communicating with the FOGIS API server
2. Converting between public and internal data formats
3. Handling authentication and session management
4. Implementing the low-level API contracts

This separation allows the public API to focus on usability and type safety,
while the internal API ensures compatibility with the server requirements.
"""
