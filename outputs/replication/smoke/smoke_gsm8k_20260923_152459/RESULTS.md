# Results

## Comparison Matrix

| Teacher | Teacher Accuracy | student_naive | student_strategic_fd (beta_s=0.5) |
| --- | --- | --- | --- |
| teacher_poe_gamma_0.65 | 0.7969 | 0.1953 | 0.1094<br><sub>mean_a=-0.3838, frac_mass_top20=0.2266</sub> |
| teacher_standard | 0.8672 | 0.1250 | 0.1016<br><sub>mean_a=-0.3021, frac_mass_top20=0.2256</sub> |

Model Context:
- Dataset: `gsm8k`
- Teacher model: `/scratch/aliasgarov/distillation-game/models/DeepSeek-R1-Distill-Qwen-7B`
- Student model: `/scratch/aliasgarov/distillation-game/models/Llama-3.2-3B`
