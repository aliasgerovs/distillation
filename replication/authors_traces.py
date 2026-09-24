"""The authors' released MATH seed-456 teacher traces, from branch `mahdi` of ysfalh/distillation-game."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ("upstream/mahdi", "origin/mahdi")
FETCH = "git remote add upstream https://github.com/ysfalh/distillation-game.git && git fetch upstream mahdi"


def load_authors_json(path: str) -> list[dict]:
    """Read a JSON file from the authors' `mahdi` branch, e.g. math_output_small/train_standard.json."""
    for ref in REFS:
        out = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True)
        if out.returncode == 0:
            return json.loads(out.stdout)
    raise SystemExit(f"The authors' `mahdi` branch is not available locally. Fetch it with:\n  {FETCH}")
