#!/usr/bin/env python3
"""Write one run_pipeline.py config per job, plus the queue's job list (replication/jobs/jobs.tsv).

Scope: the Standard teacher and the PoE teacher at the paper's Table 1 operating points, each distilled
into a passive (naive) and an adaptive (strategic_fd) student, on GSM8K and MATH, over the paper's seeds.
"""
from __future__ import annotations

import copy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
JOBS_DIR = ROOT / "replication" / "jobs"
SEEDS = [456, 123, 789]  # paper: 123, 456, 789. 456 first: the authors released their MATH seed-456 traces.

# Split sizes from Appendix C.1. The GSM8K loader caps holdout at 2,235 (the train set has 7,473
# problems) and test at 1,209 (GSM8K-Platinum's size). PoE gammas are the Table 1 operating points.
DATASETS = {
    "math": {"sizes": (5000, 2500, 5000), "batch_size": 64, "gamma": 0.75},
    "gsm8k": {"sizes": (5238, 2246, 1319), "batch_size": 128, "gamma": 0.65},
}
SMOKE = {
    "gsm8k": {"seed": 123, "sizes": (128, 24, 128)},
    "math": {"seed": 456, "sizes": (64, 12, 64)},
}


def make_config(base: dict, *, dataset: str, seed: int, sizes: tuple[int, int, int], teacher: str,
                output_dir: str, epochs: int | None = None) -> dict:
    cfg = copy.deepcopy(base)
    spec = DATASETS[dataset]
    cfg["run"].update(seed=seed, output_dir=output_dir, run_name=teacher)
    cfg["data"].update(dataset_name=dataset, train_size=sizes[0], holdout_size=sizes[1], test_size=sizes[2])
    cfg["generation"]["batch_size"] = spec["batch_size"]
    if teacher == "standard":
        cfg["teachers"].update(standard=True, poe_gammas=[])
    elif teacher == "poe":
        cfg["teachers"].update(standard=False, poe_gammas=[spec["gamma"]])
    else:  # smoke: both teachers in one run
        cfg["teachers"].update(standard=True, poe_gammas=[spec["gamma"]])
    if epochs is not None:
        cfg["distill"]["num_epochs"] = epochs
    return cfg


def main() -> None:
    base = yaml.safe_load((ROOT / "replication" / "configs" / "paper_base.yaml").read_text())
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    smoke_names = []
    for dataset, s in SMOKE.items():
        name = f"smoke_{dataset}"
        cfg = make_config(base, dataset=dataset, seed=s["seed"], sizes=s["sizes"], teacher="smoke",
                          output_dir="outputs/replication/smoke", epochs=1)
        cfg["run"]["run_name"] = name
        path = JOBS_DIR / f"{name}.yaml"
        path.write_text(yaml.safe_dump(cfg, sort_keys=False))
        rows.append((name, path, "-", f"replication/check_run.py {path.relative_to(ROOT)}"))
        smoke_names.append(name)

    for dataset, spec in DATASETS.items():
        for seed in SEEDS:
            for teacher in ("standard", "poe"):
                name = f"{dataset}_s{seed}_{teacher}"
                cfg = make_config(base, dataset=dataset, seed=seed, sizes=spec["sizes"], teacher=teacher,
                                  output_dir=f"outputs/replication/{dataset}/seed{seed}")
                path = JOBS_DIR / f"{name}.yaml"
                path.write_text(yaml.safe_dump(cfg, sort_keys=False))
                rows.append((name, path, ",".join(smoke_names), f"replication/check_run.py {path.relative_to(ROOT)}"))

    with open(JOBS_DIR / "jobs.tsv", "w") as f:
        f.write("name\tconfig\tafter\tcheck\n")
        for name, path, after, check in rows:
            f.write(f"{name}\t{path.relative_to(ROOT)}\t{after}\t{check}\n")
    print(f"wrote {len(rows)} jobs to {JOBS_DIR / 'jobs.tsv'}")


if __name__ == "__main__":
    main()
