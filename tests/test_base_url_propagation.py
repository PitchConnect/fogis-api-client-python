import os
from unittest.mock import MagicMock, patch

import requests

from fogis_api_client.public_api_client import PublicApiClient


def test_base_url_env_propagation_to_internal_and_auth(monkeypatch):
    # Arrange environment override
    base = "https://example.test/mdk"
    monkeypatch.setenv("FOGIS_API_BASE_URL", base)

    # Spy on InternalApiClient and authenticate
    with patch("fogis_api_client.internal.api_client.InternalApiClient.__init__", return_value=None) as mock_init, patch(
        "fogis_api_client.internal.auth.authenticate", return_value={}
    ) as mock_auth:
        client = PublicApiClient(username="u", password="p")

        # Internal client should be constructed with base URL
        mock_init.assert_called()
        # The second positional arg after session is base_url (or via kw)
        args, kwargs = mock_init.call_args
        assert isinstance(args[0], requests.Session)
        # base_url passed via kwargs
        assert kwargs.get("base_url") == base

        # When login happens, it should pass the same base_url to authenticate
        client.login()
        mock_auth.assert_called()
        auth_args = mock_auth.call_args.args
        assert auth_args[2] == "p"  # password
        assert auth_args[3] == base  # base_url
