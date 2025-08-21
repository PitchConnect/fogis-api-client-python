"""
Cookie key normalization utilities for the FOGIS API client.

- The FOGIS server uses cookie names with dots:
  * "FogisMobilDomarKlient.ASPXAUTH"
  * "ASP.NET_SessionId"

- The public API exposes normalized cookie names with underscores for
  nicer ergonomics and to avoid dot-in-key issues in some contexts:
  * "FogisMobilDomarKlient_ASPXAUTH"
  * "ASP_NET_SessionId"

This module provides helpers to convert between the two representations.
"""

from __future__ import annotations

from typing import Dict, Mapping

try:
    # Import only for typing; avoid hard dependency at import time
    from fogis_api_client.types import CookieDict  # type: ignore
except Exception:  # pragma: no cover - typing only
    CookieDict = Dict[str, str]  # type: ignore

# Public (normalized) cookie keys
PUBLIC_AUTH = "FogisMobilDomarKlient_ASPXAUTH"
PUBLIC_SESSION = "ASP_NET_SessionId"

# Server cookie keys
SERVER_AUTH = "FogisMobilDomarKlient.ASPXAUTH"
SERVER_SESSION = "ASP.NET_SessionId"


def normalize_public_cookie_keys(cookies: Mapping[str, str]) -> CookieDict:
    """Return cookies using normalized (underscore) keys.

    Accepts a mapping that may contain either server-style dot keys,
    public underscore keys, or both. Preference order:
    - Use underscore key when present
    - Otherwise map from corresponding dot key if present
    Missing keys are omitted.
    """
    result: Dict[str, str] = {}

    # Auth cookie
    if PUBLIC_AUTH in cookies and cookies[PUBLIC_AUTH]:
        result[PUBLIC_AUTH] = cookies[PUBLIC_AUTH]
    elif SERVER_AUTH in cookies and cookies[SERVER_AUTH]:
        result[PUBLIC_AUTH] = cookies[SERVER_AUTH]

    # Session cookie
    if PUBLIC_SESSION in cookies and cookies[PUBLIC_SESSION]:
        result[PUBLIC_SESSION] = cookies[PUBLIC_SESSION]
    elif SERVER_SESSION in cookies and cookies[SERVER_SESSION]:
        result[PUBLIC_SESSION] = cookies[SERVER_SESSION]

    return result  # type: ignore[return-value]


def to_server_cookie_keys(cookies: Mapping[str, str]) -> Dict[str, str]:
    """Return a dict containing server-style cookie names with dots.

    Accepts a mapping that may contain either underscore or dot names and
    emits only dot-named keys when values are available.
    """
    result: Dict[str, str] = {}

    # Auth cookie
    if PUBLIC_AUTH in cookies and cookies[PUBLIC_AUTH]:
        result[SERVER_AUTH] = cookies[PUBLIC_AUTH]
    elif SERVER_AUTH in cookies and cookies[SERVER_AUTH]:
        result[SERVER_AUTH] = cookies[SERVER_AUTH]

    # Session cookie
    if PUBLIC_SESSION in cookies and cookies[PUBLIC_SESSION]:
        result[SERVER_SESSION] = cookies[PUBLIC_SESSION]
    elif SERVER_SESSION in cookies and cookies[SERVER_SESSION]:
        result[SERVER_SESSION] = cookies[SERVER_SESSION]

    return result
