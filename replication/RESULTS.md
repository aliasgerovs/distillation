# Replication results: The Distillation Game (arXiv:2605.22737), Table 1 subset

Standard and PoE teachers; passive (`naive`) and adaptive (`strategic_fd`, β_s = 0.5) students.
Cells are ours / paper. Accuracies in %, mean ± standard error over the seeds that have finished.

| Dataset | Teacher | Seeds | Teacher acc. | Passive student | Adaptive student | Rel. gain | Time cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GSM8K | Standard | 0 | – / 87.22 ± 0.04 | – / 57.24 ± 0.25 | – / 56.74 ± 0.17 | – / -0.87% | – / 1.00× |
| GSM8K | PoE (γ = 0.65) | 0 | – / 81.61 ± 0.46 | – / 39.26 ± 3.33 | – / 49.46 ± 1.19 | – / 25.98% | – / 1.64× |
| MATH | Standard | 123,456 | 62.64 ± 0.38 / 61.78 ± 0.33 | 15.27 ± 0.25 / 15.17 ± 0.29 | 15.51 ± 0.19 / 15.29 ± 0.40 | 1.57% / 0.75% | 1.00× / 1.00× |
| MATH | PoE (γ = 0.75) | 123,456 | 61.10 ± 0.40 / 60.07 ± 0.48 | 12.28 ± 0.14 / 9.00 ± 2.86 | 14.94 ± 1.16 / 12.92 ± 1.13 | 21.66% / 43.56% | 1.51× / 2.33× |

## Validation against the authors' released MATH seed-456 teacher traces

Same 5,000 train prompts in the same order: answer-forced accuracy (raw accuracy), median words per trace.
Paired: problems only we / only they solved; McNemar z = (only ours − only theirs) / √(sum),
|z| < 2 means no detectable difference beyond sampling noise.

| Teacher | Authors | Ours | Only ours / only theirs | McNemar z |
| --- | --- | --- | --- | --- |
| standard | 61.16% (raw 21.40%), 611 words | 62.28% (raw 21.94%), 609 words | 405 / 349 | +2.04 |
| poe | 61.16% (raw 52.38%), 253 words | 61.56% (raw 53.10%), 251 words | 511 / 491 | +0.63 |
