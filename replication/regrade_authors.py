#!/usr/bin/env python3
"""Re-grade the authors' released MATH seed-456 teacher traces with our pinned grader.

Their rows store the trace and the answer-forced tail but not the full decoded text, so the texts are
rebuilt as the pipeline builds them (rendered prompt, trace, answer-forcing suffix and tail). The gold solutions
come from our seed-456 split, which matches theirs prompt for prompt. Agreement near 100% means our
math-verify version labels answers the way theirs did.
"""
from __future__ import annotations

import sys

from types import SimpleNamespace

from transformers import AutoConfig, AutoTokenizer, GenerationConfig

from clean_sweep.data import format_prompt_math, load_dataset_splits
from clean_sweep.eval import check_trace_correctness
from clean_sweep.generation.core import align_tokenizer_to_model, ensure_chat_template

from authors_traces import load_authors_json

TEACHER = "/scratch/aliasgarov/distillation-game/models/DeepSeek-R1-Distill-Qwen-7B"
tok = ensure_chat_template(AutoTokenizer.from_pretrained(TEACHER, trust_remote_code=True, padding_side="left"))
tok = align_tokenizer_to_model(tok, SimpleNamespace(config=AutoConfig.from_pretrained(TEACHER),
                                                    generation_config=GenerationConfig.from_pretrained(TEACHER)))


def rendered_prompt(problem: str) -> str:
    """The prompt part of full_text, as generate_teacher_traces decodes it (pad/EOS strings removed)."""
    ids = tok.apply_chat_template(format_prompt_math(problem), add_generation_prompt=True, truncation=True, max_length=512)
    return tok.decode(ids, skip_special_tokens=False).replace(tok.pad_token, "")


split = load_dataset_splits("math", seed=456, train_size=5000, holdout_size=2500, test_size=5000)["train"]
for fname in sys.argv[1:] or ["train_standard.json", "train_poe_gamma_0.75.json"]:
    rows = load_authors_json(f"math_output_small/{fname}")
    agree_af = agree_raw = 0
    flips = []
    for row, ex in zip(rows, split):
        assert row["prompt"].strip() == ex["problem"].strip()
        raw_text = rendered_prompt(ex["problem"]) + row["trace"]
        af_text = raw_text + ("" if "</think>" in row["trace"] else "\n</think>") + "\n\n" + (row["af_final_answer_only"] or "")
        ours_raw = check_trace_correctness(raw_text, ex["solution"])["correct"]
        ours_af = check_trace_correctness(af_text, ex["solution"])["correct"]
        agree_raw += ours_raw == row["raw_correct"]
        agree_af += ours_af == row["af_correct"]
        if ours_af != row["af_correct"]:
            flips.append((row["example_id"], row["af_correct"], ours_af, (row["af_final_answer_only"] or "")[:60]))
    n = len(rows)
    print(f"{fname}: answer-forced agreement {agree_af}/{n} ({100 * agree_af / n:.2f}%), raw agreement {agree_raw}/{n} ({100 * agree_raw / n:.2f}%)")
    for f in flips[:5]:
        print("   disagreement:", f)
