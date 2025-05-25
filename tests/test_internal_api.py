"""
Tests for the internal API layer.

These tests verify that the internal API layer correctly handles communication
with the FOGIS API server and properly converts between public and internal data formats.
"""
import pytest
from unittest.mock import MagicMock, patch

import requests

from fogis_api_client.internal.api_client import InternalApiClient


def test_internal_api_client_initialization():
    """Test that the internal API client can be initialized."""
    session = requests.Session()
    client = InternalApiClient(session)
    assert client.session == session
    assert client.BASE_URL == "https://fogis.svenskfotboll.se/mdk"
