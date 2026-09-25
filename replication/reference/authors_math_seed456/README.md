# Reference: the authors' MATH seed-456 teacher traces

`train_standard.json` and `train_poe_gamma_0.75.json` are the Standard and PoE (γ = 0.75) teacher traces the
paper's authors released for MATH seed 456 (5,000 train prompts), copied unchanged from
`math_output_small/` on the `mahdi` branch of github.com/ysfalh/distillation-game (commit `c19459d`).

`aggregate.py` compares our teachers with these on the same prompts, and `regrade_authors.py` re-grades
them with our grader.
