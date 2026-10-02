"""FOGIS enums, complete, as defined in the referee app's own code (FOGIS_API.md §5).

Member names follow the app's Swedish names so they can be matched against FOGIS without translation.
"""

from enum import IntEnum


class EventType(IntEnum):
    """MatchhandelsetypOption. Values FOGIS may add later are not members; models keep the raw id."""

    # DANGEROUS, never save 1 or 7 (the library refuses): FOGIS stores them as yellow cards that the event
    # list never shows, so they can't be seen or deleted; two trigger an automatic sending-off (2026-09-30).
    VARNING_OJUST_SPEL = 1  # old caution reason ("unsporting behaviour"); use VARNING
    LINDRIG_UTVISNING_AVVISNING = 2  # created by the server on a second caution; never posted by the app
    STRAFFSPARK = (
        3  # "penalty awarded", sent by live-reporting clients before the outcome; not the referee app
    )
    FRISPARK = 4
    HORNA = 5
    SPELMAL = 6  # goal
    VARNING_OLAMPLIGT_UPPTRADANDE = 7  # DANGEROUS, see VARNING_OJUST_SPEL; use VARNING
    MALCHANSUTVISNING = 8  # sending-off for denying a goal-scoring opportunity
    GROV_UTVISNING_AVVISNING = 9  # sending-off, serious offence
    SAKNAR_SPELARLEGITIMATION = 10
    MALGIVANDE_PASSNING = 11  # assist
    SKOTT_UTANFOR_MAL = 12
    SKOTT_PA_MAL = 13
    STRAFFMAL = 14  # penalty goal
    SJALVMAL = 15  # own goal
    BYTE_UT = 16  # substitution: player off
    BYTE_IN = 17  # substitution: player on (linked to its 16 since ~2024)
    STRAFFMISS_UTANFOR = 18
    STRAFFMISS_RADDNING = 19
    VARNING = 20  # caution
    STRAFFAVGORANDE_MAL = 21  # shoot-out goal
    STRAFFAVGORANDE_MISS = 22  # shoot-out miss
    MATCH_SLUT = 23
    OFFSIDE = 24
    SKOTT_I_MALSTALLNING = 25
    STRAFFMISS_I_MALSTALLNING = 26
    MATCHSEKRETERARE_AVSLUTAR_MATCHRAPPORTERING = 27
    HORNMAL = 28  # goal direct from a corner
    FRISPARKSMAL = 29  # goal direct from a free kick
    FRISPARK_ORSAKAD_AV = 30
    HALVLEK_PERIOD_START = 31
    HALVLEK_PERIOD_SLUT = 32
    ANNONSERAD_STOPPTID = 33  # announced added time; never used in history
    STRAFF_ORSAKAD_AV = 34
    STRAFF_SKJUTS_AV = 35
    NICKMAL = 39  # headed goal
    TIO_METER_STRAFF_MAL_FUTSAL = 40
    TIO_METER_STRAFF_MISS_FUTSAL = 41
    TIME_OUT = 42
    JUSTERA_MATCHKLOCKA = 4545

    @property
    def is_goal(self) -> bool:
        """A goal that counts towards the match score (shoot-out goals do not)."""
        return self in _GOALS

    @property
    def is_caution(self) -> bool:
        return self in _CAUTIONS

    @property
    def is_sending_off(self) -> bool:
        return self in _SENDING_OFFS

    @property
    def is_substitution(self) -> bool:
        return self in (EventType.BYTE_UT, EventType.BYTE_IN)

    @property
    def is_shootout(self) -> bool:
        return self in (EventType.STRAFFAVGORANDE_MAL, EventType.STRAFFAVGORANDE_MISS)

    @property
    def is_control(self) -> bool:
        """Clock/period bookkeeping rather than something a player did. Unreliable in history."""
        return self in _CONTROL


_GOALS = frozenset(
    {
        EventType.SPELMAL,
        EventType.STRAFFMAL,
        EventType.SJALVMAL,
        EventType.HORNMAL,
        EventType.FRISPARKSMAL,
        EventType.NICKMAL,
        EventType.TIO_METER_STRAFF_MAL_FUTSAL,
    }
)
_CAUTIONS = frozenset(
    {EventType.VARNING, EventType.VARNING_OJUST_SPEL, EventType.VARNING_OLAMPLIGT_UPPTRADANDE}
)
_SENDING_OFFS = frozenset(
    {EventType.LINDRIG_UTVISNING_AVVISNING, EventType.MALCHANSUTVISNING, EventType.GROV_UTVISNING_AVVISNING}
)
_CONTROL = frozenset(
    {
        EventType.MATCH_SLUT,
        EventType.MATCHSEKRETERARE_AVSLUTAR_MATCHRAPPORTERING,
        EventType.HALVLEK_PERIOD_START,
        EventType.HALVLEK_PERIOD_SLUT,
        EventType.ANNONSERAD_STOPPTID,
        EventType.TIME_OUT,
        EventType.JUSTERA_MATCHKLOCKA,
    }
)


class ResultType(IntEnum):
    """MatchresultattypOption."""

    SLUTRESULTAT = 1
    HALVTIDSRESULTAT = 2
    FULL_TID = 3
    EFTER_FORLANGNING = 4
    EFTER_STRAFFAR = 5


class FootballType(IntEnum):
    """FotbollstypOption."""

    FOTBOLL = 1
    FUTSAL = 2
    BEACH_SOCCER = 3


class AssignmentStatus(IntEnum):
    """DomaruppdragstatusOption: status of a referee's assignment to a match."""

    SKAPAT = 1
    TILLGANGLIGT = 2
    PRELIMINART = 3
    FORESLAGET = 4
    TILLDELAT = 5
    TILLDELAT_INNAN_UPPSKJUTEN = 6
    TILLDELAT_INNAN_AVBRUTEN = 7
    TILLDELAT_INNAN_WO = 8
