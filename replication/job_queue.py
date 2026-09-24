#!/usr/bin/env python3
"""GPU job queue for the replication runs (replication/jobs/jobs.tsv).

A job starts only on a GPU that has been nearly empty (< --max-used-mib) for --settle consecutive polls,
so jobs from other users are never disturbed; one job per GPU. A job runs once every job in its `after`
column has passed; if one of those fails, the job is blocked. After a job exits 0, its `check` command
decides pass/fail. Restart-safe: state lives in replication/state/.
"""
from __future__ import annotations

import argparse
import csv
import os
import shlex
import subprocess
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "replication" / "state"
LOGS = ROOT / "replication" / "logs"
PY = str(ROOT / ".venv" / "bin" / "python")


def log(msg: str) -> None:
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOGS / "queue.log", "a") as f:
        f.write(line + "\n")


def gpu_memory_used() -> dict[int, int]:
    out = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=index,memory.used", "--format=csv,noheader,nounits"], text=True
    )
    return {int(i): int(m) for i, m in (line.split(",") for line in out.strip().splitlines())}


def status(name: str) -> str | None:
    for s in ("passed", "failed", "blocked"):
        if (STATE / f"{name}.{s}").exists():
            return s
    return None


def mark(name: str, s: str, detail: str = "") -> None:
    (STATE / f"{name}.{s}").write_text(detail + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", default="replication/jobs/jobs.tsv")
    ap.add_argument("--gpus", default="0,1,2,3")
    ap.add_argument("--max-used-mib", type=int, default=1024)
    ap.add_argument("--settle", type=int, default=3, help="consecutive free polls before a GPU is used")
    ap.add_argument("--poll", type=int, default=20)
    args = ap.parse_args()

    STATE.mkdir(parents=True, exist_ok=True)
    (LOGS / "jobs").mkdir(parents=True, exist_ok=True)
    jobs = list(csv.DictReader(open(ROOT / args.jobs), delimiter="\t"))
    gpus = [int(g) for g in args.gpus.split(",")]
    free_streak = {g: 0 for g in gpus}
    running: dict[str, dict] = {}  # name -> {proc, gpu, start, peak, logf}
    log(f"queue started: {len(jobs)} jobs, gpus={gpus}, pid={os.getpid()}")
    for marker in STATE.glob("*.running"):
        pid = int(marker.read_text().split()[0])
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            log(f"{marker.stem} died without being reaped (pid {pid}); it will be rerun")
            marker.unlink()
            continue
        raise SystemExit(f"{marker.stem} is still running as pid {pid}; stop it or wait before restarting the queue")

    while True:
        mem = gpu_memory_used()
        busy = {r["gpu"] for r in running.values()}
        for g in gpus:
            free_streak[g] = free_streak[g] + 1 if (mem[g] < args.max_used_mib and g not in busy) else 0
        for r in running.values():
            r["peak"] = max(r["peak"], mem[r["gpu"]])

        # Reap finished jobs.
        for name, r in list(running.items()):
            rc = r["proc"].poll()
            if rc is None:
                continue
            r["logf"].close()
            elapsed = (time.time() - r["start"]) / 3600
            detail = f"gpu={r['gpu']} exit={rc} hours={elapsed:.2f} peak_mib={r['peak']}"
            job = next(j for j in jobs if j["name"] == name)
            if rc == 0 and job["check"] != "-":
                chk = subprocess.run([PY, *shlex.split(job["check"])], cwd=ROOT, capture_output=True, text=True)
                (LOGS / "jobs" / f"{name}.check.txt").write_text(chk.stdout + chk.stderr)
                rc = chk.returncode
                detail += f" check={'PASS' if rc == 0 else 'FAIL'}"
            mark(name, "passed" if rc == 0 else "failed", detail)
            (STATE / f"{name}.running").unlink(missing_ok=True)
            log(f"{'PASSED' if rc == 0 else 'FAILED'} {name}: {detail}")
            del running[name]

        # Block jobs whose dependencies failed; launch runnable jobs on settled free GPUs.
        for job in jobs:
            name = job["name"]
            if status(name) or name in running:
                continue
            deps = [] if job["after"] == "-" else job["after"].split(",")
            if any(status(d) in ("failed", "blocked") for d in deps):
                mark(name, "blocked", f"dependency failed: {deps}")
                log(f"BLOCKED {name}: a dependency failed")
                continue
            if not all(status(d) == "passed" for d in deps):
                continue
            ready = [g for g in gpus if free_streak[g] >= args.settle and g not in {r["gpu"] for r in running.values()}]
            if not ready:
                break
            g = ready[0]
            logf = open(LOGS / "jobs" / f"{name}.log", "a")
            env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(g), PYTHONPATH=str(ROOT / "src"),
                       PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True", HF_HUB_OFFLINE="1",
                       HF_DATASETS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
            proc = subprocess.Popen([PY, "scripts/run_pipeline.py", "--config", job["config"]], cwd=ROOT,
                                    stdout=logf, stderr=subprocess.STDOUT, env=env, start_new_session=True)
            running[name] = {"proc": proc, "gpu": g, "start": time.time(), "peak": 0, "logf": logf}
            (STATE / f"{name}.running").write_text(f"{proc.pid} gpu={g}\n")
            free_streak[g] = 0
            log(f"STARTED {name} on GPU {g} (pid {proc.pid})")

        if not running and all(status(j["name"]) for j in jobs):
            log("queue finished: " + ", ".join(f"{j['name']}={status(j['name'])}" for j in jobs))
            return
        time.sleep(args.poll)


if __name__ == "__main__":
    main()
