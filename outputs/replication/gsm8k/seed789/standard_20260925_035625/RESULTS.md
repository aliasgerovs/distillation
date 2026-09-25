# Results

## Comparison Matrix

| Teacher | Teacher Accuracy | student_naive | student_strategic_fd (beta_s=0.5) |
| --- | --- | --- | --- |
| teacher_standard | 0.8817 | 0.5931 | 0.5906<br><sub>mean_a=-0.2941, frac_mass_top20=0.2303</sub> |

Model Context:
- Dataset: `gsm8k`
- Teacher model: `/scratch/aliasgarov/distillation-game/models/DeepSeek-R1-Distill-Qwen-7B`
- Student model: `/scratch/aliasgarov/distillation-game/models/Llama-3.2-3B`
