"""Typed views of FOGIS read responses (FOGIS_API.md §3, §6-8).

Every model is built with `from_api()` from one record as FOGIS returns it, and keeps that record in `raw`,
so fields not modelled here are never lost. FOGIS uses sentinels instead of null: 0 for a missing id, -1 for a
missing number or position, and double.MinValue for a missing coordinate. Those become None.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from .enums import AssignmentStatus, EventType, FootballType, ResultType

STOCKHOLM = ZoneInfo("Europe/Stockholm")
PROTECTED_NAME = "Personuppgifter Skyddade"

Raw = Mapping[str, Any]

_MS_DATE = re.compile(r"^/Date\((-?\d+)\)/$")


def parse_ms_date(value: str | None) -> datetime | None:
    """'/Date(1682069400000)/' -> aware datetime in Swedish time. None/empty/unparseable -> None."""
    if not value:
        return None
    m = _MS_DATE.match(value)
    if m is None:
        return None
    return datetime.fromtimestamp(int(m.group(1)) / 1000, tz=STOCKHOLM)


def _id(value: Any) -> int | None:
    return value if isinstance(value, int) and value > 0 else None


def _num(value: Any) -> int | None:
    return value if isinstance(value, int) and value >= 0 else None


def _coord(value: Any) -> float | None:
    return float(value) if isinstance(value, int | float) and abs(value) <= 180 else None


def _enum[E: (EventType, ResultType, FootballType, AssignmentStatus)](cls: type[E], value: Any) -> E | None:
    try:
        return cls(value)
    except ValueError:
        return None


def _name(value: str | None) -> str | None:
    """Protected identities and empty names become None; see is_protected on the models that have names."""
    return None if not value or value == PROTECTED_NAME else value


# ---------------------------------------------------------------------------- match list


@dataclass(frozen=True, slots=True)
class MatchTeam:
    match_team_id: int  # matchlagid: this team *in this match*; key for line-ups and officials
    team_id: int
    club_id: int | None
    engagement_id: int  # lagengagemangid: the team's entry in the competition
    name: str


@dataclass(frozen=True, slots=True)
class Assignment:
    """One referee's assignment to a match (domaruppdraglista)."""

    assignment_id: int
    role_id: int
    role_name: str
    role_short: str
    referee_id: int
    person_id: int | None
    status_id: int
    status: AssignmentStatus | None
    name: str | None  # None for protected identities
    is_protected: bool
    raw: Raw = field(repr=False, compare=False)

    @classmethod
    def from_api(cls, d: Raw) -> Assignment:
        return cls(
            assignment_id=d["domaruppdragid"],
            role_id=d["domarrollid"],
            role_name=d.get("domarrollnamn", ""),
            role_short=d.get("domarrollkortnamn", ""),
            referee_id=d["domareid"],
            person_id=_id(d.get("personid")),
            status_id=d.get("domaruppdragstatusid", 0),
            status=_enum(AssignmentStatus, d.get("domaruppdragstatusid")),
            name=_name(d.get("personnamn")),
            is_protected=d.get("personnamn") == PROTECTED_NAME,
            raw=d,
        )


@dataclass(frozen=True, slots=True)
class Match:
    """One entry of GetMatcherAttRapportera's matchlista (also hamtaTidigareMatcherForLag)."""

    match_id: int
    match_number: str
    football_type: FootballType | None
    home: MatchTeam
    away: MatchTeam
    kickoff: datetime | None
    date: date | None
    competition_id: int
    competition_name: str
    venue_name: str
    venue_latitude: float | None
    venue_longitude: float | None
    home_goals: int
    away_goals: int
    result_is_final: bool
    postponed: bool
    abandoned: bool
    cancelled: bool
    report_approved: bool
    report_approved_at: datetime | None
    halves: int
    half_length: int
    extra_periods: int
    extra_period_length: int
    high_resolution_time: bool  # tavlinganvanderhogupplosttid: minutes may be entered as mm:ss
    crew: tuple[Assignment, ...]
    raw: Raw = field(repr=False, compare=False)

    @classmethod
    def from_api(cls, d: Raw) -> Match:
        return cls(
            match_id=d["matchid"],
            match_number=d.get("matchnr", ""),
            football_type=_enum(FootballType, d.get("fotbollstypid")),
            home=_team(d, 1),
            away=_team(d, 2),
            kickoff=parse_ms_date(d.get("tid")),
            date=date.fromisoformat(d["speldatum"]) if d.get("speldatum") else None,
            competition_id=d.get("tavlingid", 0),
            competition_name=d.get("tavlingnamn", ""),
            venue_name=d.get("anlaggningnamn", ""),
            venue_latitude=_coord(d.get("anlaggningLatitud")),
            venue_longitude=_coord(d.get("anlaggningLongitud")),
            home_goals=d.get("matchlag1mal", 0),
            away_goals=d.get("matchlag2mal", 0),
            result_is_final=bool(d.get("arslutresultat")),
            postponed=bool(d.get("uppskjuten")),
            abandoned=bool(d.get("avbruten")),
            cancelled=bool(d.get("installd")),
            report_approved=bool(d.get("matchrapportgodkandavdomare")),
            report_approved_at=parse_ms_date(d.get("matchrapportgodkandavdomaredatum")),
            halves=d.get("antalhalvlekar", 2),
            half_length=d.get("tidperhalvlek", 0),
            extra_periods=d.get("antalforlangningsperioder", 0),
            extra_period_length=d.get("tidperforlangningsperiod", 0),
            high_resolution_time=bool(d.get("tavlinganvanderhogupplosttid")),
            crew=tuple(Assignment.from_api(a) for a in d.get("domaruppdraglista") or ()),
            raw=d,
        )

    @property
    def shootout_period(self) -> int:
        """Period number FOGIS uses for the penalty shoot-out (FOGIS_API.md §6)."""
        return self.halves + self.extra_periods + 1


def _team(d: Raw, n: int) -> MatchTeam:
    return MatchTeam(
        match_team_id=d[f"matchlag{n}id"],
        team_id=d.get(f"lag{n}lagid", 0),
        club_id=_id(d.get(f"lag{n}foreningid")),
        engagement_id=d.get(f"lag{n}lagengagemangid", 0),
        name=d.get(f"lag{n}namn", ""),
    )


# ---------------------------------------------------------------------------- events


@dataclass(frozen=True, slots=True)
class MatchEvent:
    """One row of GetMatchhandelselista, as stored. See the timeline helpers for interpretation."""

    event_id: int
    match_id: int
    type_id: int
    type: EventType | None  # None for a type id this library doesn't know
    type_name: str
    match_team_id: int | None
    team_name: str
    player_id: int | None
    participant_id: int | None  # matchdeltagareid: links to the line-up row
    shirt_number: int | None
    player_name: str | None
    minute: int  # base minute; added time is only in time_text ("90+5" -> minute 90)
    time_text: str  # tidsangivelse as FOGIS renders it
    period: int  # 0 = unknown (see FOGIS_API.md §6)
    home_goals: int  # score typed by the reporter on goals; 0-0 on everything else; never validated
    away_goals: int
    related_event_id: int | None  # e.g. BYTE_IN -> its BYTE_UT (only since ~2024)
    position_x: int | None
    position_y: int | None
    comment: str
    raw: Raw = field(repr=False, compare=False)

    @classmethod
    def from_api(cls, d: Raw) -> MatchEvent:
        return cls(
            event_id=d["matchhandelseid"],
            match_id=d["matchid"],
            type_id=d["matchhandelsetypid"],
            type=_enum(EventType, d["matchhandelsetypid"]),
            type_name=d.get("matchhandelsetypnamn", ""),
            match_team_id=_id(d.get("matchlagid")),
            team_name=d.get("matchlagnamn", ""),
            player_id=_id(d.get("spelareid")),
            participant_id=_id(d.get("matchdeltagareid")),
            shirt_number=_num(d.get("trojnummer")),
            player_name=_name(d.get("spelarenamn")),
            minute=d.get("matchminut", 0),
            time_text=d.get("tidsangivelse", ""),
            period=d.get("period", 0),
            home_goals=d.get("hemmamal", 0),
            away_goals=d.get("bortamal", 0),
            related_event_id=_id(d.get("relateradTillMatchhandelseID")),
            position_x=_num(d.get("planpositionx")),
            position_y=_num(d.get("planpositiony")),
            comment=d.get("kommentar", ""),
            raw=d,
        )

    @property
    def added_minutes(self) -> int | None:
        """The '+N' of added time, parsed from time_text ('90+5' -> 5), else None."""
        base, plus, extra = self.time_text.partition("+")
        return int(extra) if plus and base.strip().isdigit() and extra.strip().isdigit() else None


# ---------------------------------------------------------------------------- line-ups and officials


@dataclass(frozen=True, slots=True)
class LineupEntry:
    """One row of GetMatchdeltagareListaForMatchlag."""

    participant_id: int  # matchdeltagareid
    match_id: int
    match_team_id: int
    player_id: int
    shirt_number: int | None
    first_name: str
    last_name: str
    captain: bool
    substitute: bool
    playing_official: bool
    responsible: bool
    sending_off: str  # utvisning: '' or a code such as 'L' / 'M'
    substitution_minutes: tuple[int, ...]  # byte1/byte2 when set
    accumulated_cautions: int
    suspension: str
    raw: Raw = field(repr=False, compare=False)

    @classmethod
    def from_api(cls, d: Raw) -> LineupEntry:
        return cls(
            participant_id=d["matchdeltagareid"],
            match_id=d["matchid"],
            match_team_id=d["matchlagid"],
            player_id=d["spelareid"],
            shirt_number=_num(d.get("trojnummer")),
            first_name=d.get("fornamn", ""),
            last_name=d.get("efternamn", ""),
            captain=bool(d.get("lagkapten")),
            substitute=bool(d.get("ersattare")),
            playing_official=bool(d.get("arSpelandeLedare")),
            responsible=bool(d.get("ansvarig")),
            sending_off=d.get("utvisning", ""),
            substitution_minutes=tuple(m for m in (d.get("byte1", 0), d.get("byte2", 0)) if m),
            accumulated_cautions=d.get("spelareAntalAckumuleradeVarningar", 0),
            suspension=d.get("spelareAvstangningBeskrivning", ""),
            raw=d,
        )


@dataclass(frozen=True, slots=True)
class TeamOfficial:
    """One row of GetMatchlagledareListaForMatchlag, including discipline (FOGIS_API.md §8)."""

    official_id: int  # matchlagledareid; what SparaMatchlagledare takes
    match_id: int
    match_team_id: int
    person_id: int
    first_name: str
    last_name: str
    role_id: int  # lagrollid; must be re-sent unchanged when saving discipline
    role_name: str
    responsible: bool  # ansvarig; must be re-sent unchanged when saving discipline
    cautioned: bool
    caution_minute: int | None
    sent_off_minor: bool  # avvisadlindrig
    sent_off_major: bool  # avvisadgrov
    sending_off_minute: int | None
    accumulated_cautions: int
    suspension: str
    raw: Raw = field(repr=False, compare=False)

    @classmethod
    def from_api(cls, d: Raw) -> TeamOfficial:
        return cls(
            official_id=d["matchlagledareid"],
            match_id=d["matchid"],
            match_team_id=d["matchlagid"],
            person_id=d["personid"],
            first_name=d.get("fornamn", ""),
            last_name=d.get("efternamn", ""),
            role_id=d.get("lagrollid", 0),
            role_name=d.get("lagrollnamn", ""),
            responsible=bool(d.get("ansvarig")),
            cautioned=bool(d.get("varnad")),
            caution_minute=d.get("varnadmatchminut") or None,
            sent_off_minor=bool(d.get("avvisadlindrig")),
            sent_off_major=bool(d.get("avvisadgrov")),
            sending_off_minute=d.get("avvisadmatchminut") or None,
            accumulated_cautions=d.get("ledareAntalAckumuleradeVarningar", 0),
            suspension=d.get("ledareAvstangningBeskrivning", ""),
            raw=d,
        )

    @property
    def sent_off(self) -> bool:
        return self.sent_off_minor or self.sent_off_major


# ---------------------------------------------------------------------------- results and change log


@dataclass(frozen=True, slots=True)
class MatchResult:
    """One row of GetMatchresultatlista (one row per result type)."""

    result_id: int
    match_id: int
    type_id: int
    type: ResultType | None
    type_name: str
    home_goals: int
    away_goals: int
    walkover: bool
    ow: bool
    ww: bool
    raw: Raw = field(repr=False, compare=False)

    @classmethod
    def from_api(cls, d: Raw) -> MatchResult:
        return cls(
            result_id=d["matchresultatid"],
            match_id=d["matchid"],
            type_id=d["matchresultattypid"],
            type=_enum(ResultType, d["matchresultattypid"]),
            type_name=d.get("matchresultattypnamn", ""),
            home_goals=d.get("matchlag1mal", 0),
            away_goals=d.get("matchlag2mal", 0),
            walkover=bool(d.get("wo")),
            ow=bool(d.get("ow")),
            ww=bool(d.get("ww")),
            raw=d,
        )


@dataclass(frozen=True, slots=True)
class LineupChange:
    """One row of GetMatchdeltagareAndringForMatch."""

    match_team_id: int
    at: time | None  # tidpunkt is only "HH:MM", without a date
    description: str
    changed_by: str
    changed_by_own_club: bool
    raw: Raw = field(repr=False, compare=False)

    @classmethod
    def from_api(cls, d: Raw) -> LineupChange:
        return cls(
            match_team_id=d["matchlagid"],
            at=_clock(d.get("tidpunkt")),
            description=d.get("beskrivning", ""),
            changed_by=d.get("andradav", ""),
            changed_by_own_club=bool(d.get("andradavegenforening")),
            raw=d,
        )


def _clock(value: str | None) -> time | None:
    try:
        return time.fromisoformat(value) if value else None
    except ValueError:
        return None


_CAUTION_LABEL = re.compile(r"^Varning i match (?P<nr>\S+?),.*,\s*(?P<date>\d{4}-\d{2}-\d{2})\s*$")


@dataclass(frozen=True, slots=True)
class CautionRecord:
    """One caution in a competition (a row of SokVarningarForSpelareITavling / SokVarningarForLedareITavling).

    FOGIS returns only a text label and an annulled flag; match number and date are parsed from the label.
    """

    annulled: bool
    label: str  # "Varning i match <matchnr>, <home> - <away>, <YYYY-MM-DD>"
    match_number: str | None
    date: date | None
    raw: Raw = field(repr=False, compare=False)

    @classmethod
    def from_api(cls, d: Raw) -> CautionRecord:
        label = d.get("label", "")
        m = _CAUTION_LABEL.match(label)
        return cls(
            annulled=bool(d.get("arannullerad")),
            label=label,
            match_number=m.group("nr") if m else None,
            date=date.fromisoformat(m.group("date")) if m else None,
            raw=d,
        )
