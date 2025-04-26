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
    """Type definition for an event object returned by the API."""

    matchhandelseid: int
    matchid: int
    handelsekod: int
    handelsetyp: str
    minut: int
    lagid: int
    lag: str
    personid: Optional[int]
    spelare: Optional[str]
    assisterande: Optional[str]
    assisterandeid: Optional[int]
    period: Optional[int]
    mal: Optional[bool]
    resultatHemma: Optional[int]
    resultatBorta: Optional[int]
    strafflage: Optional[str]
    straffriktning: Optional[str]
    straffresultat: Optional[str]


class MatchResultDict(TypedDict, total=False):
    """Type definition for a match result object used in reporting."""

    matchid: int
    hemmamal: int
    bortamal: int
    halvtidHemmamal: Optional[int]
    halvtidBortamal: Optional[int]


class OfficialActionDict(TypedDict, total=False):
    """Type definition for a team official action used in reporting."""

    matchid: int
    lagid: int
    personid: int
    matchlagledaretypid: int
    minut: Optional[int]


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
