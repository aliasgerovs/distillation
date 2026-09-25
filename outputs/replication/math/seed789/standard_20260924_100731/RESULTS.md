# Results

## Comparison Matrix

| Teacher | Teacher Accuracy | student_naive | student_strategic_fd (beta_s=0.5) |
| --- | --- | --- | --- |
| teacher_standard | 0.6340 | 0.1380 | 0.1476<br><sub>mean_a=-0.0706, frac_mass_top20=0.2083</sub> |

Model Context:
- Dataset: `math`
- Teacher model: `/scratch/aliasgarov/distillation-game/models/DeepSeek-R1-Distill-Qwen-7B`
- Student model: `/scratch/aliasgarov/distillation-game/models/Llama-3.2-3B`
