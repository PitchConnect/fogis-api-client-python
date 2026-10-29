"""Turning models into JSON and plain-text tables."""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime, time
from enum import Enum
from typing import IO, Any

from ..timeline import GoalScore, TimelineEntry

# A goal's score sits next to its event in a timeline entry; repeating the event inside it adds nothing.
_OMIT: dict[type, frozenset[str]] = {GoalScore: frozenset({"event"})}


def jsonable(value: Any, *, raw: bool = False) -> Any:
    """Models as plain JSON values: dataclass fields (without `raw`) plus their properties, enums by name,
    dates as ISO 8601. With raw=True a model is replaced by the FOGIS record it was parsed from."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        if raw and hasattr(value, "raw"):
            return value.raw
        omit = _OMIT.get(type(value), frozenset()) | {"raw"}
        fields = (f.name for f in dataclasses.fields(value) if f.name not in omit)
        out = {name: jsonable(getattr(value, name)) for name in fields}
        for name, attr in vars(type(value)).items():
            if isinstance(attr, property) and not name.startswith("_"):
                out[name] = jsonable(getattr(value, name))
        return out
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, datetime | date | time):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(k): jsonable(v, raw=raw) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [jsonable(v, raw=raw) for v in value]
    return value


def write_json(value: Any, out: IO[str], *, raw: bool = False) -> None:
    json.dump(jsonable(value, raw=raw), out, ensure_ascii=False, indent=2)
    out.write("\n")


Column = tuple[str, Callable[[Any], object]]


def write_table(rows: Sequence[Any], columns: Sequence[Column], out: IO[str]) -> None:
    cells = [[header for header, _ in columns]]
    cells += [["" if (v := get(row)) is None else str(v) for _, get in columns] for row in rows]
    widths = [max(len(r[i]) for r in cells) for i in range(len(columns))]
    for r in cells:
        out.write("  ".join(c.ljust(w) for c, w in zip(r, widths, strict=True)).rstrip() + "\n")


def clock(e: TimelineEntry) -> str:
    """'45+2' style minute of a timeline entry."""
    if e.event is not None and e.event.time_text:
        return e.event.time_text
    if e.minute is None:
        return ""
    return f"{e.minute}+{e.added_minutes}" if e.added_minutes else str(e.minute)
