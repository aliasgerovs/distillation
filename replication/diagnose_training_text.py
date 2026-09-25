#!/usr/bin/env python3
"""Diagnostic: retrain a passive student on a finished run's teacher traces with a chosen training text.

The authors' two branches build the student's training text differently:
  main   (official release; what all our runs use): the trace plus the answer-forced "**Final Answer**" line
  mahdi  (their other branch): the raw trace only
Everything else (traces, hyperparameters, seed, evaluation) is the pipeline's own code, unchanged.

Usage: diagnose_training_text.py <job config> <main|mahdi>   (set CUDA_VISIBLE_DEVICES)
Writes outputs/diagnostics/training_text/<job>_<variant>/results.json.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import torch
import yaml

import clean_sweep.train.distill as distill
from clean_sweep.config import FullConfig
from clean_sweep.data import format_prompt_gsm8k, format_prompt_math, load_dataset_splits
from clean_sweep.generation import generate_teacher_traces
from clean_sweep.utils import set_seed, write_json

ROOT = Path(__file__).resolve().parent.parent
VARIANTS = {
    "main": distill._trace_text_for_training,
    "mahdi": lambda ex: ex.get("af_trace", ex.get("reasoning_text", ex.get("trace", ""))),
}

job_config, variant = sys.argv[1], sys.argv[2]
cfg = FullConfig.from_yaml(job_config)
teacher_file = "train_standard.json" if cfg.teachers.standard else f"train_poe_gamma_{cfg.teachers.poe_gammas[0]}.json"
runs = sorted((ROOT / cfg.run.output_dir).glob(f"{cfg.run.run_name}_*/results.json"))
source = runs[-1].parent
traces = json.loads((source / "teacher" / teacher_file).read_text())
out_dir = ROOT / "outputs" / "diagnostics" / "training_text" / f"{Path(job_config).stem}_{variant}"
print(f"source run: {source.relative_to(ROOT)} | traces: {teacher_file} (n={len(traces)}) | variant: {variant}", flush=True)

distill._trace_text_for_training = VARIANTS[variant]
appended = sum(VARIANTS[variant](r) != r["trace"] for r in traces)
print(f"training texts that differ from the raw trace: {appended}/{len(traces)}", flush=True)

device = torch.device("cuda")
set_seed(cfg.run.seed)
with tempfile.TemporaryDirectory() as tmp:
    _, model, tokenizer = distill.run_distill(cfg=cfg, train_traces=traces, holdout_traces=[], output_dir=tmp,
                                              device=device, mode="naive", beta_s=1.0)
splits = load_dataset_splits(cfg.data.dataset_name, seed=cfg.run.seed, train_size=cfg.data.train_size,
                             holdout_size=cfg.data.holdout_size, test_size=cfg.data.test_size)
fmt = format_prompt_gsm8k if cfg.data.dataset_name == "gsm8k" else format_prompt_math
set_seed(cfg.run.seed)
rows, _ = generate_teacher_traces(cfg=cfg, dataset=splits["test"], format_prompt=fmt, method_name="standard",
                                  device=device, model=model, tokenizer=tokenizer)
acc = sum(r["correct"] for r in rows) / len(rows)
original = {r["eval_model"]: r["accuracy"] for r in json.loads((source / "results.json").read_text())
            if r["eval_model"] == "student_naive"}
result = {"job": Path(job_config).stem, "variant": variant, "teacher_traces": teacher_file,
          "source_run": str(source.relative_to(ROOT)), "passive_accuracy": acc,
          "original_passive_accuracy_main_variant": original.get("student_naive"),
          "n_test": len(rows), "training_texts_differing_from_raw_trace": appended}
write_json(result, out_dir / "results.json")
write_json(rows, out_dir / "test_outputs.json")
print(json.dumps(result, indent=2), flush=True)
