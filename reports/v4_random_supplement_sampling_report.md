# v4 Random Clean Supplement Sampling Report

## Purpose

Plan B v4 strategy supplement: 1,000 random clean records from
the 188K production pool, source-stratified at 38/52/10 to match
production. All `is_clean=True`. Goal: provide ~240 new
production-distribution clean+not_keep training examples to
break the rule-flag shortcut.

## Inputs

- Excluded reservations: 6482 (all teacher-labeled + locked + v2active002 + evergreen).

## Outputs

- Candidates: `data/splits/teacher_judge/v4_random_supplement/teacher_candidates_all.jsonl`
  (1000 records).

## By Source

| Source | Records | Production target |
| --- | ---: | ---: |
| cot_zh | 386 | 38.6% |
| finetome | 515 | 51.6% |
| openmath_reasoning | 99 | 9.9% |
| **Total** | **1000** | 100% |

## Next Steps

1. DeepSeek-label these 1,000 records:

```powershell
python scripts/04_teacher_judge.py `
  --input data/splits/teacher_judge/v4_random_supplement/teacher_candidates_all.jsonl `
  --output-dir data/labeled/teacher_judge/v4_random_supplement `
  --output-name v4_random_supplement_teacher_labels.jsonl `
  --no-dry-run --resume
```

2. After labeling completes, pass this batch to
   `scripts/09_build_binary_scorer_sft.py` with `--no-rule-fields`
   (Plan B prompt change) to build v4 binary scorer datasets.
