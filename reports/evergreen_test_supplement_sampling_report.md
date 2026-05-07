# Evergreen Baseline Test Supplement Sampling Report

## Purpose

Supplement to `evergreen_test_v1` (200 records) to reach a 500-record
total cross-version evaluation set at the 60/25/15 source ratio.
Same lock policy: NEVER passed to training.

## Inputs

- Source pool: `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\splits\teacher_judge\v3_unlabeled_pool_5000\teacher_candidates_all.jsonl` (5000 records)
- Excluded: 2565 ids (v2active002 candidates + evergreen_test_v1 candidates)
- Eligible clean pool: 2435 records

## Outputs

- Candidates: `data\splits\teacher_judge\evergreen_test_v1_supplement\teacher_candidates_all.jsonl`

## Selected By Source

| Source | Records | Combined with v1 (target 500) |
| --- | ---: | ---: |
| cot_zh | 180 | 300 |
| finetome | 75 | 125 |
| openmath_reasoning | 45 | 75 |
| **Total** | **300** | **500** |

## Note

All records are clean. The 5,000 pool's flagged subset was fully
consumed by `v2active002` priority queue, so flagged-record edge
coverage is deferred to a future evergreen_test_v2 batch.

## Next Step

Run teacher labeling on this batch (parallel-safe with the original
evergreen_test_v1 job and the v2active002 job):

```powershell
python scripts/04_teacher_judge.py `
  --input data\splits\teacher_judge\evergreen_test_v1_supplement\teacher_candidates_all.jsonl `
  --output-dir data/labeled/teacher_judge/evergreen_test_v1_supplement `
  --output-name evergreen_test_v1_supplement_teacher_labels.jsonl `
  --no-dry-run --resume
```

After this and `evergreen_test_v1` both finish, the combined 500
records form the cross-version baseline. The evaluation script
`scripts/17_evaluate_on_evergreen.py` (TBD) will read both label
files together and compute one comparison table.
