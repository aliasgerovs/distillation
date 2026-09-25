# Results

## Comparison Matrix

| Teacher | Teacher Accuracy | student_naive | student_strategic_fd (beta_s=0.5) |
| --- | --- | --- | --- |
| teacher_poe_gamma_0.75 | 0.8125 | 0.0000 | 0.0000<br><sub>mean_a=-0.1129, frac_mass_top20=0.2027</sub> |
| teacher_standard | 0.8438 | 0.0000 | 0.0000<br><sub>mean_a=-0.0549, frac_mass_top20=0.1957</sub> |

Model Context:
- Dataset: `math`
- Teacher model: `/scratch/aliasgarov/distillation-game/models/DeepSeek-R1-Distill-Qwen-7B`
- Student model: `/scratch/aliasgarov/distillation-game/models/Llama-3.2-3B`
