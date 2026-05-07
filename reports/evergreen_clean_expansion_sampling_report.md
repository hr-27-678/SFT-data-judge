# Evergreen Clean Expansion Sampling Report

## Purpose

Enlarge cot_zh and finetome clean true-negative pools so per-source
not_keep recall on evergreen v2 has stable estimates.

## Inputs

- Excluded reservations: 7782.
- cot_zh clean eligible pool: 68827.
- finetome clean eligible pool: 94437.

## Outputs

- Candidates: `data/splits/teacher_judge/evergreen_clean_expansion/teacher_candidates_all.jsonl`
  (300 records).

## By Source

| Source | Records | Quota |
| --- | ---: | ---: |
| cot_zh | 200 | 200 |
| finetome | 100 | 100 |
| **Total** | **300** | **300** |

## Next Steps

1. DeepSeek-label these records:

```powershell
python scripts/04_teacher_judge.py `
  --input data/splits/teacher_judge/evergreen_clean_expansion/teacher_candidates_all.jsonl `
  --output-dir data/labeled/teacher_judge/evergreen_clean_expansion `
  --output-name evergreen_clean_expansion_teacher_labels.jsonl `
  --no-dry-run --resume
```

2. Merge into evergreen v2 (separate task, not handled here).
