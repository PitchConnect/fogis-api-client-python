"""Session behaviour against the flows recorded in FOGIS_API.md §1 (mocked with `responses`)."""

import json
import stat
from pathlib import Path
from urllib.parse import parse_qs

import pytest
import requests
import responses
from responses import matchers
from responses.registries import OrderedRegistry

from fogis_api_client.errors import (
    FogisAPIRequestError,
    FogisAuthServiceUnavailableError,
    FogisDataError,
    FogisError,
    FogisInvalidCredentialsError,
    FogisLoginError,
    FogisSessionExpiredError,
)
from fogis_api_client.session import BASE_URL, LOGIN_URL, FogisSession

API = f"{BASE_URL}/MatchWebMetoder.aspx"
AUTHORIZE = "https://auth.fogis.se/connect/authorize?client_id=fogis.mobildomarklient"
LOGIN_PAGE = "https://auth.fogis.se/Account/LogIn?ReturnUrl=%2Fconnect%2Fauthorize%2Fcallback"
CALLBACK = "https://auth.fogis.se/connect/authorize/callback?client_id=fogis.mobildomarklient"
SIGNIN = f"{BASE_URL}/signin-oidc?code=abc"

LOGIN_FORM_HTML = """
<html><body>
<form method="post" action="/Account/Login?returnurl=%2Fconnect%2Fauthorize%2Fcallback">
  <input name="Username" type="text" value="">
  <input name="Password" type="password">
  <input name="RememberMe" type="checkbox" value="true">
  <input name="__RequestVerificationToken" type="hidden" value="tok123">
  <input name="RememberMe" type="hidden" value="false">
</form>
</body></html>
"""


def identity_cookie(session: FogisSession) -> None:
    session.import_cookies(
        [{"name": ".AspNetCore.Identity.Application", "value": "id", "domain": "auth.fogis.se", "path": "/"}]
    )


def add_expired_call(rsps: responses.RequestsMock, method: str = "GetMatchresultatlista") -> None:
    rsps.post(f"{API}/{method}", status=302, headers={"Location": AUTHORIZE})


def add_mdk_landing(rsps: responses.RequestsMock) -> None:
    """signin-oidc sets the new auth cookie and lands in /mdk/ (hops 5-7 of the recorded login)."""
    rsps.get(SIGNIN, status=302, headers={"Location": "/mdk/", "Set-Cookie": ".MDK.AuthCookie=new; Path=/"})
    rsps.get(f"{BASE_URL}/", status=200, body="<html>mdk</html>")


# ---------------------------------------------------------------- API calls


@responses.activate
def test_call_unwraps_d_and_sends_app_headers() -> None:
    responses.post(
        f"{API}/GetMatchresultatlista",
        json={"d": [{"matchresultattypid": 1}]},
        match=[
            matchers.json_params_matcher({"matchid": 1}),
            matchers.header_matcher({"X-Requested-With": "XMLHttpRequest"}),
        ],
    )
    assert FogisSession().call("GetMatchresultatlista", {"matchid": 1}) == [{"matchresultattypid": 1}]


@responses.activate
def test_every_request_has_a_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = []
    original = requests.Session.request

    def spy(self: requests.Session, *args: object, **kwargs: object) -> requests.Response:
        seen.append(kwargs.get("timeout"))
        return original(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(requests.Session, "request", spy)
    responses.post(f"{API}/GetApplicationConfig", json={"d": {}})
    FogisSession(timeout=(1, 2)).call("GetApplicationConfig")
    assert seen == [(1, 2)]


@responses.activate
def test_server_error_carries_status_and_aspnet_message() -> None:
    responses.post(f"{API}/GetMatchhandelselista", status=500, json={"Message": "Objektreferensen saknas"})
    with pytest.raises(FogisAPIRequestError, match="Objektreferensen saknas") as exc:
        FogisSession().call("GetMatchhandelselista", {"matchid": 1})
    assert exc.value.status_code == 500


@responses.activate
def test_non_json_answer_is_a_data_error() -> None:
    responses.post(f"{API}/GetMatchhandelselista", status=200, body="<html/>", content_type="text/html")
    with pytest.raises(FogisDataError):
        FogisSession().call("GetMatchhandelselista", {"matchid": 1})


@responses.activate
def test_network_error_is_chained() -> None:
    responses.post(f"{API}/GetMatchhandelselista", body=requests.ConnectionError("down"))
    with pytest.raises(FogisAPIRequestError) as exc:
        FogisSession().call("GetMatchhandelselista", {"matchid": 1})
    assert isinstance(exc.value.__cause__, requests.ConnectionError)


@responses.activate
def test_is_valid_does_not_follow_the_login_redirect() -> None:
    responses.post(f"{API}/GetApplicationConfig", status=302, headers={"Location": AUTHORIZE})
    assert FogisSession().is_valid() is False
    assert len(responses.calls) == 1


# ---------------------------------------------------------------- renewal


@responses.activate(registry=OrderedRegistry)
def test_expired_session_renews_silently_with_identity_cookie() -> None:
    add_expired_call(responses)
    responses.get(f"{BASE_URL}/", status=302, headers={"Location": AUTHORIZE})
    responses.get(AUTHORIZE, status=302, headers={"Location": SIGNIN})
    add_mdk_landing(responses)
    responses.post(f"{API}/GetMatchresultatlista", json={"d": []})

    session = FogisSession(username="u", password="p")
    identity_cookie(session)
    assert session.call("GetMatchresultatlista", {"matchid": 1}) == []
    assert not any("Account/Login" in c.request.url for c in responses.calls)
    assert session.has_cookie(".MDK.AuthCookie")


@responses.activate(registry=OrderedRegistry)
def test_expired_session_without_identity_cookie_logs_in_with_password() -> None:
    add_expired_call(responses)
    responses.get(LOGIN_URL, status=302, headers={"Location": AUTHORIZE})
    responses.get(AUTHORIZE, status=302, headers={"Location": LOGIN_PAGE})
    responses.get(LOGIN_PAGE, status=200, body=LOGIN_FORM_HTML)
    responses.post(
        "https://auth.fogis.se/Account/Login?returnurl=%2Fconnect%2Fauthorize%2Fcallback",
        status=302,
        headers={"Location": CALLBACK},
    )
    responses.get(CALLBACK, status=302, headers={"Location": SIGNIN})
    add_mdk_landing(responses)
    responses.post(f"{API}/GetMatchresultatlista", json={"d": []})

    session = FogisSession(username="Anna Domare", password="hemligt")
    assert session.call("GetMatchresultatlista", {"matchid": 1}) == []

    login_post = next(
        c for c in responses.calls if c.request.method == "POST" and "Account/Login" in c.request.url
    )
    sent = parse_qs(str(login_post.request.body))
    assert sent["Username"] == ["Anna Domare"]
    assert sent["Password"] == ["hemligt"]
    assert sent["RememberMe"] == ["true"]
    assert sent["__RequestVerificationToken"] == ["tok123"]


@responses.activate(registry=OrderedRegistry)
def test_failed_silent_reauth_falls_back_to_password() -> None:
    add_expired_call(responses)
    responses.get(f"{BASE_URL}/", status=302, headers={"Location": AUTHORIZE})
    responses.get(AUTHORIZE, status=302, headers={"Location": LOGIN_PAGE})
    responses.get(LOGIN_PAGE, status=200, body=LOGIN_FORM_HTML)  # identity cookie no longer accepted
    responses.get(LOGIN_URL, status=302, headers={"Location": LOGIN_PAGE})
    responses.get(LOGIN_PAGE, status=200, body=LOGIN_FORM_HTML)
    responses.post(
        "https://auth.fogis.se/Account/Login?returnurl=%2Fconnect%2Fauthorize%2Fcallback",
        status=302,
        headers={"Location": SIGNIN},
    )
    add_mdk_landing(responses)
    responses.post(f"{API}/GetMatchresultatlista", json={"d": []})

    session = FogisSession(username="u", password="p")
    identity_cookie(session)
    assert session.call("GetMatchresultatlista", {"matchid": 1}) == []


@responses.activate(registry=OrderedRegistry)
def test_rejected_password_raises_invalid_credentials() -> None:
    responses.get(LOGIN_URL, status=302, headers={"Location": LOGIN_PAGE})
    responses.get(LOGIN_PAGE, status=200, body=LOGIN_FORM_HTML)
    responses.post(
        "https://auth.fogis.se/Account/Login?returnurl=%2Fconnect%2Fauthorize%2Fcallback",
        status=200,
        body=LOGIN_FORM_HTML,
    )
    with pytest.raises(FogisInvalidCredentialsError):
        FogisSession(username="u", password="wrong").login()


@responses.activate
def test_auth_server_error_raises_service_unavailable() -> None:
    responses.get(LOGIN_URL, status=503)
    with pytest.raises(FogisAuthServiceUnavailableError):
        FogisSession(username="u", password="p").login()


@responses.activate
def test_unreachable_auth_service_raises_service_unavailable() -> None:
    responses.get(LOGIN_URL, body=requests.ConnectionError("no route"))
    with pytest.raises(FogisAuthServiceUnavailableError) as exc:
        FogisSession(username="u", password="p").login()
    assert isinstance(exc.value.__cause__, requests.ConnectionError)


@responses.activate
def test_expired_session_without_password_raises_session_expired() -> None:
    add_expired_call(responses)
    with pytest.raises(FogisSessionExpiredError):
        FogisSession().call("GetMatchresultatlista", {"matchid": 1})


@responses.activate(registry=OrderedRegistry)
def test_still_redirected_after_renewal_raises_session_expired() -> None:
    add_expired_call(responses)
    responses.get(f"{BASE_URL}/", status=302, headers={"Location": SIGNIN})
    add_mdk_landing(responses)
    add_expired_call(responses)

    session = FogisSession()
    identity_cookie(session)
    with pytest.raises(FogisSessionExpiredError):
        session.call("GetMatchresultatlista", {"matchid": 1})


def test_exception_hierarchy_keeps_0x_catch_clauses_working() -> None:
    for cls in (FogisInvalidCredentialsError, FogisAuthServiceUnavailableError, FogisSessionExpiredError):
        assert issubclass(cls, FogisLoginError)
    assert issubclass(FogisLoginError, FogisError)


# ---------------------------------------------------------------- cookie jar


@responses.activate
def test_reissued_auth_cookie_is_persisted(tmp_path: Path) -> None:
    jar = tmp_path / "cookies.json"
    responses.post(
        f"{API}/GetApplicationConfig",
        json={"d": {}},
        headers={"Set-Cookie": ".MDK.AuthCookie=reissued; Path=/; Secure; HttpOnly"},
    )
    FogisSession(cookie_file=jar).call("GetApplicationConfig")

    saved = json.loads(jar.read_text())
    assert [(c["name"], c["value"]) for c in saved] == [(".MDK.AuthCookie", "reissued")]
    assert stat.S_IMODE(jar.stat().st_mode) == 0o600


@responses.activate
def test_cookie_file_is_loaded_and_sent(tmp_path: Path) -> None:
    jar = tmp_path / "cookies.json"
    jar.write_text(
        json.dumps(
            [{"name": ".MDK.AuthCookie", "value": "abc", "domain": "fogis.svenskfotboll.se", "path": "/"}]
        )
    )
    responses.post(
        f"{API}/GetApplicationConfig",
        json={"d": {}},
        match=[matchers.header_matcher({"Cookie": ".MDK.AuthCookie=abc"})],
    )
    FogisSession(cookie_file=jar).call("GetApplicationConfig")


def test_unreadable_cookie_file_is_ignored(tmp_path: Path) -> None:
    jar = tmp_path / "cookies.json"
    jar.write_text("not json")
    assert FogisSession(cookie_file=jar).export_cookies() == []


@responses.activate
def test_business_rule_refusal_is_a_rejected_error_with_fogis_text() -> None:
    from fogis_api_client.errors import FogisRejectedError

    text = "Bortalagets matchtrupp saknar lagkapten."
    responses.post(
        f"{API}/SparaMatchGodkannDomarrapport",
        status=500,
        json={"Message": text, "ExceptionType": "System.ApplicationException", "StackTrace": "…"},
    )
    with pytest.raises(FogisRejectedError) as exc:
        FogisSession().call("SparaMatchGodkannDomarrapport", {"matchid": 1})
    assert exc.value.server_message == text and exc.value.status_code == 500
    assert isinstance(exc.value, FogisAPIRequestError)
