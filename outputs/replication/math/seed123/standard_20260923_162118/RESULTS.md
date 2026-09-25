# Results

## Comparison Matrix

| Teacher | Teacher Accuracy | student_naive | student_strategic_fd (beta_s=0.5) |
| --- | --- | --- | --- |
| teacher_standard | 0.6226 | 0.1552 | 0.1570<br><sub>mean_a=-0.0720, frac_mass_top20=0.2084</sub> |

Model Context:
- Dataset: `math`
- Teacher model: `/scratch/aliasgarov/distillation-game/models/DeepSeek-R1-Distill-Qwen-7B`
- Student model: `/scratch/aliasgarov/distillation-game/models/Llama-3.2-3B`
