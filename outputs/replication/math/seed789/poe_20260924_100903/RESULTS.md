# Results

## Comparison Matrix

| Teacher | Teacher Accuracy | student_naive | student_strategic_fd (beta_s=0.5) |
| --- | --- | --- | --- |
| teacher_poe_gamma_0.75 | 0.6030 | 0.1266 | 0.1482<br><sub>mean_a=-0.0989, frac_mass_top20=0.2112</sub> |

Model Context:
- Dataset: `math`
- Teacher model: `/scratch/aliasgarov/distillation-game/models/DeepSeek-R1-Distill-Qwen-7B`
- Student model: `/scratch/aliasgarov/distillation-game/models/Llama-3.2-3B`
