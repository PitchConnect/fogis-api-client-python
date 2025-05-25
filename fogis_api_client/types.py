"""
Type definitions for FOGIS API client.

This module contains TypedDict classes and other type definitions used throughout the API client.
"""
from typing import List, Optional, TypedDict


class MatchDict(TypedDict, total=False):
    """Type definition for a match object returned by the API."""

    matchid: int
    matchnr: str
    datum: str
    tid: str
    hemmalag: str
    bortalag: str
    hemmalagid: int
    bortalagid: int
    arena: str
    status: str
    domare: str
    ad1: str
    ad2: str
    fjarde: str
    matchtyp: str
    tavling: str
    grupp: str
    hemmamal: Optional[int]
    bortamal: Optional[int]
    publik: Optional[int]
    notering: Optional[str]
    rapportstatus: str
    matchstart: Optional[str]
    halvtidHemmamal: Optional[int]
    halvtidBortamal: Optional[int]


class MatchListResponse(TypedDict):
    """Type definition for the response from the match list endpoint."""

    matcher: List[MatchDict]


class PlayerDict(TypedDict, total=False):
    """Type definition for a player object returned by the API."""

    personid: int
    fornamn: str
    efternamn: str
    smeknamn: Optional[str]
    tshirt: Optional[str]
    position: Optional[str]
    positionid: Optional[int]
    lagkapten: Optional[bool]
    spelareid: Optional[int]
    licensnr: Optional[str]


class TeamPlayersResponse(TypedDict):
    """Type definition for the response from the team players endpoint."""

    spelare: List[PlayerDict]


class OfficialDict(TypedDict, total=False):
    """Type definition for an official object returned by the API."""

    personid: int
    fornamn: str
    efternamn: str
    roll: str
    rollid: int


class EventDict(TypedDict, total=False):
    """Type definition for an event object returned by the API.

    Note: This class uses the original field names expected by the FOGIS server.
    Alternative field names (handelsekod, minut, lagid, personid, resultatHemma, resultatBorta)
    are no longer supported as of v0.4.5.
    """

    matchhandelseid: int
    matchid: int
    matchhandelsetypid: int  # Original field name (was handelsekod)
    matchhandelsetypnamn: str  # Original field name (was handelsetyp)
    matchminut: int  # Original field name (was minut)
    matchlagid: int  # Original field name (was lagid)
    matchlagnamn: str  # Original field name (was lag)
    spelareid: Optional[int]  # Original field name (was personid)
    spelarenamn: Optional[str]  # Original field name (was spelare)
    assisterande: Optional[str]
    assisterandeid: Optional[int]
    period: Optional[int]
    mal: Optional[bool]
    hemmamal: Optional[int]  # Original field name (was resultatHemma)
    bortamal: Optional[int]  # Original field name (was resultatBorta)
    strafflage: Optional[str]
    straffriktning: Optional[str]
    straffresultat: Optional[str]
    # Default values for rarely used fields
    sekund: Optional[int]  # Default: 0
    planpositionx: Optional[str]  # Default: '-1'
    planpositiony: Optional[str]  # Default: '-1'
    relateradTillMatchhandelseID: Optional[int]  # Default: 0
    spelareid2: Optional[int]  # Default: -1 (except for substitutions)
    matchdeltagareid2: Optional[int]  # Default: -1 (except for substitutions)


class MatchResultDict(TypedDict, total=False):
    """Type definition for a match result object used in reporting."""

    matchid: int
    hemmamal: int
    bortamal: int
    halvtidHemmamal: Optional[int]
    halvtidBortamal: Optional[int]


class OfficialActionDict(TypedDict, total=False):
    """Type definition for a team official action used in reporting.

    Note: This class uses the original field names expected by the FOGIS server.
    """

    matchid: int
    matchlagid: int  # Original field name (was lagid)
    matchlagledareid: int  # Original field name (was personid)
    matchlagledaretypid: int
    matchminut: Optional[int]  # Original field name (was minut)


class CookieDict(TypedDict, total=False):
    """Type definition for session cookies."""

    FogisMobilDomarKlient_ASPXAUTH: str
    ASP_NET_SessionId: str


class MatchParticipantDict(TypedDict, total=False):
    """Type definition for a match participant update used in reporting."""

    matchdeltagareid: int
    trojnummer: int
    lagdelid: int
    lagkapten: bool
    ersattare: bool
    positionsnummerhv: int
    arSpelandeLedare: bool
    ansvarig: bool
