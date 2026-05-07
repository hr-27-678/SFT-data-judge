# Evergreen Baseline Test Flagged Stratum Sampling Report

## Purpose

Adds a 100-record flagged stratum to the evergreen cross-version test
set so scorer behavior on rule-flagged records can be measured. The
5,000 active-learning pool's flagged subset was fully consumed by
v2active002 priority, so this batch samples directly from the 188K
processed pool. Same lock policy: NEVER passed to training.

## Inputs

- Processed pool: `data/processed/by_source/`
- Excluded ids (all teacher-labeled + locked + clean evergreen): 5185

## Outputs

- Candidates: `data\splits\teacher_judge\evergreen_test_v1_flagged\teacher_candidates_all.jsonl`

## Selected By Source

| Source | Records |
| --- | ---: |
| cot_zh | 40 |
| finetome | 60 |
| **Total** | **100** |

## Selected By Flag Type

| Flag | Records |
| --- | ---: |
| `short_output` | 98 |
| `possible_mojibake` | 1 |
| `short_instruction` | 1 |

## Combined Evergreen Test Set

- Clean (v1 + supplement): 500
- Flagged (this batch): 100
- **Combined evergreen total: 600**

## Next Step

Run teacher labeling on this batch:

```powershell
python scripts/04_teacher_judge.py `
  --input data\splits\teacher_judge\evergreen_test_v1_flagged\teacher_candidates_all.jsonl `
  --output-dir data/labeled/teacher_judge/evergreen_test_v1_flagged `
  --output-name evergreen_test_v1_flagged_teacher_labels.jsonl `
  --no-dry-run --resume
```
