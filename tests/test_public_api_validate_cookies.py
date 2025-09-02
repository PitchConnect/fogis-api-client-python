from unittest.mock import MagicMock, patch

import requests

from fogis_api_client.public_api_client import PublicApiClient


def test_validate_cookies_true_on_welcome_page():
    client = PublicApiClient(
        cookies={
            "FogisMobilDomarKlient_ASPXAUTH": "A",
            "ASP_NET_SessionId": "B",
        }
    )

    mock_resp = MagicMock()
    mock_resp.text = "<html>Welcome</html>"
    mock_resp.url = "https://fogis.svenskfotboll.se/mdk/"
    mock_resp.raise_for_status = lambda: None

    with patch.object(requests.Session, "get", return_value=mock_resp):
        assert client.validate_cookies() is True


def test_validate_cookies_false_on_login():
    client = PublicApiClient(
        cookies={
            "FogisMobilDomarKlient_ASPXAUTH": "A",
            "ASP_NET_SessionId": "B",
        }
    )

    mock_resp = MagicMock()
    mock_resp.text = "<html>Logga in</html>"
    mock_resp.url = "https://fogis.svenskfotboll.se/mdk/Login.aspx"
    mock_resp.raise_for_status = lambda: None

    with patch.object(requests.Session, "get", return_value=mock_resp):
        assert client.validate_cookies() is False


def test_validate_cookies_false_on_exception():
    client = PublicApiClient(
        cookies={
            "FogisMobilDomarKlient_ASPXAUTH": "A",
            "ASP_NET_SessionId": "B",
        }
    )

    with patch.object(requests.Session, "get", side_effect=requests.exceptions.RequestException("boom")):
        assert client.validate_cookies() is False
