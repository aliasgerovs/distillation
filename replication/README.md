# Replicating *The Distillation Game* (arXiv:2605.22737v3)

Original code: github.com/ysfalh/distillation-game, `main` @ `671704e`; `git diff 671704e` (or
`code_changes_vs_upstream.patch`) shows exactly what we changed in the pipeline.
Paper: [arXiv:2605.22737v3](https://arxiv.org/abs/2605.22737v3) (a local copy in `paper/` is not committed).

## Conclusions (all 12 runs, 3 seeds each; full table in `RESULTS.md`)

| Mean ± s.e. over 3 seeds (ours / paper) | Teacher acc. | Passive student | Adaptive student | Rel. gain |
| --- | --- | --- | --- | --- |
| GSM8K Standard | 87.5 / 87.2 | 58.8 / 57.2 | 58.8 / 56.7 | +0% / −1% |
| GSM8K PoE (γ = 0.65) | 81.0 / 81.6 | **49.6 ± 0.3 / 39.3 ± 3.3** | 51.6 / 49.5 | +4% / +26% |
| MATH Standard | 62.9 / 61.8 | 14.8 / 15.2 | 15.3 / 15.3 | +3% / +1% |
| MATH PoE (γ = 0.75) | 60.8 / 60.1 | **12.4 ± 0.2 / 9.0 ± 2.9** | 14.9 / 12.9 | +20% / +44% |

- **Replicated:** both teachers (and against the authors' own released traces on the same prompts), every
  Standard-teacher student, PoE's effect on traces (about 40–60% shorter at almost no accuracy cost), and the
  direction of the paper's main claim: on all 6 PoE runs the adaptive student beats the passive one, and
  adaptive reweighting does nothing against the undefended teacher.
- **Not replicated in size:** our passive students trained on PoE traces are much stronger than the paper's
  (+10 points on GSM8K, +3.4 on MATH, with small seed-to-seed spread), so PoE blocks about half as much
  leakage under passive evaluation and the passive–adaptive gap is several times smaller.
- **Partly explained:** the authors' other branch trains students on the raw trace instead of trace + forced
  answer; that lowers only the PoE student (by 2.7 points on GSM8K seed 456; see the diagnostic below).
- **Time cost** (PoE vs Standard generation): 1.49× GSM8K, 1.52× MATH on A40s (paper 1.64×, 2.33× on
  B200/H200/A100).

## Scope

The **Standard** (undefended) teacher and the paper's **PoE** teacher at its Table 1 operating points
(γ = 0.65 on GSM8K, γ = 0.75 on MATH). Each teacher is distilled into a **passive** (`naive`) and an
**adaptive** (`strategic_fd`, β_s = 0.5) student. Both datasets, seeds 123/456/789: 12 runs plus 2 smoke tests.
Not in scope: ADS, the Figure 3 λ/γ sweeps, Figure 4 (Claude-judged trace quality), Figure 5 (frontier-model traces).

Models: teacher DeepSeek-R1-Distill-Qwen-7B, proxy Qwen2.5-3B, student Llama-3.2-3B. All hyperparameters
are the paper's (Section 4.1, Appendix C.1); see `configs/paper_base.yaml`.

## Layout

| Path | What |
| --- | --- |
| `setup_env.sh` | Builds `../.venv` with pinned versions (upstream pins nothing) |
| `configs/paper_base.yaml` | Paper settings; `make_jobs.py` derives one config per job into `jobs/` |
| `job_queue.py` | Starts jobs only on idle GPUs (< 1 GiB used for 3 polls), one per GPU; smoke tests gate the rest |
| `check_run.py` | Per-run sanity check: all rows present, no prompt text in traces, plausible teacher accuracy |
| `memory_probe.py`, `train_memory_probe.py` | Peak-memory probes for the heaviest generation batch and the longest student-training texts |
| `reference/authors_math_seed456/` | The authors' released MATH seed-456 Standard and PoE teacher traces (30 MB), used by `aggregate.py` and `regrade_authors.py` |
| `aggregate.py` | Writes `RESULTS.md`: ours vs. Table 1, plus a check against the authors' own seed-456 MATH traces |
| `models/Llama-3.2-3B/` | Student weights (symlinked from the unsloth mirror) with Meta's config semantics |
| `/scratch/aliasgarov/distillation-game/models/` | Local NVMe copies of teacher, proxy and student that the runs load (SHA-256 checked against the HF cache). Loading from the NFS cache ran at ~30 MB/s per process. If `/scratch` is wiped, re-copy from `~/.cache/huggingface` |
| `logs/queue.log`, `logs/jobs/` | Queue events and per-job logs; `state/` holds pass/fail markers |
| `../outputs/replication/` | Run outputs. Each run's small files (results, config snapshot, manifest, sample traces) are committed; the bulk trace JSONs (~100 MB per run) stay on the machine |

```bash
tail -f replication/logs/queue.log            # job starts, pass/fail, peak GPU memory
ls replication/state/                          # <job>.running / .passed / .failed / .blocked
.venv/bin/python replication/aggregate.py      # refresh RESULTS.md at any time
bash replication/stop_queue.sh                 # stop the queue and its jobs, freeing the GPUs
# restart the queue (skips finished jobs, reruns interrupted ones):
setsid nohup .venv/bin/python replication/job_queue.py > replication/logs/queue.stdout 2>&1 < /dev/null &
```

## Deviations and why they should not move the results

| # | Change | Effect on results |
| --- | --- | --- |
| 1 | **Hardware:** 46 GB A40s instead of the paper's B200/H200/A100. Memory-only code changes: build the ±ε ADS proxies with 2 copies instead of 3, free proxy KV caches before answer forcing (both ported verbatim from the authors' `mahdi` branch), release the proxy after its gradients and the teacher before the student stage | None: identical values, less memory |
| 2 | GSM8K generation batch 128 instead of 240 (MATH keeps 64) | Different random stream only; prompts are padded across the whole split, not per batch |
| 3 | Activation checkpointing while computing holdout gradients (the adaptive student's g_s) | None: same forward pass recomputed; the trainer enables it right after anyway |
| 4 | Proxy gradients skipped when no ADS teacher is configured | None: only ADS reads them, and every later stage re-seeds |
| 5 | **Student weights** from `unsloth/Llama-3.2-3B` (your HF account lacks Meta access). unsloth added `pad_token_id=128004`; removed it again so the pipeline pads with EOS as it would with Meta's files. This matters: trl appends `<|end_of_text|>` to every training text, and the collator masks tokens equal to the pad id, so with Meta's config the student never learns to emit it (and always generates to the 1,024-token cap); with unsloth's pad id it would learn to stop. Shard sizes match Meta's byte-for-byte; hashes can't be compared until Meta grants access | None expected |
| 6 | Upstream bug: `data/__init__.py` imports two modules that don't exist. Applied the authors' own fix from `mahdi` | None |
| 7 | `results.json` rows gain a `gen_seconds` field for the Time Cost column | None; A40 timings are not comparable in absolute terms |
| 8 | Dependency versions pinned (torch 2.8.0, transformers 4.56.2, trl 0.23.1, peft 0.17.1, datasets 4.1.1, flash-attn 2.8.3); the authors' versions are unknown | Possible small numeric differences |

Things that are *not* deviations but matter for comparing numbers:

- **Split sizes.** MATH is 5,000/2,500/5,000 as in Appendix C.1 (upstream `configs/math.yaml` says 2000/1000/1000).
  Our MATH seed-456 train split is identical, prompt for prompt, to the authors' released traces. GSM8K
  resolves to 5,238/2,235/1,209: the train set has only 7,473 problems and the test set is GSM8K-Platinum.
- **Which training text.** `main` trains students on the trace *plus* the answer-forced `\boxed{}` line
  (`_trace_text_for_training`, added in an April 16 cleanup); the authors' `mahdi` branch trains on the raw
  trace only. The paper doesn't say which produced Table 1. We follow `main`, the official release.
- **Student training text.** trl 0.23 keeps the `text` column, so the pipeline's collator does the tokenizing, as designed. Training sequences start with two BOS tokens (the collator re-tokenizes already-formatted text); eval prompts have one. Checked with a tiny model on CPU.
- **Pipeline quirks kept as-is.** The teacher's config sets BOS to its EOS token, so teacher prompts start with
  `<｜end▁of▁sentence｜>`; the Llama-3.2 chat template writes the current date into every student prompt.
  The authors' runs had both.

## GPU memory (measured on an A40, worst-case shapes)

Prompts are padded to the longest in the whole split, so each generation batch has the same shape as the probe.

| Stage | Peak allocated | Peak reserved |
| --- | --- | --- |
| GSM8K PoE teacher, batch 128, prompts padded to 267 tokens (seed 789, the longest) | 35.5 GiB | 38.0 GiB |
| GSM8K student eval, batch 128 | 26.3 GiB | 29.4 GiB |
| MATH PoE teacher, batch 64, prompts padded to 512 | 32.3 GiB | 32.7 GiB |
| MATH student eval, batch 64 | 18.2 GiB | 18.9 GiB |
| MATH adaptive student on the 12 longest training texts (holdout grads, weights, training) | 39.6 GiB | 40.1 GiB |
| MATH passive student on the same texts | 27.2 GiB | 33.1 GiB |

Standard-teacher generation needs less than PoE (no proxy). About 1% of MATH prompts (21 to 56 per
split) exceed `max_prompt_tokens: 512` and are truncated, losing the assistant tag. The authors'
pipeline does the same. No split *starts* with such a prompt, which matters because answer forcing
reads the chat markers from the first trace and raises if they are missing.

## Fidelity checks (done before and during the runs)

| Check | Result |
| --- | --- |
| Our MATH seed-456 train split vs. the authors' released traces (`reference/authors_math_seed456/`) | Identical, all 5,000 prompts in order |
| Re-grading the authors' released MATH traces with our grader (`regrade_authors.py`; texts rebuilt with the exact rendered prompt) | Answer-forced correctness agrees on 4,996/5,000 Standard and 4,998/5,000 PoE traces; the rest are ours = wrong, theirs = right |
| Our Standard teacher vs. the authors' on the same 5,000 MATH seed-456 train prompts | 62.28% vs 61.16% answer-forced, 21.94% vs 21.40% raw, median 609 vs 611 words; paired: 405 solved only by ours, 349 only by theirs (McNemar z = +2.0, borderline) |
| Our PoE (γ = 0.75) teacher vs. the authors' on the same prompts | 61.56% vs 61.16% answer-forced, 53.10% vs 52.38% raw, median 251 vs 253 words; paired: 511 only ours, 491 only theirs (McNemar z = +0.6) |
| Holdout traces generated independently by the Standard and PoE jobs of the same seed | Byte-identical (seeds 123 and 456), so splitting the pipeline one job per teacher changes nothing |
| Smoke tests (GSM8K 128 / MATH 64 problems, 1 epoch) | Both pass end to end; GSM8K teacher 86.7% Standard / 79.7% PoE on 128 test problems (paper: 87.2 / 81.6) |

## Diagnostic: the student's training text (GSM8K seed 456, passive students)

Our PoE passive students are much stronger than the paper's (GSM8K 49.6 vs 39.3), while teachers and Standard
students match. The authors' two branches build the student's training text differently: `main` (the official
release, which our runs use) appends the answer-forced `**Final Answer**` line to every trace; their `mahdi`
branch trains on the raw trace. `diagnose_training_text.py` retrains the passive student on the same traces with
the raw-trace text, changing nothing else.

| Teacher traces | `main` text (our runs) | Raw trace (`mahdi`) | Solved only by one / only by the other | Paper |
| --- | --- | --- | --- | --- |
| Standard | 58.23% | 58.23% | 163 / 163 (different outputs, no net effect) | 57.24 ± 0.25 |
| PoE (γ = 0.65) | 49.13% | 46.40% | 188 / 155 (McNemar z = 1.8) | 39.26 ± 3.33 |

The difference only matters for PoE: PoE traces rarely finish their thinking (15% contain `</think>` vs 90% for
Standard), and 19% of them reach the right answer only through answer forcing (11% for Standard). It accounts
for about 3 of the 10-point GSM8K gap on this seed; the rest is unexplained.
