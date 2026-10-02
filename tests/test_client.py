from datetime import date, timedelta
from typing import Any

import pytest
from conftest import load

from fogis_api_client.client import MATCH_LIST_CAP, FogisClient
from fogis_api_client.errors import FogisDataError


class FakeSession:
    """Answers GetMatcherAttRapportera like FOGIS: date-filtered, oldest first, truncated to 100."""

    def __init__(
        self, matches: list[dict[str, Any]] | None = None, answers: dict[str, Any] | None = None
    ) -> None:
        self.matches = matches or []
        self.answers = answers or {}
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def call(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        self.calls.append((method, payload or {}))
        if method == "GetMatcherAttRapportera":
            f = payload["filter"] if payload else {}
            hits = [m for m in self.matches if f["datumFran"] <= m["speldatum"] <= f["datumTill"]]
            return {"matchlista": sorted(hits, key=lambda m: m["speldatum"])[:MATCH_LIST_CAP]}
        return self.answers[method]

    def close(self) -> None:
        pass


def match_record(match_id: int, day: date) -> dict[str, Any]:
    template = load("12_match_list", "matches")[0]
    return {**template, "matchid": match_id, "speldatum": day.isoformat()}


def client(session: FakeSession) -> FogisClient:
    return FogisClient(session=session)  # type: ignore[arg-type]


def test_busy_period_is_split_until_nothing_is_truncated() -> None:
    start = date(2023, 1, 1)
    records = [match_record(i, start + timedelta(days=i // 3)) for i in range(3 * 365)]  # 3 matches a day
    session = FakeSession(records)

    got = client(session).matches(start, date(2023, 12, 31))

    assert [m.match_id for m in got] == list(range(3 * 365))
    assert len(session.calls) > 3 * 365 // MATCH_LIST_CAP  # the year had to be split


def test_range_is_fetched_per_calendar_year() -> None:
    session = FakeSession([match_record(1, date(2022, 6, 1)), match_record(2, date(2024, 6, 1))])
    got = client(session).matches(date(2022, 3, 1), date(2024, 2, 1))
    ranges = [(c[1]["filter"]["datumFran"], c[1]["filter"]["datumTill"]) for c in session.calls]
    assert ranges == [
        ("2022-03-01", "2022-12-31"),
        ("2023-01-01", "2023-12-31"),
        ("2024-01-01", "2024-02-01"),
    ]
    assert [m.match_id for m in got] == [1]


def test_filter_uses_fixed_dates_and_exclusion_statuses() -> None:
    session = FakeSession()
    client(session).matches(date(2026, 1, 1), date(2026, 1, 2), exclude_statuses=["installd"])
    f = session.calls[0][1]["filter"]
    assert f["datumTyp"] == 1
    assert f["status"] == ["installd"]
    assert f["alderskategori"] == [1, 2, 3, 4, 5] and f["kon"] == [2, 3, 4]


def test_end_before_start_is_rejected() -> None:
    with pytest.raises(ValueError):
        client(FakeSession()).matches(date(2026, 2, 1), date(2026, 1, 1))


def test_match_scans_the_list() -> None:
    today = date.today()
    session = FakeSession([match_record(7, today), match_record(8, today)])
    found = client(session).match(8)
    assert found is not None and found.match_id == 8
    assert client(session).match(9) is None


def test_per_match_reads_send_the_app_payloads_and_return_models() -> None:
    events = load("01_modern_linked_subs", "events")
    lineup = load("01_modern_linked_subs", "lineups")
    officials = load("01_modern_linked_subs", "officials")
    session = FakeSession(
        answers={
            "GetMatchhandelselista": events,
            "GetMatchdeltagareListaForMatchlag": lineup,
            "GetMatchlagledareListaForMatchlag": officials,
            "GetMatchresultatlista": [],
            "GetMatchdeltagareAndringForMatch": [],
            "hamtaTidigareMatcherForLag": load("12_match_list", "matches"),
            "SokVarningarForSpelareITavling": [
                {"arannullerad": False, "label": "Varning i match 1, A - B, 2026-05-01"}
            ],
            "SokVarningarForLedareITavling": [],
        }
    )
    c = client(session)
    assert len(c.events(1)) == len(events)
    assert len(c.lineup(2)) == len(lineup)
    assert len(c.officials(2)) == len(officials)
    assert c.results(1) == [] and c.lineup_changes(1) == []
    assert len(c.earlier_matches(3, 4)) == 5
    assert c.player_cautions(5, 4)[0].match_number == "1"
    assert c.official_cautions(6, 4) == []
    assert session.calls == [
        ("GetMatchhandelselista", {"matchid": 1}),
        ("GetMatchdeltagareListaForMatchlag", {"matchlagid": 2}),
        ("GetMatchlagledareListaForMatchlag", {"matchlagid": 2}),
        ("GetMatchresultatlista", {"matchid": 1}),
        ("GetMatchdeltagareAndringForMatch", {"matchid": 1}),
        ("hamtaTidigareMatcherForLag", {"tavlingsId": 3, "lagengagemangId": 4}),
        ("SokVarningarForSpelareITavling", {"spelareId": 5, "lagengagemangId": 4}),
        ("SokVarningarForLedareITavling", {"personId": 6, "lagengagemangId": 4}),
    ]


def test_unexpected_shape_is_a_data_error() -> None:
    with pytest.raises(FogisDataError):
        client(FakeSession(answers={"GetMatchhandelselista": {"oops": 1}})).events(1)
