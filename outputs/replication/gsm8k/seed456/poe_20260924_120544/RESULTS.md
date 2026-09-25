# Results

## Comparison Matrix

| Teacher | Teacher Accuracy | student_naive | student_strategic_fd (beta_s=0.5) |
| --- | --- | --- | --- |
| teacher_poe_gamma_0.65 | 0.8147 | 0.4913 | 0.5236<br><sub>mean_a=-0.3670, frac_mass_top20=0.2329</sub> |

Model Context:
- Dataset: `gsm8k`
- Teacher model: `/scratch/aliasgarov/distillation-game/models/DeepSeek-R1-Distill-Qwen-7B`
- Student model: `/scratch/aliasgarov/distillation-game/models/Llama-3.2-3B`
