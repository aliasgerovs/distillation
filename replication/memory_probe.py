#!/usr/bin/env python3
"""Measure peak GPU memory for a job's heaviest generation batches under the real shapes.

Runs one full PoE teacher batch (max_new_tokens as configured, plus answer forcing) on a subset that
contains the split's longest prompt, so padding matches the full run, then one student-eval batch with
the untrained LoRA student. Usage: memory_probe.py <job config> (run with CUDA_VISIBLE_DEVICES set).
"""
from __future__ import annotations

import sys

import torch

from clean_sweep.config import FullConfig
from clean_sweep.data import format_prompt_gsm8k, format_prompt_math, load_dataset_splits
from clean_sweep.generation import generate_teacher_traces, load_model_and_tokenizer
from clean_sweep.train.distill import load_student_model


def heaviest_batch(ds, tok, fmt, n):
    lengths = [len(tok.apply_chat_template(fmt(p), add_generation_prompt=True, truncation=True, max_length=512)) for p in ds["problem"]]
    longest = max(range(len(lengths)), key=lengths.__getitem__)
    # Longest prompt last: answer forcing reads the chat markers from the first trace, as in the real run.
    idx = [i for i in range(len(ds)) if i != longest][: n - 1] + [longest]
    return ds.select(idx), lengths[longest]


def report(label: str) -> None:
    gib = 2**30
    print(f"{label}: peak allocated {torch.cuda.max_memory_allocated() / gib:.1f} GiB | "
          f"peak reserved {torch.cuda.max_memory_reserved() / gib:.1f} GiB", flush=True)
    torch.cuda.reset_peak_memory_stats()


cfg = FullConfig.from_yaml(sys.argv[1])
fmt = format_prompt_gsm8k if cfg.data.dataset_name == "gsm8k" else format_prompt_math
B = cfg.generation.batch_size
splits = load_dataset_splits(cfg.data.dataset_name, seed=cfg.run.seed, train_size=cfg.data.train_size,
                             holdout_size=cfg.data.holdout_size, test_size=cfg.data.test_size)
device = torch.device("cuda")

teacher, ttok = load_model_and_tokenizer(cfg.model.teacher, cfg.model.tokenizer, cfg, device)
batch, L = heaviest_batch(splits["train"], ttok, fmt, B)
print(f"{cfg.data.dataset_name}: batch={B}, padded prompt length={L}", flush=True)
torch.cuda.reset_peak_memory_stats()
rows, _ = generate_teacher_traces(cfg=cfg, dataset=batch, format_prompt=fmt, method_name="poe", device=device,
                                  model=teacher, tokenizer=ttok, gamma=cfg.teachers.poe_gammas[0])
report(f"PoE teacher (gamma={cfg.teachers.poe_gammas[0]}), 1 batch")
del teacher
torch.cuda.empty_cache()

student, stok = load_student_model(cfg, device)
batch, L = heaviest_batch(splits["test"], stok, fmt, B)
torch.cuda.reset_peak_memory_stats()
generate_teacher_traces(cfg=cfg, dataset=batch, format_prompt=fmt, method_name="standard", device=device,
                        model=student, tokenizer=stok)
report(f"student eval (LoRA, untrained), 1 batch, padded prompt length={L}")
