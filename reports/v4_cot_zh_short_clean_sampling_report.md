# v4 cot_zh Short-Clean Targeted Sampling Report

## Purpose

Evergreen evaluation isolated cot_zh clean as the weakest slice
for current scorers (true drop rate ~28.7%, v3 cons recall 12.79%).
Short cot_zh records dominate the failure mode. This batch
adds 300 cot_zh short-clean records to v4.

## Inputs

- Excluded reservations: 7482.
- cot_zh clean eligible pool: 69127.
- Short bucket cutoff: output_len <= 31.
- Short pool size: 24445.

## Outputs

- Candidates: `data/splits/teacher_judge/v4_cot_zh_short_clean/teacher_candidates_all.jsonl`
  (300 records).

## Next Steps

Label with DeepSeek:

```powershell
python scripts/04_teacher_judge.py `
  --input data/splits/teacher_judge/v4_cot_zh_short_clean/teacher_candidates_all.jsonl `
  --output-dir data/labeled/teacher_judge/v4_cot_zh_short_clean `
  --output-name v4_cot_zh_short_clean_teacher_labels.jsonl `
  --no-dry-run --resume
```
