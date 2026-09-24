#!/usr/bin/env python3
"""Sanity-check a finished run_pipeline.py run, given its job config. Exits 1 on failure.

Checks: every expected teacher/student row is in results.json, no stored teacher trace begins with the
prompt (which would mean it was not stripped and the student trains on it; a model echoing the prompt
later in its output is legitimate), and teacher accuracy is in a plausible range (paper Table 1:
standard 87% GSM8K / 62% MATH).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MIN_TEACHER_ACC = {"gsm8k": 0.60, "math": 0.35}
from clean_sweep.data.gsm8k import SYSTEM_PROMPT


def not_stripped(row: dict) -> bool:
    """An unstripped prompt starts with the exact system prompt and then contains the problem itself.

    A defended teacher (PoE mixes in a base-model proxy) occasionally echoes the system prompt at the
    start of its answer; those echoes differ in formatting and never contain the problem text.
    """
    head = row["trace"].lstrip()[: len(SYSTEM_PROMPT) + 400]
    return head.startswith(SYSTEM_PROMPT.strip()) and row["prompt"].strip()[:60] in head


def latest_run_dir(cfg: dict) -> Path | None:
    out = ROOT / cfg["run"]["output_dir"]
    runs = sorted(p.parent for p in out.glob(f"{cfg['run']['run_name']}_*/results.json"))
    return runs[-1] if runs else None


def main() -> int:
    cfg = yaml.safe_load(Path(sys.argv[1]).read_text())
    run = latest_run_dir(cfg)
    if run is None:
        print(f"FAIL: no results.json for {cfg['run']['run_name']} under {cfg['run']['output_dir']}")
        return 1
    rows = json.loads((run / "results.json").read_text())
    by_model = {(r["train_source"], r["eval_model"]): r for r in rows}
    problems = []

    teachers = (["teacher_standard"] if cfg["teachers"]["standard"] else []) + [
        f"teacher_poe_gamma_{g}" for g in cfg["teachers"]["poe_gammas"]
    ]
    floor = MIN_TEACHER_ACC[cfg["data"]["dataset_name"]]
    for t in teachers:
        row = by_model.get(("-", f"{t}_test"))
        if row is None:
            problems.append(f"missing teacher row {t}_test")
        elif row["accuracy"] < floor:
            problems.append(f"{t} test accuracy {row['accuracy']:.3f} below sanity floor {floor}")
        for mode in cfg["distill"]["student_modes"]:
            if (t, f"student_{mode}") not in by_model:
                problems.append(f"missing student row {t} / {mode}")

    for f in sorted((run / "teacher").glob("*.json")):
        traces = json.loads(f.read_text())
        leaked = sum(not_stripped(r) for r in traces)
        if leaked:
            problems.append(f"{f.name}: {leaked}/{len(traces)} traces start with the prompt")

    print(f"run: {run.relative_to(ROOT)}")
    for r in rows:
        extra = f" gen={r['gen_seconds']:.0f}s" if "gen_seconds" in r else ""
        print(f"  {r['train_source']:<28} {r['eval_model']:<40} acc={r['accuracy']:.4f}{extra}  {r.get('notes', '')}")
    if problems:
        print("FAIL:\n  " + "\n  ".join(problems))
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
