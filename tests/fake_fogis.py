"""In-memory FOGIS for testing the verification runner.

Server behaviour follows FOGIS_API.md §6 as far as it is known ([history]) or assumed
([unverified]: one-call substitutions become 16 + linked 17)."""

import copy
from typing import Any

from fogis_api_client.models import Match

KNOWN_READS = {
    "GetMatcherAttRapportera",
    "GetMatchhandelselista",
    "GetMatchresultatlista",
    "GetMatchdeltagareListaForMatchlag",
    "GetMatchlagledareListaForMatchlag",
}


class FakeFogis:
    def __init__(
        self,
        match: dict[str, Any],
        events: list[dict[str, Any]],
        lineups: dict[int, list[dict[str, Any]]],
        officials: dict[int, list[dict[str, Any]]],
        results: list[dict[str, Any]] | None = None,
    ) -> None:
        self.match = copy.deepcopy(match)
        self.events = copy.deepcopy(events)
        self.lineups = copy.deepcopy(lineups)
        self.officials = copy.deepcopy(officials)
        self.results = copy.deepcopy(results or [])
        self.next_id = max([e["matchhandelseid"] for e in events] + [1000]) + 10
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.fail_on: str | None = None  # method name that raises, to test aborts

    # the FogisSession interface used by FogisClient
    def call(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        payload = payload or {}
        self.calls.append((method, payload))
        if method == self.fail_on:
            raise RuntimeError(f"injected failure in {method}")
        if method == "GetMatcherAttRapportera":
            return {"matchlista": [copy.deepcopy(self.match)]}
        if method == "GetMatchhandelselista":
            return copy.deepcopy(self.events)
        if method == "GetMatchresultatlista":
            return copy.deepcopy(self.results)
        if method == "GetMatchdeltagareListaForMatchlag":
            return copy.deepcopy(self.lineups[payload["matchlagid"]])
        if method == "GetMatchlagledareListaForMatchlag":
            return copy.deepcopy(self.officials[payload["matchlagid"]])
        handler = getattr(self, "_" + method, None)
        if handler is None:
            raise AssertionError(f"fake FOGIS does not implement {method}")
        return handler(payload)

    def close(self) -> None:
        pass

    # ---------------------------------------------------------------- writes

    def _new_id(self) -> int:
        self.next_id += 1
        return self.next_id

    def _time_text(self, period: int, minute: int) -> str:
        m = Match.from_api(self.match)
        end = m.half_length * min(period, m.halves) + (
            m.extra_period_length * (period - m.halves) if period > m.halves else 0
        )
        if period and 0 < end < minute and period <= m.halves + m.extra_periods:
            return f"{end}+{minute - end}"
        return str(minute)

    def _stored(
        self,
        p: dict[str, Any],
        event_type: int,
        event_id: int,
        *,
        player: int,
        participant: int | None,
        rel: int = 0,
    ) -> dict[str, Any]:
        text = self._time_text(p["period"], p["matchminut"])
        base = int(text.split("+")[0])
        return {
            "__type": "MatchhandelseJSON",
            "matchhandelseid": event_id,
            "matchid": p["matchid"],
            "matchdeltagareid": participant or 0,
            "matchhandelsetypid": event_type,
            "matchhandelsetypnamn": str(event_type),
            "matchlagid": p["matchlagid"],
            "matchlagnamn": "",
            "trojnummer": -1,
            "spelareid": player,
            "spelarenamn": "",
            "matchminut": base,
            "kommentar": "",
            "hemmamal": p["hemmamal"],
            "bortamal": p["bortamal"],
            "period": p["period"],
            "matchhandelsetypmedforstallningsandring": False,
            "matchhandelsetypanvanderannonseradtid": event_type == 33,
            "tidsangivelse": text,
            "planpositionx": int(p["planpositionx"]),
            "planpositiony": int(p["planpositiony"]),
            "relateradTillMatchhandelseID": rel,
        }

    def _SparaMatchhandelse(self, p: dict[str, Any]) -> Any:
        t = p["matchhandelsetypid"]
        if p["matchhandelseid"]:
            for i, e in enumerate(self.events):
                if e["matchhandelseid"] == p["matchhandelseid"]:
                    self.events[i] = self._stored(
                        p,
                        t,
                        e["matchhandelseid"],
                        # the app edits a 16 with the outgoing player as the second player [unverified]
                        player=p["spelareid"] or p["spelareid2"],
                        participant=p["matchdeltagareid"] or p["matchdeltagareid2"],
                        rel=e["relateradTillMatchhandelseID"],
                    )
            return None
        if t == 17 and p["spelareid2"]:
            off = self._stored(
                p, 16, self._new_id(), player=p["spelareid2"], participant=p["matchdeltagareid2"]
            )
            on = self._stored(
                p,
                17,
                self._new_id(),
                player=p["spelareid"],
                participant=p["matchdeltagareid"],
                rel=off["matchhandelseid"],
            )
            self.events += [off, on]
            return None
        if t == 14:
            award = self._stored(
                p, 3, self._new_id(), player=p["spelareid"], participant=p["matchdeltagareid"]
            )
            goal = self._stored(
                p,
                14,
                self._new_id(),
                player=p["spelareid"],
                participant=p["matchdeltagareid"],
                rel=award["matchhandelseid"],
            )
            self.events += [award, goal]
            return None
        e = self._stored(p, t, self._new_id(), player=p["spelareid"], participant=p["matchdeltagareid"])
        self.events.append(e)
        if (
            t == 20
            and sum(
                1 for x in self.events if x["matchhandelsetypid"] == 20 and x["spelareid"] == e["spelareid"]
            )
            == 2
        ):
            second = dict(e, matchhandelseid=self._new_id(), matchhandelsetypid=2)
            self.events.append(second)
        return None

    def _RaderaMatchhandelse(self, p: dict[str, Any]) -> Any:
        self.events = [e for e in self.events if e["matchhandelseid"] != p["matchhandelseid"]]
        return None

    def _SparaMatchlagledare(self, p: dict[str, Any]) -> Any:
        """Like FOGIS: discipline can be set but never removed (FOGIS_API.md §8)."""
        for rows in self.officials.values():
            for r in rows:
                if r["matchlagledareid"] == p["matchlagledareid"]:
                    r.update(lagrollid=p["lagrollid"], ansvarig=p["ansvarig"])
                    if p["varnad"]:
                        r.update(varnad=True, varnadmatchminut=p["avvisadmatchminut"])
                    if p["avvisadlindrig"] or p["avvisadgrov"]:
                        r.update(
                            avvisadlindrig=p["avvisadlindrig"],
                            avvisadgrov=p["avvisadgrov"],
                            avvisadmatchminut=p["avvisadmatchminut"],
                        )
                    return [dict(x, personnr="19800101-0000") for x in copy.deepcopy(rows)]
        raise AssertionError(f"no official {p['matchlagledareid']}")

    def _MatchLaguppställningKlar(self, p: dict[str, Any]) -> Any:
        gone = {x["matchlagledareid"] for x in p["matchlagledareAttRaderaListaJSON"]}
        self.officials[p["matchlagid"]] = [
            r for r in self.officials[p["matchlagid"]] if r["matchlagledareid"] not in gone
        ]
        return None

    def _LaggTillMatchlagledare(self, p: dict[str, Any]) -> Any:
        template = next(r for rows in self.officials.values() for r in rows)
        new = dict(
            template,
            matchlagledareid=self._new_id(),
            personid=p["personid"],
            lagrollid=p["lagrollid"],
            matchid=p["matchid"],
            matchlagid=p["matchlagid"],
            ansvarig=False,
            varnad=False,
            varnadmatchminut=0,
            avvisadlindrig=False,
            avvisadgrov=False,
            avvisadmatchminut=0,
        )
        self.officials[p["matchlagid"]].append(new)
        return dict(new, personnr="19800101-0000")

    def _SparaMatchdeltagare(self, p: dict[str, Any]) -> Any:
        for rows in self.lineups.values():
            for r in rows:
                if r["matchdeltagareid"] == p["matchdeltagareid"]:
                    r.update(
                        {
                            k: p[k]
                            for k in (
                                "trojnummer",
                                "lagdelid",
                                "lagkapten",
                                "ersattare",
                                "positionsnummerhv",
                                "arSpelandeLedare",
                                "ansvarig",
                            )
                        }
                    )
                    return copy.deepcopy(r)
        raise AssertionError(f"no participant {p['matchdeltagareid']}")

    def _SparaMatchresultatLista(self, p: dict[str, Any]) -> Any:
        for row in p["matchresultatListaJSON"]:
            existing = next(
                (r for r in self.results if r["matchresultattypid"] == row["matchresultattypid"]), None
            )
            if existing is None:
                self.results.append(dict(row, matchresultatid=self._new_id(), matchresultattypnamn=""))
            else:
                existing.update(row)
        return None

    def _SparaPubliksiffra(self, p: dict[str, Any]) -> Any:
        self.match["antalaskadare"] = p["antalaskadare"]
        return None

    def _SparaNoteringFranDomare(self, p: dict[str, Any]) -> Any:
        self.match["noteringfrandomare"] = p["noterinfrandomare"]
        return None
