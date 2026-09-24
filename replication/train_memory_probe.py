#!/usr/bin/env python3
"""Peak GPU memory of the student stage on its worst case: the longest MATH training texts.

Uses the authors' released MATH seed-456 standard traces (branch mahdi) and runs run_distill on the 12
longest (prompt + trace + forced answer) examples, first adaptive (holdout gradients, per-trace weights,
weighted training) and then passive. Usage: train_memory_probe.py <job config>, with CUDA_VISIBLE_DEVICES set.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile

import torch

from clean_sweep.config import FullConfig
from clean_sweep.train import run_distill
from clean_sweep.train.distill import _trace_text_for_training
from transformers import AutoTokenizer

cfg = FullConfig.from_yaml(sys.argv[1])
cfg.distill.num_epochs = 1
rows = json.loads(subprocess.check_output(["git", "show", "origin/mahdi:math_output_small/train_standard.json"]))
tok = AutoTokenizer.from_pretrained(cfg.model.student_tokenizer)
for r in rows:
    r["problem"] = r["prompt"]
    r["_len"] = len(tok(r["problem"] + _trace_text_for_training(r))["input_ids"])
rows.sort(key=lambda r: r["_len"], reverse=True)
longest = rows[:12]
print("longest training texts (tokens, before chat markup):", [r["_len"] for r in longest], flush=True)

for mode in ("strategic_fd", "naive"):
    torch.cuda.reset_peak_memory_stats()
    with tempfile.TemporaryDirectory() as d:
        stats, model, _ = run_distill(cfg=cfg, train_traces=longest, holdout_traces=longest[:6], output_dir=d,
                                      device=torch.device("cuda"), mode=mode, beta_s=0.5)
    print(f"{mode}: peak allocated {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB | "
          f"peak reserved {torch.cuda.max_memory_reserved() / 2**30:.1f} GiB | stats {stats}", flush=True)
    del model
    torch.cuda.empty_cache()
