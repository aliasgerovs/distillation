# Replication results: The Distillation Game (arXiv:2605.22737), Table 1 subset

Standard and PoE teachers; passive (`naive`) and adaptive (`strategic_fd`, β_s = 0.5) students.
Cells are ours / paper. Accuracies in %, mean ± standard error over the seeds that have finished.

| Dataset | Teacher | Seeds | Teacher acc. | Passive student | Adaptive student | Rel. gain | Time cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GSM8K | Standard | 123,456 | 87.14 ± 0.37 / 87.22 ± 0.04 | 58.52 ± 0.29 / 57.24 ± 0.25 | 58.68 ± 0.21 / 56.74 ± 0.17 | 0.28% / -0.87% | 1.00× / 1.00× |
| GSM8K | PoE (γ = 0.65) | 123,456 | 81.76 ± 0.29 / 81.61 ± 0.46 | 49.59 ± 0.45 / 39.26 ± 3.33 | 51.61 ± 0.74 / 49.46 ± 1.19 | 4.09% / 25.98% | 1.49× / 1.64× |
| MATH | Standard | 123,456,789 | 62.89 ± 0.34 / 61.78 ± 0.33 | 14.78 ± 0.51 / 15.17 ± 0.29 | 15.26 ± 0.27 / 15.29 ± 0.40 | 3.25% / 0.75% | 1.00× / 1.00× |
| MATH | PoE (γ = 0.75) | 123,456,789 | 60.83 ± 0.35 / 60.07 ± 0.48 | 12.41 ± 0.15 / 9.00 ± 2.86 | 14.90 ± 0.67 / 12.92 ± 1.13 | 20.10% / 43.56% | 1.52× / 2.33× |

## Validation against the authors' released MATH seed-456 teacher traces

Same 5,000 train prompts in the same order: answer-forced accuracy (raw accuracy), median words per trace.
Paired: problems only we / only they solved; McNemar z = (only ours − only theirs) / √(sum),
|z| < 2 means no detectable difference beyond sampling noise.

| Teacher | Authors | Ours | Only ours / only theirs | McNemar z |
| --- | --- | --- | --- | --- |
| standard | 61.16% (raw 21.40%), 611 words | 62.28% (raw 21.94%), 609 words | 405 / 349 | +2.04 |
| poe | 61.16% (raw 52.38%), 253 words | 61.56% (raw 53.10%), 251 words | 511 / 491 | +0.63 |
