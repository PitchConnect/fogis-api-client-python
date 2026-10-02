"""Write methods, with payloads exactly as the referee app builds them (FOGIS_API.md §4, app v20260610).

Payloads are taken from the app's code; event saves, edits, substitutions and deletes are confirmed live
(identical to the app's, 2026-09-27). Other write responses are still unknown, so responses are returned as
FOGIS sends them and logged. Remaining assumptions are marked [unverified] with their §10 checklist item.

Use dry_run=True (payloads are logged and returned, nothing is sent) or a confirm callback while trying this
out. Two calls cannot be undone and have extra guards: mark_reporting_finished (submits the referee report)
and end_live_reporting. SkjutUppMatch (postpones the match) is deliberately not implemented.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from .checks import Problem
from .enums import EventType, ResultType
from .errors import FogisDataError, FogisError
from .matchtime import encode_match_time
from .models import LineupEntry, Match, MatchEvent, TeamOfficial
from .timeline import Substitution

if TYPE_CHECKING:
    from .session import FogisSession

log = logging.getLogger(__name__)

Confirm = Callable[[str, Mapping[str, Any]], bool]

# Types for which the app asks for the score after the event (arMatchResultatpaverkande).
SCORE_TYPES = frozenset(
    {
        EventType.STRAFFMAL,
        EventType.SPELMAL,
        EventType.NICKMAL,
        EventType.HORNMAL,
        EventType.FRISPARKSMAL,
        EventType.SJALVMAL,
        EventType.STRAFFAVGORANDE_MAL,
        EventType.TIO_METER_STRAFF_MAL_FUTSAL,
    }
)
# Event types this library refuses to save, and why.
_HIDDEN = "is stored as a yellow card the event list never shows, so it can neither be seen nor deleted"
# Event types this library refuses to save, and why.
NEVER_SAVE: dict[int, str] = {
    EventType.VARNING_OJUST_SPEL: f"type 1 {_HIDDEN} (FOGIS_API.md §6); use EventType.VARNING",
    EventType.VARNING_OLAMPLIGT_UPPTRADANDE: f"type 7 {_HIDDEN} (FOGIS_API.md §6); use EventType.VARNING",
    EventType.LINDRIG_UTVISNING_AVVISNING: "FOGIS creates the sending-off for a second caution itself; "
    "save the second caution (EventType.VARNING) instead",
}
# Types the referee app never sends: untested through this API, so only with allow_untested=True.
UNTESTED: dict[int, str] = {
    EventType.STRAFFSPARK: "type 3 ('penalty awarded', used by live-reporting clients before the outcome)",
    EventType.ANNONSERAD_STOPPTID: "type 33 (announced added time; accepted but not listed on 2026-09-30)",
}
_FINAL_METHODS = frozenset({"SparaMatchGodkannDomarrapport", "SparaMatchAvslutaLiveRapportering"})


def _no_0x_call(method: str, first: Any, expected: type, new_form: str) -> None:
    """0.x write methods took one dict (or a bare match id); 1.0 takes models. Say so, not a cryptic error."""
    if not isinstance(first, expected):
        raise TypeError(f"{method}() changed in 1.0: use {new_form} (see docs/MIGRATION.md)")


class FogisWriteCancelled(FogisError):
    """The confirm callback declined a write."""


@dataclass(frozen=True, slots=True)
class DryRun:
    """Returned instead of FOGIS's answer when the client is in dry-run mode."""

    method: str
    payload: Mapping[str, Any]


class WriteMethods:
    """Mixed into FogisClient."""

    session: FogisSession
    dry_run: bool
    confirm: Confirm | None

    # ------------------------------------------------------------------ events

    def save_match_event(
        self,
        match: Match,
        event_type: EventType | int,
        time: str,
        *,
        team_id: int = 0,
        player: LineupEntry | None = None,
        score: tuple[int, int] | None = None,
        position: tuple[int, int] | None = None,
        event_id: int = 0,
        allow_untested: bool = False,
    ) -> Any:
        """Save a new event (event_id=0) or overwrite an existing one, as the app's event form does.

        time: as typed in the app ("23", "45+2", "12:30"); see matchtime.encode_match_time.
        team_id: the team's match_team_id; 0 for match events such as period start/end.
        score: (home, away) after the event; required for goals (SCORE_TYPES) and never checked by FOGIS.
            next_score() gives the app's suggestion.
        For substitutions use substitute(); cautions that make a second caution get their sending-off
        added by FOGIS itself. Types 1, 7 and 2 are refused (NEVER_SAVE); types the referee app never sends
        (UNTESTED: 3, 33) need allow_untested=True.
        """
        _no_0x_call(
            "save_match_event",
            match,
            Match,
            "save_match_event(match, event_type, time, team_id=..., player=...)",
        )
        event_type = int(event_type)
        if event_type in NEVER_SAVE:
            raise ValueError(NEVER_SAVE[event_type])
        if event_type in UNTESTED and not allow_untested:
            raise ValueError(
                f"{UNTESTED[event_type]} is not offered by the referee app and untested through this "
                "API; pass allow_untested=True to send it anyway"
            )
        if event_type in (EventType.BYTE_IN, EventType.BYTE_UT):
            raise ValueError("use substitute() for substitutions")
        if event_type in SCORE_TYPES and score is None:
            raise ValueError("score (home, away) after the goal is required; see next_score()")
        t = encode_match_time(time, match, event_type)
        is_goal = event_type in (EventType.SPELMAL, EventType.NICKMAL)
        payload = _event_payload(
            match,
            event_id=event_id,
            time=(t.period, t.minute, t.second),
            event_type=event_type,
            team_id=team_id,
            player=player,
            # The referee client has no assist input and always sends -1 for goals (FOGIS_API.md §6).
            second_player=(-1, -1) if is_goal else (0, None),
            score=score if event_type in SCORE_TYPES and score else (0, 0),
            position=position,
        )
        return self._write("SparaMatchhandelse", payload)

    def substitute(
        self, match: Match, time: str, *, team_id: int, player_in: LineupEntry, player_out: LineupEntry
    ) -> Any:
        """Save a substitution. Like the app, one BYTE_IN event carrying the outgoing player as the second
        player; FOGIS stores it as BYTE_UT + linked BYTE_IN (confirmed live). To delete a substitution, delete
        both events, the BYTE_IN first: FOGIS does not remove the pair by itself.
        """
        t = encode_match_time(time, match, EventType.BYTE_IN)
        payload = _event_payload(
            match,
            event_id=0,
            time=(t.period, t.minute, t.second),
            event_type=EventType.BYTE_IN,
            team_id=team_id,
            player=player_in,
            second_player=(player_out.player_id, player_out.participant_id),
            score=(0, 0),
            position=None,
        )
        return self._write("SparaMatchhandelse", payload)

    def edit_substitution(
        self,
        match: Match,
        sub: Substitution,
        *,
        time: str | None = None,
        player_in: LineupEntry | None = None,
        player_out: LineupEntry | None = None,
    ) -> Any:
        """Correct a stored substitution in place, as the app's "Ändra händelse" does: both events keep
        their ids and link; only what is given changes. The team cannot change (the app locks it too).

        `sub` comes from timeline.pair_substitutions() and must be a linked pair. Like the app, two saves:
        the BYTE_IN with the incoming player, then the BYTE_UT carrying the outgoing player as the second
        player. [unverified: live behaviour, checklist §10.15]
        """
        on, off = sub.on, sub.off
        if sub.pairing != "linked" or on is None or off is None:
            raise ValueError(
                "only a linked substitution (both halves, linked by FOGIS) can be edited in place"
            )
        text = on.time_text if time is None else time
        t = encode_match_time("" if text in ("0", "0:00") else text, match, EventType.BYTE_IN)
        x, y = (
            (str(on.position_x), str(on.position_y))
            if on.position_x is not None and on.position_y is not None
            else ("-1", "-1")
        )
        common = {
            "matchid": match.match_id,
            "period": t.period,
            "matchminut": t.minute,
            "sekund": t.second,
            "hemmamal": 0,
            "bortamal": 0,
            "planpositionx": x,
            "planpositiony": y,
            "fotbollstypId": match.raw.get("fotbollstypid", 1),
        }
        in_ids = (
            (player_in.player_id, player_in.participant_id)
            if player_in
            else (on.player_id, on.participant_id)
        )
        out_ids = (
            (player_out.player_id, player_out.participant_id)
            if player_out
            else (off.player_id, off.participant_id)
        )
        on_payload = {
            "matchhandelseid": on.event_id,
            **common,
            "matchhandelsetypid": int(EventType.BYTE_IN),
            "matchlagid": on.match_team_id or 0,
            "spelareid": in_ids[0] or 0,
            "spelareid2": 0,
            "matchdeltagareid": in_ids[1],
            "matchdeltagareid2": 0,
            "relateradTillMatchhandelseID": on.related_event_id or 0,
        }
        off_payload = {
            "matchhandelseid": off.event_id,
            **common,
            "matchhandelsetypid": int(EventType.BYTE_UT),
            "matchlagid": off.match_team_id or 0,
            "spelareid": 0,
            "spelareid2": out_ids[0] or 0,
            "matchdeltagareid": None,
            "matchdeltagareid2": out_ids[1],
            "relateradTillMatchhandelseID": off.related_event_id or 0,
        }
        self._write("SparaMatchhandelse", on_payload)
        return self._write("SparaMatchhandelse", off_payload)

    def delete_match_event(self, event_id: int) -> Any:
        """Delete one event. Deleting a second caution does NOT remove the sending-off FOGIS created for it
        (FOGIS_API.md §6); delete that one too."""
        return self._write("RaderaMatchhandelse", {"matchhandelseid": event_id})

    # ------------------------------------------------------------------ results, attendance, notes

    def report_match_result(self, match_id: int, results: Mapping[ResultType | int, tuple[int, int]]) -> Any:
        """Save result rows, e.g. {ResultType.SLUTRESULTAT: (2, 1), ResultType.HALVTIDSRESULTAT: (1, 0)}.

        Like the app, send only rows that changed. (-1, -1) is the app's "empty" [unverified: clears the row?
        checklist §10.7].
        """
        _no_0x_call(
            "report_match_result",
            match_id,
            int,
            "report_match_result(match_id, {ResultType.SLUTRESULTAT: (h, a)})",
        )
        rows = [
            {
                "matchid": match_id,
                "matchresultattypid": int(kind),
                "matchlag1mal": home,
                "matchlag2mal": away,
                "wo": False,
                "ow": False,
                "ww": False,
            }
            for kind, (home, away) in results.items()
        ]
        return self._write("SparaMatchresultatLista", {"matchresultatListaJSON": rows})

    def save_attendance(self, match_id: int, spectators: int) -> Any:
        return self._write("SparaPubliksiffra", {"matchid": match_id, "antalaskadare": spectators})

    def save_referee_note(self, match_id: int, text: str) -> Any:
        """The referee's note on the match report (FOGIS's field name is misspelled, 'noterinfrandomare')."""
        return self._write("SparaNoteringFranDomare", {"matchid": match_id, "noterinfrandomare": text})

    # ------------------------------------------------------------------ team officials

    def save_official_discipline(
        self,
        official: TeamOfficial,
        *,
        minute: int = 0,
        caution: bool = False,
        sending_off: Literal["minor", "major"] | None = None,
    ) -> Any:
        """Give a team official a caution (minute -> varnadmatchminut) and/or a sending-off (minute ->
        avvisadmatchminut), as the app's discipline form does.

        FOGIS can only SET discipline this way; it silently ignores every attempt to remove it
        (confirmed live, FOGIS_API.md §8). To remove discipline use clear_official_discipline().
        Calling this with nothing to set for an official who has discipline raises ValueError
        instead of pretending to clear it.

        SparaMatchlagledare overwrites the role and the 'responsible' flag too, so they are re-sent from
        `official` (read it fresh).
        """
        if not caution and sending_off is None and (official.cautioned or official.sent_off):
            raise ValueError("FOGIS ignores removing discipline this way; use clear_official_discipline()")
        payload = {
            "matchlagledareid": official.official_id,
            "lagrollid": official.role_id,
            "avvisadmatchminut": minute,
            "avvisadlindrig": sending_off == "minor",
            "avvisadgrov": sending_off == "major",
            "varnad": caution,
            "ansvarig": official.responsible,
        }
        return self._write("SparaMatchlagledare", payload)

    def save_match_participant(
        self,
        player: LineupEntry,
        *,
        shirt_number: int | None = None,
        substitute: bool | None = None,
        captain: bool | None = None,
        goalkeeper: bool | None = None,
    ) -> Any:
        """Change one player's line-up entry as the app's player form does, e.g. a new shirt number after a
        torn shirt, or starting/bench after an injury in the warm-up. Only the given fields change.

        SparaMatchdeltagare overwrites all eight fields, so the others are re-sent from `player` (read it
        fresh). Like the app: shirt number -1 means none, a substitute gets position -1 and a starting
        goalkeeper position 1. [unverified: live behaviour, checklist §10.13]
        """
        _no_0x_call(
            "save_match_participant", player, LineupEntry, "save_match_participant(player, shirt_number=...)"
        )
        raw = player.raw
        team_part = raw.get("lagdelid", 0) if goalkeeper is None else (1 if goalkeeper else 0)
        is_substitute = player.substitute if substitute is None else substitute
        position = raw.get("positionsnummerhv", 0)
        if team_part == 1 and not is_substitute:
            position = 1
        if is_substitute:
            position = -1
        payload = {
            "matchdeltagareid": player.participant_id,
            "trojnummer": (player.shirt_number if player.shirt_number is not None else -1)
            if shirt_number is None
            else shirt_number,
            "lagdelid": team_part,
            "lagkapten": player.captain if captain is None else captain,
            "ersattare": is_substitute,
            "positionsnummerhv": position,
            "arSpelandeLedare": player.playing_official,
            "ansvarig": player.responsible,
        }
        return self._write("SparaMatchdeltagare", payload)

    def remove_team_official(self, match_team_id: int, official_id: int) -> Any:
        """Remove a team official from one team's match sheet (the app's team-sheet page, "Klar")."""
        return self._write(
            "MatchLaguppställningKlar",
            {
                "matchlagid": match_team_id,
                "matchdeltagareAttRaderaListaJSON": [],
                "matchDeltagareAndraErsattareListaJSON": [],
                "matchlagledareAttRaderaListaJSON": [{"matchlagledareid": official_id}],
                "matchdeltagareAttAndraPositionListaJSON": [],
            },
        )

    def add_team_official(self, match_id: int, match_team_id: int, person_id: int, role_id: int) -> Any:
        """Add a person as team official in one match. FOGIS returns the new record, not yet 'responsible'."""
        return self._write(
            "LaggTillMatchlagledare",
            {"personid": person_id, "lagrollid": role_id, "matchid": match_id, "matchlagid": match_team_id},
        )

    def clear_official_discipline(self, official: TeamOfficial) -> TeamOfficial:
        """Remove a team official's caution and/or sending-off. Returns the official's new record.

        FOGIS cannot remove discipline from a record, so this does what works in the app: remove the official
        from the match, add the same person with the same role again (a new, clean record with a new id), and
        restore the 'responsible' flag. The result is read back and checked; FogisDataError if it isn't clean.
        Pass a freshly read official. Not available in dry-run mode (step 3 needs the new record's id).
        """
        if not (official.cautioned or official.sent_off):
            return official
        if self.dry_run:
            raise ValueError("clear_official_discipline needs real answers; it cannot run in dry-run mode")
        self.remove_team_official(official.match_team_id, official.official_id)
        added = self.add_team_official(
            official.match_id, official.match_team_id, official.person_id, official.role_id
        )
        if not isinstance(added, Mapping) or not added.get("matchlagledareid"):
            raise FogisDataError(f"LaggTillMatchlagledare returned no new record: {type(added).__name__}")
        new_id = added["matchlagledareid"]
        if official.responsible:
            self._write(
                "SparaMatchlagledare",
                {
                    "matchlagledareid": new_id,
                    "lagrollid": official.role_id,
                    "avvisadmatchminut": 0,
                    "avvisadlindrig": False,
                    "avvisadgrov": False,
                    "varnad": False,
                    "ansvarig": True,
                },
            )
        rows = self.session.call("GetMatchlagledareListaForMatchlag", {"matchlagid": official.match_team_id})
        current = [TeamOfficial.from_api(r) for r in rows]
        new = next((o for o in current if o.official_id == new_id), None)
        problems = []
        if any(o.official_id == official.official_id for o in current):
            problems.append("the old record is still there")
        if new is None:
            problems.append("the new record is missing")
        elif (new.person_id, new.role_id) != (official.person_id, official.role_id):
            problems.append("the new record has another person or role")
        elif new.cautioned or new.sent_off:
            problems.append("the new record still has discipline")
        elif new.responsible != official.responsible:
            problems.append("'responsible' was not restored")
        if problems or new is None:
            raise FogisDataError(
                f"clear_official_discipline for person {official.person_id}: " + "; ".join(problems)
            )
        return new

    # ------------------------------------------------------------------ irreversible

    def check_report(self, match: Match) -> list[Problem]:
        raise NotImplementedError  # provided by FogisClient

    def mark_reporting_finished(
        self,
        match: Match,
        *,
        confirm_match_id: int,
        allow_missing_result: bool = False,
        ignore_problems: bool = False,
    ) -> Any:
        """SUBMIT THE REFEREE REPORT (SparaMatchGodkannDomarrapport). THIS CANNOT BE UNDONE.

        After this, the referee can no longer change anything in the report: no new events, no edits or
        deletions of existing events, results, line-ups or team-official discipline. The app warns:
        "När du godkänt domarrapporten har du inte längre möjlighet att administrera den."
        Depending on the competition, the report may then be reviewed by the administering association.

        Guards (all must pass; dry_run and the confirm callback apply as for every write):
        - confirm_match_id must repeat match.match_id;
        - the report must not already be approved;
        - a final result must be reported (the app warns about this too), unless allow_missing_result=True;
        - check_report() must find no errors (wrong result, duplicate events, events without a minute, ...),
          unless ignore_problems=True. The problems are in the ValueError's message.

        Pass a Match read just before, so the checks see the current state.
        """
        _no_0x_call(
            "mark_reporting_finished", match, Match, "mark_reporting_finished(match, confirm_match_id=...)"
        )
        self._check_irreversible(match, confirm_match_id, allow_missing_result)
        if match.report_approved:
            raise ValueError(f"the report for match {match.match_id} is already approved")
        if not ignore_problems:
            errors = [p for p in self.check_report(match) if p.severity == "error"]
            if allow_missing_result:
                errors = [p for p in errors if p.code != "no_final_result"]
            if errors:
                raise ValueError("the report has problems:\n" + "\n".join(f"- {p.message}" for p in errors))
        return self._send("SparaMatchGodkannDomarrapport", {"matchid": match.match_id})

    def end_live_reporting(
        self, match: Match, *, confirm_match_id: int, allow_missing_result: bool = False
    ) -> Any:
        """END LIVE REPORTING (SparaMatchAvslutaLiveRapportering). THIS CANNOT BE UNDONE.

        After this, no more events or results can be added to the match. The app warns:
        "När du avslutat matchrapporteringen kan du inte lägga in fler händelser eller resultat."
        This is not the same as submitting the report (mark_reporting_finished).

        Guards as for mark_reporting_finished.
        """
        self._check_irreversible(match, confirm_match_id, allow_missing_result)
        return self._send("SparaMatchAvslutaLiveRapportering", {"matchid": match.match_id})

    @staticmethod
    def _check_irreversible(match: Match, confirm_match_id: int, allow_missing_result: bool) -> None:
        if confirm_match_id != match.match_id:
            raise ValueError(
                f"confirm_match_id={confirm_match_id} does not repeat match_id={match.match_id}; "
                "this call cannot be undone"
            )
        if not match.result_is_final and not allow_missing_result:
            raise ValueError(
                f"match {match.match_id} has no final result; "
                "report it first or pass allow_missing_result=True"
            )

    # ------------------------------------------------------------------ plumbing

    def _write(self, method: str, payload: Mapping[str, Any]) -> Any:
        if method in _FINAL_METHODS:
            raise AssertionError(f"{method} must go through its own guarded method")
        return self._send(method, payload)

    def _send(self, method: str, payload: Mapping[str, Any]) -> Any:
        if self.dry_run:
            log.info("dry run: %s %s", method, payload)
            return DryRun(method, payload)
        if self.confirm is not None and not self.confirm(method, payload):
            raise FogisWriteCancelled(f"{method} not sent: declined")
        d = _without_personnr(self.session.call(method, payload))
        log.info("%s answered with %s", method, type(d).__name__)
        return d


def _without_personnr(d: Any) -> Any:
    """Some write responses carry every official's personnummer (SparaMatchlagledare); never pass it on."""
    if isinstance(d, list):
        return [_without_personnr(x) for x in d]
    if isinstance(d, dict):
        return {k: _without_personnr(v) for k, v in d.items() if k != "personnr"}
    return d


def next_score(events: Iterable[MatchEvent], match: Match, team_id: int) -> tuple[int, int]:
    """The score the app pre-fills for a new goal by `team_id`: the highest home/away score typed on any
    earlier goal, plus one for the scoring team. Own goals are recorded on the benefiting team."""
    home = max((e.home_goals for e in events if e.type_id in SCORE_TYPES), default=0)
    away = max((e.away_goals for e in events if e.type_id in SCORE_TYPES), default=0)
    if team_id == match.home.match_team_id:
        home += 1
    elif team_id == match.away.match_team_id:
        away += 1
    else:
        raise ValueError(f"team {team_id} does not play in match {match.match_id}")
    return home, away


def _event_payload(
    match: Match,
    *,
    event_id: int,
    time: tuple[int, int, int],
    event_type: int,
    team_id: int,
    player: LineupEntry | None,
    second_player: tuple[int, int | None],
    score: tuple[int, int],
    position: tuple[int, int] | None,
) -> dict[str, Any]:
    period, minute, second = time
    x, y = (str(position[0]), str(position[1])) if position else ("-1", "-1")
    return {
        "matchhandelseid": event_id,
        "matchid": match.match_id,
        "period": period,
        "matchminut": minute,
        "sekund": second,
        "matchhandelsetypid": int(event_type),
        "matchlagid": team_id,
        "spelareid": player.player_id if player else 0,
        "spelareid2": second_player[0],
        "hemmamal": score[0],
        "bortamal": score[1],
        "planpositionx": x,
        "planpositiony": y,
        "matchdeltagareid": player.participant_id if player else None,
        "matchdeltagareid2": second_player[1],
        "fotbollstypId": match.raw.get("fotbollstypid", 1),
        "relateradTillMatchhandelseID": 0,
    }
