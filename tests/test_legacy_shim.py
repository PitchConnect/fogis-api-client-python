import warnings
from unittest.mock import MagicMock, patch

import requests

from fogis_api_client.fogis_api_client import FogisApiClient


def test_legacy_shim_delegates_and_warns():
    with warnings.catch_warnings(record=True) as w, patch(
        "fogis_api_client.public_api_client.PublicApiClient", autospec=True
    ) as MockPublic:
        warnings.simplefilter("always")

        inst = FogisApiClient(username="u", password="p")
        # Instantiation should have warned
        assert any(issubclass(x.category, DeprecationWarning) for x in w)

        # Shim should have created a PublicApiClient instance
        assert MockPublic.called
        # Delegation via attribute access
        method = MagicMock(return_value=42)
        MockPublic.return_value.some_method = method
        assert inst.some_method() == 42
        method.assert_called_once()
