"""
Internal type definitions for FOGIS API client.

This module contains TypedDict classes and other type definitions used by the internal API layer.
These types represent the exact structure expected by the FOGIS API server.
"""
from typing import Any, Dict, List, Optional, TypedDict, Union


class InternalMatchDict(TypedDict, total=False):
    """Internal type definition for a match object returned by the API."""
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


class InternalMatchListResponse(TypedDict):
    """Internal type definition for the response from the match list endpoint."""
    matchlista: List[InternalMatchDict]


class InternalPlayerDict(TypedDict, total=False):
    """Internal type definition for a player object returned by the API."""
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


class InternalTeamPlayersResponse(TypedDict):
    """Internal type definition for the response from the team players endpoint."""
    spelare: List[InternalPlayerDict]


class InternalOfficialDict(TypedDict, total=False):
    """Internal type definition for an official object returned by the API."""
    personid: int
    fornamn: str
    efternamn: str
    roll: str
    rollid: int


class InternalEventDict(TypedDict, total=False):
    """Internal type definition for an event object returned by the API."""
    matchhandelseid: int
    matchid: int
    matchhandelsetypid: int  # Internal API name for handelsekod
    matchhandelsetypnamn: str  # Internal API name for handelsetyp
    matchminut: int  # Internal API name for minut
    matchlagid: int  # Internal API name for lagid
    matchlagnamn: str  # Internal API name for lag
    spelareid: Optional[int]  # Internal API name for personid
    spelarenamn: Optional[str]  # Internal API name for spelare
    assisterande: Optional[str]
    assisterandeid: Optional[int]
    period: Optional[int]
    mal: Optional[bool]
    hemmamal: Optional[int]  # Internal API name for resultatHemma
    bortamal: Optional[int]  # Internal API name for resultatBorta
    strafflage: Optional[str]
    straffriktning: Optional[str]
    straffresultat: Optional[str]


class InternalMatchResultItem(TypedDict):
    """Internal type definition for a single match result item in the nested format."""
    matchid: int
    matchresultattypid: int  # 1=fulltime, 2=halftime
    matchlag1mal: int
    matchlag2mal: int
    wo: bool
    ow: bool
    ww: bool


class InternalMatchResultDict(TypedDict):
    """Internal type definition for a match result object in the nested format."""
    matchresultatListaJSON: List[InternalMatchResultItem]


class InternalOfficialActionDict(TypedDict, total=False):
    """Internal type definition for a team official action used in reporting."""
    matchid: int
    matchlagid: int  # Internal API name for lagid
    matchlagledareid: int  # Internal API name for personid
    matchlagledaretypid: int
    matchminut: Optional[int]  # Internal API name for minut


class InternalMatchParticipantDict(TypedDict, total=False):
    """Internal type definition for a match participant update used in reporting."""
    matchdeltagareid: int
    trojnummer: int
    lagdelid: int
    lagkapten: bool
    ersattare: bool
    positionsnummerhv: int
    arSpelandeLedare: bool
    ansvarig: bool


class InternalCookieDict(TypedDict, total=False):
    """Internal type definition for session cookies."""
    FogisMobilDomarKlient_ASPXAUTH: str
    ASP_NET_SessionId: str
