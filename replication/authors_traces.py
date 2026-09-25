"""The authors' released MATH seed-456 teacher traces, kept in replication/reference/ (see its README)."""
from __future__ import annotations

import json
from pathlib import Path

REFERENCE = Path(__file__).resolve().parent / "reference" / "authors_math_seed456"


def load_authors_json(name: str) -> list[dict]:
    """Load one reference file, e.g. train_standard.json."""
    return json.loads((REFERENCE / name).read_text())
