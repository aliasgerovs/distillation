#!/usr/bin/env python3
"""Aggregate replication runs into replication/RESULTS.md (ours vs. the paper's Table 1).

Reads the newest results.json per (dataset, seed, teacher) under outputs/replication/. Accuracies are
mean +/- standard error over seeds, as in the paper; relative gain is (adaptive - passive) / passive on
the means, which reproduces the paper's column. Time cost is PoE / Standard teacher generation time on
the train and test splits, per seed, averaged. Our timings are on A40s; the paper's on B200/H200/A100.
"""
from __future__ import annotations

import json
import math
import statistics as st
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "replication"
GAMMA = {"gsm8k": 0.65, "math": 0.75}
SEEDS = [123, 456, 789]
# Paper Table 1 (arXiv:2605.22737v3): (mean, sem) in %, relative gain in %, time cost in x.
PAPER = {
    ("gsm8k", "standard"): {"teacher": (87.22, 0.04), "passive": (57.24, 0.25), "adaptive": (56.74, 0.17), "gain": -0.87, "time": 1.00},
    ("gsm8k", "poe"): {"teacher": (81.61, 0.46), "passive": (39.26, 3.33), "adaptive": (49.46, 1.19), "gain": 25.98, "time": 1.64},
    ("math", "standard"): {"teacher": (61.78, 0.33), "passive": (15.17, 0.29), "adaptive": (15.29, 0.40), "gain": 0.75, "time": 1.00},
    ("math", "poe"): {"teacher": (60.07, 0.48), "passive": (9.00, 2.86), "adaptive": (12.92, 1.13), "gain": 43.56, "time": 2.33},
}
# The authors' released MATH seed-456 teacher traces (branch mahdi, math_output_small/): same 5,000 prompts.
AUTHOR_TRACES = {"standard": "train_standard.json", "poe": "train_poe_gamma_0.75.json"}


def latest(dataset: str, seed: int, teacher: str) -> Path | None:
    runs = sorted((OUT / dataset / f"seed{seed}").glob(f"{teacher}_*/results.json"))
    return runs[-1].parent if runs else None


def seed_metrics(dataset: str, seed: int, teacher: str) -> dict | None:
    run = latest(dataset, seed, teacher)
    if run is None:
        return None
    rows = json.loads((run / "results.json").read_text())
    key = "teacher_standard" if teacher == "standard" else f"teacher_poe_gamma_{GAMMA[dataset]}"
    get = {(r["train_source"], r["eval_model"]): r for r in rows}
    need = [("-", f"{key}_test"), (key, "student_naive"), (key, "student_strategic_fd")]
    if any(k not in get for k in need):
        return None
    return {
        "teacher": 100 * get[("-", f"{key}_test")]["accuracy"],
        "passive": 100 * get[(key, "student_naive")]["accuracy"],
        "adaptive": 100 * get[(key, "student_strategic_fd")]["accuracy"],
        "gen_seconds": sum(get[("-", f"{key}_{s}")].get("gen_seconds", math.nan) for s in ("train", "test")),
        "run": str(run.relative_to(ROOT)),
    }


def mean_sem(xs: list[float]) -> tuple[float, float]:
    return st.mean(xs), (st.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else math.nan)


def fmt(ms: tuple[float, float]) -> str:
    m, s = ms
    return f"{m:.2f}" + ("" if math.isnan(s) else f" ± {s:.2f}")


def trace_stats(rows: list[dict]) -> str:
    n = len(rows)
    acc = 100 * sum(r["correct"] for r in rows) / n
    raw = 100 * sum(r["raw_correct"] for r in rows) / n
    words = st.median(len(r["trace"].split()) for r in rows)
    return f"{acc:.2f}% (raw {raw:.2f}%), {words:.0f} words"


def main() -> None:
    lines = ["# Replication results: The Distillation Game (arXiv:2605.22737), Table 1 subset", "",
             "Standard and PoE teachers; passive (`naive`) and adaptive (`strategic_fd`, β_s = 0.5) students.",
             "Cells are ours / paper. Accuracies in %, mean ± standard error over the seeds that have finished.", "",
             "| Dataset | Teacher | Seeds | Teacher acc. | Passive student | Adaptive student | Rel. gain | Time cost |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    summary = {}
    for dataset in ("gsm8k", "math"):
        std_time = {s: m["gen_seconds"] for s in SEEDS if (m := seed_metrics(dataset, s, "standard"))}
        for teacher in ("standard", "poe"):
            per_seed = {s: m for s in SEEDS if (m := seed_metrics(dataset, s, teacher))}
            p = PAPER[(dataset, teacher)]
            label = "Standard" if teacher == "standard" else f"PoE (γ = {GAMMA[dataset]})"
            if not per_seed:
                lines.append(f"| {dataset.upper()} | {label} | 0 | – / {fmt(p['teacher'])} | – / {fmt(p['passive'])} | "
                             f"– / {fmt(p['adaptive'])} | – / {p['gain']:.2f}% | – / {p['time']:.2f}× |")
                continue
            agg = {k: mean_sem([m[k] for m in per_seed.values()]) for k in ("teacher", "passive", "adaptive")}
            gain = 100 * (agg["adaptive"][0] - agg["passive"][0]) / agg["passive"][0]
            ratios = [m["gen_seconds"] / std_time[s] for s, m in per_seed.items() if s in std_time]
            time_cost = f"{st.mean(ratios):.2f}×" if ratios else "–"
            lines.append(f"| {dataset.upper()} | {label} | {','.join(map(str, per_seed))} | {fmt(agg['teacher'])} / {fmt(p['teacher'])} | "
                         f"{fmt(agg['passive'])} / {fmt(p['passive'])} | {fmt(agg['adaptive'])} / {fmt(p['adaptive'])} | "
                         f"{gain:.2f}% / {p['gain']:.2f}% | {time_cost} / {p['time']:.2f}× |")
            summary[f"{dataset}/{teacher}"] = {"per_seed": per_seed, "aggregate": agg, "rel_gain": gain, "time_cost_ratios": ratios}

    lines += ["", "## Validation against the authors' released MATH seed-456 teacher traces", "",
              "Same 5,000 train prompts in the same order: answer-forced accuracy (raw accuracy), median words per trace.",
              "Paired: problems only we / only they solved; McNemar z = (only ours − only theirs) / √(sum),",
              "|z| < 2 means no detectable difference beyond sampling noise.", "",
              "| Teacher | Authors | Ours | Only ours / only theirs | McNemar z |", "| --- | --- | --- | --- | --- |"]
    for teacher, fname in AUTHOR_TRACES.items():
        theirs = json.loads(subprocess.check_output(["git", "show", f"origin/mahdi:math_output_small/{fname}"], cwd=ROOT))
        # Teacher traces are written long before results.json, so look for the file itself.
        found = sorted((OUT / "math" / "seed456").glob(f"{teacher}_*/teacher/{fname}"))
        ours_path = found[-1] if found else None
        if ours_path:
            ours_rows = json.loads(ours_path.read_text())
            b = sum(o["correct"] and not t["correct"] for o, t in zip(ours_rows, theirs))
            c = sum(t["correct"] and not o["correct"] for o, t in zip(ours_rows, theirs))
            z = (b - c) / math.sqrt(b + c) if b + c else 0.0
            lines.append(f"| {teacher} | {trace_stats(theirs)} | {trace_stats(ours_rows)} | {b} / {c} | {z:+.2f} |")
        else:
            lines.append(f"| {teacher} | {trace_stats(theirs)} | not run yet | – | – |")

    (ROOT / "replication" / "RESULTS.md").write_text("\n".join(lines) + "\n")
    (ROOT / "replication" / "results_summary.json").write_text(json.dumps(summary, indent=2))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
