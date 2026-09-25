# Results

## Comparison Matrix

| Teacher | Teacher Accuracy | student_naive | student_strategic_fd (beta_s=0.5) |
| --- | --- | --- | --- |
| teacher_standard | 0.8751 | 0.5881 | 0.5889<br><sub>mean_a=-0.2895, frac_mass_top20=0.2297</sub> |

Model Context:
- Dataset: `gsm8k`
- Teacher model: `/scratch/aliasgarov/distillation-game/models/DeepSeek-R1-Distill-Qwen-7B`
- Student model: `/scratch/aliasgarov/distillation-game/models/Llama-3.2-3B`
