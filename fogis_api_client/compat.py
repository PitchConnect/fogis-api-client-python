"""The 0.x `FogisApiClient` surface, kept for existing users (REWRITE_PLAN.md, "Compatibility surface").

Only what known consumers use is kept: the constructor, login(), get_cookies(), fetch_matches_list_json(),
get_match_details() and the deprecated fetch_match_json(). New code should use FogisClient.
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any

from .client import ALL_AGE_CATEGORIES, ALL_GENDERS, FogisClient
from .errors import FogisAPIRequestError
from .session import FogisSession

_COOKIE_DOMAIN = "fogis.svenskfotboll.se"

# 0.x methods that are gone, with what replaces them (docs/MIGRATION.md has the full table).
_REMOVED_0X = {
    "fetch_match_events_json": "events(match_id)",
    "fetch_match_result_json": "results(match_id)",
    "fetch_team_players_json": "lineup(match_team_id)",
    "fetch_team_officials_json": "officials(match_team_id)",
    "get_match_players": "lineup() for match.home and match.away",
    "fetch_match_players_json": "lineup() for match.home and match.away",
    "get_match_officials": "officials() per team and match.crew",
    "fetch_match_officials_json": "officials() per team and match.crew",
    "fetch_complete_match": "match(), events(), lineup(), officials(), results()",
    "get_match_summary": "match(), events(), lineup(), officials(), results()",
    "get_recent_matches": "matches(start, end)",
    "find_matches": "matches(start, end) and filter the models",
    "get_matches_requiring_action": "matches(start, end) and filter the models",
    "get_match_events_by_type": "events() filtered by EventType",
    "get_team_statistics": "events() and fogis_api_client.timeline",
    "save_team_official": "save_official_discipline(official, ...) / clear_official_discipline(official)",
    "clear_match_events": "delete_match_event(event_id) per event (FOGIS has no clear method)",
    "refresh_authentication": "session.renew() (renewal is automatic)",
    "is_authenticated": "session.is_valid()",
    "validate_cookies": "session.is_valid()",
    "get_authentication_info": "get_cookies() / session.export_cookies()",
    "hello_world": "nothing",
}


def _reject_dict(method: str, args: tuple[Any, ...], new_form: str) -> None:
    if args and isinstance(args[0], Mapping):
        raise TypeError(f"{method}() changed in 1.0: use {new_form} (see docs/MIGRATION.md)")


class FogisApiClient(FogisClient):
    """Drop-in replacement for the 0.x client. Returns raw FOGIS dicts, as 0.x did."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        cookies: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        if kwargs.pop("oauth_tokens", None) is not None:
            raise TypeError("oauth_tokens is no longer supported: FOGIS sessions are cookie-only")
        if not (username and password) and not cookies:
            raise ValueError("Either username and password OR cookies must be provided")
        super().__init__(session=FogisSession(username, password, **kwargs))
        self.username = username
        for name, value in (cookies or {}).items():
            self.session.http.cookies.set(name, value, domain=_COOKIE_DOMAIN, path="/")

    def __getattr__(self, name: str) -> Any:
        if name in _REMOVED_0X:
            raise AttributeError(
                f"{name}() was removed in 1.0; use {_REMOVED_0X[name]} (see docs/MIGRATION.md)"
            )
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    # 0.x wrote with one dict; Python would complain about missing arguments before 1.0 could explain.
    def save_match_event(self, *args: Any, **kwargs: Any) -> Any:
        _reject_dict(
            "save_match_event", args, "save_match_event(match, event_type, time, team_id=..., player=...)"
        )
        return super().save_match_event(*args, **kwargs)

    def report_match_result(self, *args: Any, **kwargs: Any) -> Any:
        _reject_dict(
            "report_match_result", args, "report_match_result(match_id, {ResultType.SLUTRESULTAT: (h, a)})"
        )
        return super().report_match_result(*args, **kwargs)

    def login(self) -> dict[str, str]:
        """Log in now instead of on the first call. Returns the session cookies, as 0.x did."""
        self.session.login()
        return self.get_cookies()

    def get_cookies(self) -> dict[str, str]:
        return {c.name: c.value for c in self.session.http.cookies if c.value is not None}

    def fetch_matches_list_json(self, filter_params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        """The referee's matches as raw dicts. Default range: a week ago to a year ahead, all statuses.

        filter_params keys as in 0.x: datumFran, datumTill ('YYYY-MM-DD'), status (EXCLUDED statuses),
        alderskategori, kon. Unlike 0.x, ranges with more than 100 matches are returned in full.
        """
        f = dict(filter_params or {})
        today = date.today()
        start = date.fromisoformat(f["datumFran"]) if f.get("datumFran") else today - timedelta(days=7)
        end = date.fromisoformat(f["datumTill"]) if f.get("datumTill") else today + timedelta(days=365)
        return self.matches_raw(
            start,
            end,
            exclude_statuses=f.get("status") or (),
            age_categories=f.get("alderskategori") or ALL_AGE_CATEGORIES,
            genders=f.get("kon") or ALL_GENDERS,
        )

    def get_match_details(
        self, match_id: int | str, filter_params: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        """One match from the match list (FOGIS has no single-match method)."""
        wanted = int(match_id)
        for record in self.fetch_matches_list_json(filter_params):
            if record.get("matchid") == wanted:
                return record
        raise FogisAPIRequestError(f"Match with ID {match_id} not found in match list")

    def fetch_match_json(self, match_id: int | str) -> dict[str, Any]:
        """Deprecated: fetches the whole match list on every call. Look the match up in a list you have."""
        warnings.warn(
            "fetch_match_json() fetches the whole match list per call; look the match up in "
            "fetch_matches_list_json() instead, or use FogisClient.matches()",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_match_details(match_id)
