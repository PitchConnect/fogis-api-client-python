"""Read-only checks against production FOGIS. Costs one password login.

Run with:  uv run --env-file .env pytest -m live
"""

import os

import pytest

from fogis_api_client.session import AUTH_COOKIE, IDENTITY_COOKIE, FogisSession

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def session() -> FogisSession:
    username, password = os.environ.get("FOGIS_USERNAME"), os.environ.get("FOGIS_PASSWORD")
    if not (username and password):
        pytest.skip("FOGIS_USERNAME / FOGIS_PASSWORD not set")
    s = FogisSession(username, password, min_interval=1.5)
    s.login()
    return s


def test_login_gives_both_cookies(session: FogisSession) -> None:
    assert session.has_cookie(AUTH_COOKIE)
    assert session.has_cookie(IDENTITY_COOKIE)
    assert session.is_valid()


def test_read_call_returns_parsed_d(session: FogisSession) -> None:
    config = session.call("GetApplicationConfig")
    assert isinstance(config, dict)


def test_lost_auth_cookie_is_renewed_without_password(
    session: FogisSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    for c in [c for c in session.http.cookies if c.name == AUTH_COOKIE]:
        session.http.cookies.clear(c.domain, c.path, c.name)
    assert not session.is_valid()

    def no_password_login() -> None:
        raise AssertionError("renewal fell back to a password login")

    monkeypatch.setattr(session, "login", no_password_login)
    assert isinstance(session.call("GetApplicationConfig"), dict)
    assert session.has_cookie(AUTH_COOKIE)
