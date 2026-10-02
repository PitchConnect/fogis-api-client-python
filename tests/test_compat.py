"""The 0.x surface fogis_friend relies on (REWRITE_PLAN.md, "Compatibility surface")."""

from datetime import date, timedelta

import pytest
from test_client import FakeSession, match_record

import fogis_api_client
from fogis_api_client import (
    FogisApiClient,
    FogisAPIRequestError,
    FogisAuthServiceUnavailableError,
    FogisInvalidCredentialsError,
    FogisLoginError,
)


def compat_client(session: FakeSession) -> FogisApiClient:
    c = FogisApiClient(username="u", password="p")
    c.session = session  # type: ignore[assignment]
    return c


def test_fogis_friend_imports_exist() -> None:
    for name in (
        "FogisApiClient",
        "FogisLoginError",
        "FogisInvalidCredentialsError",
        "FogisAuthServiceUnavailableError",
    ):
        assert hasattr(fogis_api_client, name)
    assert issubclass(FogisInvalidCredentialsError, FogisLoginError)
    assert issubclass(FogisAuthServiceUnavailableError, FogisLoginError)
    assert FogisLoginError("boom").message == "boom"


def test_constructor_needs_credentials_or_cookies() -> None:
    with pytest.raises(ValueError):
        FogisApiClient()
    with pytest.raises(TypeError):
        FogisApiClient(cookies={"a": "b"}, oauth_tokens={"access_token": "x"})
    c = FogisApiClient(cookies={".MDK.AuthCookie": "abc"})
    assert c.get_cookies() == {".MDK.AuthCookie": "abc"}


def test_fetch_matches_list_json_default_window_and_raw_dicts() -> None:
    today = date.today()
    session = FakeSession(
        [
            match_record(1, today - timedelta(days=8)),
            match_record(2, today - timedelta(days=7)),
            match_record(3, today + timedelta(days=365)),
            match_record(4, today + timedelta(days=366)),
        ]
    )
    got = compat_client(session).fetch_matches_list_json()
    assert [m["matchid"] for m in got] == [2, 3]
    assert all(isinstance(m, dict) for m in got)
    assert all(c[1]["filter"]["status"] == [] for c in session.calls)


def test_fetch_matches_list_json_honours_0x_filter_keys() -> None:
    session = FakeSession([match_record(1, date(2024, 5, 1))])
    got = compat_client(session).fetch_matches_list_json(
        {"datumFran": "2024-01-01", "datumTill": "2024-12-31", "status": ["installd"], "kon": [3]}
    )
    assert [m["matchid"] for m in got] == [1]
    f = session.calls[0][1]["filter"]
    assert (f["datumFran"], f["datumTill"], f["status"], f["kon"]) == (
        "2024-01-01",
        "2024-12-31",
        ["installd"],
        [3],
    )


def test_fetch_match_json_is_deprecated_but_works() -> None:
    session = FakeSession([match_record(5, date.today())])
    c = compat_client(session)
    with pytest.warns(DeprecationWarning):
        assert c.fetch_match_json("5")["matchid"] == 5
    with pytest.warns(DeprecationWarning), pytest.raises(FogisAPIRequestError):
        c.fetch_match_json(6)


def test_removed_0x_methods_point_to_their_replacement() -> None:
    c = FogisApiClient(username="u", password="p")
    with pytest.raises(AttributeError, match=r"events\(match_id\).*MIGRATION"):
        c.fetch_match_events_json(1)  # type: ignore[attr-defined]
    with pytest.raises(AttributeError, match="has no attribute"):
        c.no_such_thing  # type: ignore[attr-defined]  # noqa: B018


@pytest.mark.parametrize(
    ("method", "args"),
    [
        ("save_match_event", ({"matchid": 1, "matchhandelsetypid": 6},)),
        ("report_match_result", ({"matchid": 1, "hemmamal": 2, "bortamal": 1},)),
        ("save_match_participant", ({"matchdeltagareid": 1},)),
        ("mark_reporting_finished", (123456,)),
    ],
)
def test_0x_style_write_calls_get_a_migration_hint(method: str, args: tuple) -> None:  # type: ignore[type-arg]
    c = FogisApiClient(username="u", password="p")
    kwargs = {"confirm_match_id": 123456} if method == "mark_reporting_finished" else {}
    with pytest.raises(TypeError, match=r"changed in 1\.0"):
        getattr(c, method)(*args, **kwargs)
