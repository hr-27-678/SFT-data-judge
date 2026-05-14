# V5 Math/Code Hard-Negative Teacher Sampling Report

This batch targets the math/code not_keep coverage gap found by the evergreen human audit.

- Batch prefix: `v5_math_code_hardneg`
- Output: `data\splits\teacher_judge\v5_math_code_hard_negatives\v5_math_code_hardneg_teacher_candidates_all.jsonl`
- Records: 600
- Excluded ids: 12211
- Seed: 20260514

## Requested Quotas

- openmath hard: 300
- code hard: 150
- openmath keep controls: 75
- code keep controls: 75

## Available Candidate Pools After Exclusion

- openmath hard candidates: 3065
- code hard candidates: 22064
- openmath keep controls: 13950
- code keep controls: 10452

## Selected Distribution

- by bucket: `{'openmath': 375, 'code': 225}`
- by reason: `{'heuristic_answer_mismatch': 291, 'missing_boxed_answer': 9, 'python_syntax_error': 145, 'code_prompt_missing_code': 5, 'balance_keep_control': 150}`

## Teacher Labeling Command

```powershell
python scripts/04_teacher_judge.py `
  --input data\splits\teacher_judge\v5_math_code_hard_negatives\v5_math_code_hardneg_teacher_candidates_all.jsonl `
  --output-dir data/labeled/teacher_judge/v5_math_code_hardneg `
  --output-name v5_math_code_hardneg_teacher_labels.jsonl `
  --no-dry-run `
  --resume
```

## Notes

- These are candidate records only. They still need teacher labels before training.
- The hard-negative heuristics are intentionally high-recall and may include false positives.
- Keep-control slices are included so v5 does not learn `math/code -> not_keep`.