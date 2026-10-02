import json
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"
SCENARIOS = sorted(p.name for p in FIXTURES.iterdir() if p.is_dir())


def load(scenario: str, kind: str) -> list[Any]:
    """All records of one kind (matches/events/lineups/officials) in a scenario, concatenated."""
    records: list[Any] = []
    for path in sorted((FIXTURES / scenario / kind).glob("*.json")):
        records.extend(json.loads(path.read_text(encoding="utf-8")))
    return records
