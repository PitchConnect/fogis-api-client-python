"""Transport and session handling for the mobile referee client's API (FOGIS_API.md §1-2).

A FOGIS session is nothing but cookies:

- `.MDK.AuthCookie` (fogis.svenskfotboll.se) authorizes API calls. The server re-issues it roughly hourly
  while the session is used, so the jar must be kept up to date.
- `.AspNetCore.Identity.Application` (auth.fogis.se, persistent for 14 days with RememberMe) lets us get a
  new `.MDK.AuthCookie` without a password.

An expired or missing session shows up as a 302 to auth.fogis.se, never as a 401. We therefore never follow
redirects on API calls: on a 302 we renew the session (silently if possible, with the password only as a
last resort) and retry the call once.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections.abc import Iterable, Mapping
from http.cookiejar import Cookie
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests

from ._login_form import find_login_form
from .errors import (
    FogisAPIRequestError,
    FogisAuthServiceUnavailableError,
    FogisDataError,
    FogisInvalidCredentialsError,
    FogisLoginError,
    FogisRejectedError,
    FogisSessionExpiredError,
)

log = logging.getLogger(__name__)

ORIGIN = "https://fogis.svenskfotboll.se"
BASE_URL = f"{ORIGIN}/mdk"
LOGIN_URL = f"{BASE_URL}/Login.aspx?ReturnUrl=%2Fmdk%2F"
AUTH_COOKIE = ".MDK.AuthCookie"
IDENTITY_COOKIE = ".AspNetCore.Identity.Application"

DEFAULT_TIMEOUT = (10.0, 30.0)  # (connect, read) seconds

_API_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": ORIGIN,
    "Referer": f"{BASE_URL}/",
}


class FogisSession:
    """An authenticated connection to FOGIS.

    Args:
        username, password: FOGIS credentials. Optional if a still-valid cookie jar is supplied; without a
            password an expired session raises FogisSessionExpiredError instead of logging in.
        cookie_file: Where to keep the cookie jar between runs (JSON, mode 0600). Loaded if it exists and
            written whenever FOGIS sets new cookies. Keeping it makes password logins rare.
        timeout: (connect, read) timeout in seconds for every request.
        min_interval: Minimum seconds between requests (0 = no throttling).
        http: A requests.Session to use instead of a new one (e.g. for custom adapters).
    """

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        *,
        cookie_file: str | os.PathLike[str] | None = None,
        timeout: float | tuple[float, float] = DEFAULT_TIMEOUT,
        min_interval: float = 0.0,
        http: requests.Session | None = None,
    ) -> None:
        self._username = username
        self._password = password
        self._cookie_file = Path(cookie_file).expanduser() if cookie_file is not None else None
        self._timeout = timeout
        self._min_interval = min_interval
        self._last_request = 0.0
        self._renew_lock = threading.Lock()
        self.http = http or requests.Session()
        self.http.headers.setdefault("Accept-Language", "sv-SE,sv;q=0.9,en;q=0.8")
        if self._cookie_file is not None and self._cookie_file.exists():
            self.load_cookies(self._cookie_file)

    # ------------------------------------------------------------------ API calls

    def call(self, method: str, payload: Mapping[str, Any] | None = None) -> Any:
        """POST to MatchWebMetoder.aspx/<method> and return the unwrapped `d` value.

        Renews the session once if it has expired.
        """
        url = f"{BASE_URL}/MatchWebMetoder.aspx/{method}"
        body = dict(payload or {})
        response = self._post_api(url, body)
        if response.is_redirect:
            log.info("FOGIS session expired (302 on %s); renewing", method)
            self.renew()
            response = self._post_api(url, body)
            if response.is_redirect:
                raise FogisSessionExpiredError(
                    f"{method}: still redirected to login after renewing the session"
                )
        return _unwrap(method, response)

    def is_valid(self) -> bool:
        """True if the current cookies are accepted by FOGIS (one small request, never logs in)."""
        response = self._post_api(f"{BASE_URL}/MatchWebMetoder.aspx/GetApplicationConfig", {})
        return response.status_code == 200 and not response.is_redirect

    def _post_api(self, url: str, body: dict[str, Any]) -> requests.Response:
        try:
            response = self._request("POST", url, json=body, headers=_API_HEADERS, allow_redirects=False)
        except requests.RequestException as e:
            raise FogisAPIRequestError(f"Request to {url} failed: {e}") from e
        self._save_if_changed(response)
        return response

    # ------------------------------------------------------------------ session renewal

    def renew(self) -> None:
        """Get a fresh `.MDK.AuthCookie`: silently via the identity cookie, else with the password."""
        with self._renew_lock:
            if self.has_cookie(IDENTITY_COOKIE) and self._silent_reauth():
                log.info("FOGIS session renewed without password")
                return
            self.login()

    def _silent_reauth(self) -> bool:
        try:
            response = self._request("GET", f"{BASE_URL}/", allow_redirects=True)
        except requests.RequestException as e:
            log.warning("Silent re-authentication failed: %s", e)
            return False
        ok = _landed_in_mdk(response)
        if ok:
            self._save()
        return ok

    def login(self) -> None:
        """Log in with username and password (RememberMe=true, so later renewals need no password)."""
        if not (self._username and self._password):
            raise FogisSessionExpiredError("FOGIS session expired and no username/password was given")
        try:
            page = self._request("GET", LOGIN_URL, allow_redirects=True)
            _raise_for_auth_status(page)
            if _landed_in_mdk(page):  # the identity cookie was still good after all
                self._save()
                return
            form = find_login_form(page.text)
            if form is None:
                raise FogisLoginError(f"No login form found at {page.url}")
            fields = {
                **form.fields,
                "Username": self._username,
                "Password": self._password,
                "RememberMe": "true",
            }
            result = self._request("POST", urljoin(page.url, form.action), data=fields, allow_redirects=True)
            _raise_for_auth_status(result)
        except requests.RequestException as e:
            raise FogisAuthServiceUnavailableError(f"Could not reach the FOGIS login service: {e}") from e

        if _landed_in_mdk(result):
            log.info("Logged in to FOGIS")
            self._save()
            return
        # [unverified] A rejected password is assumed to re-render the login form (FOGIS_API.md §10, item 11).
        if find_login_form(result.text) is not None:
            raise FogisInvalidCredentialsError("FOGIS rejected the username or password")
        raise FogisLoginError(f"Login did not end in the referee client (ended at {result.url})")

    # ------------------------------------------------------------------ cookies

    def has_cookie(self, name: str) -> bool:
        return any(c.name == name for c in self.http.cookies)

    def export_cookies(self) -> list[dict[str, Any]]:
        """The cookie jar as JSON-serializable dicts (see load_cookies)."""
        return [
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
                "expires": c.expires,
                "secure": c.secure,
            }
            for c in self.http.cookies
        ]

    def import_cookies(self, cookies: Iterable[Mapping[str, Any]]) -> None:
        for c in cookies:
            self.http.cookies.set_cookie(_make_cookie(c))

    def load_cookies(self, path: str | os.PathLike[str]) -> None:
        try:
            self.import_cookies(json.loads(Path(path).read_text(encoding="utf-8")))
        except (OSError, ValueError, KeyError, TypeError) as e:
            log.warning("Ignoring unreadable cookie file %s: %s", path, e)

    def save_cookies(self, path: str | os.PathLike[str]) -> None:
        path = Path(path)
        tmp = path.with_name(path.name + ".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.export_cookies(), f)
        os.replace(tmp, path)

    def _save(self) -> None:
        if self._cookie_file is not None:
            self.save_cookies(self._cookie_file)

    def _save_if_changed(self, response: requests.Response) -> None:
        if response.cookies:
            self._save()

    # ------------------------------------------------------------------ plumbing

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        if self._min_interval:
            wait = self._last_request + self._min_interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()
        kwargs.setdefault("timeout", self._timeout)
        return self.http.request(method, url, **kwargs)

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> FogisSession:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _landed_in_mdk(response: requests.Response) -> bool:
    return response.status_code == 200 and response.url.startswith(f"{BASE_URL}/")


def _raise_for_auth_status(response: requests.Response) -> None:
    if response.status_code >= 500:
        raise FogisAuthServiceUnavailableError(f"FOGIS login service answered {response.status_code}")


def _unwrap(method: str, response: requests.Response) -> Any:
    if response.status_code != 200:
        message, exception_type = _server_error(response)
        cls = FogisRejectedError if exception_type == "System.ApplicationException" else FogisAPIRequestError
        detail = f": {message}" if message else ""
        raise cls(
            f"{method}: HTTP {response.status_code}{detail}",
            status_code=response.status_code,
            server_message=message,
        )
    try:
        body = response.json()
    except ValueError as e:
        ctype = response.headers.get("Content-Type", "")
        raise FogisDataError(f"{method}: expected JSON, got {ctype or 'no content type'}") from e
    if not isinstance(body, dict) or "d" not in body:
        raise FogisDataError(f"{method}: response has no 'd' member")
    return body["d"]


def _server_error(response: requests.Response) -> tuple[str | None, str | None]:
    """ASP.NET page methods report exceptions as JSON {Message, ExceptionType, StackTrace}."""
    try:
        body = response.json()
    except ValueError:
        return None, None
    if not isinstance(body, dict):
        return None, None
    return body.get("Message") or None, body.get("ExceptionType") or None


def _make_cookie(c: Mapping[str, Any]) -> Cookie:
    domain = str(c["domain"])
    return Cookie(
        version=0,
        name=str(c["name"]),
        value=str(c["value"]),
        port=None,
        port_specified=False,
        domain=domain,
        domain_specified=domain.startswith("."),
        domain_initial_dot=domain.startswith("."),
        path=str(c.get("path") or "/"),
        path_specified=True,
        secure=bool(c.get("secure", True)),
        expires=int(c["expires"]) if c.get("expires") is not None else None,
        discard=c.get("expires") is None,
        comment=None,
        comment_url=None,
        rest={},
    )
