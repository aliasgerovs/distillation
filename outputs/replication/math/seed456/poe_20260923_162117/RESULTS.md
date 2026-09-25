# Results

## Comparison Matrix

| Teacher | Teacher Accuracy | student_naive | student_strategic_fd (beta_s=0.5) |
| --- | --- | --- | --- |
| teacher_poe_gamma_0.75 | 0.6150 | 0.1214 | 0.1378<br><sub>mean_a=-0.0865, frac_mass_top20=0.2109</sub> |

Model Context:
- Dataset: `math`
- Teacher model: `/scratch/aliasgarov/distillation-game/models/DeepSeek-R1-Distill-Qwen-7B`
- Student model: `/scratch/aliasgarov/distillation-game/models/Llama-3.2-3B`
