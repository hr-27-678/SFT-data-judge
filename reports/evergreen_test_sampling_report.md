# Evergreen Baseline Test Resampling Report

## Purpose

Resampled to fix six known blindspots. See PROJECT_PLAN.md for
full rationale.

## Inputs

- Salvaged from v0: 500 clean records (preserved labels).
- Excluded reservations: 4985 ids.

## Outputs

- Candidates: `data/splits/teacher_judge/evergreen_test/teacher_candidates_all.jsonl` (1497 records).
- Pre-populated labels: `data/labeled/teacher_judge/evergreen_test/evergreen_test_teacher_labels.jsonl` (500 salvaged).
- Lock: `data/eval/evergreen_test_ids.json`.

## By Source

| Source | Records | Production target |
| --- | ---: | ---: |
| cot_zh | 585 | 38.6% |
| finetome | 793 | 51.6% |
| openmath_reasoning | 119 | 9.9% |

## By Clean / Flagged

| Stratum | Records | Target |
| --- | ---: | ---: |
| clean | 1200 | 1200 |
| flagged | 297 | 300 |

## Flagged Flag Distribution (duplicate_pair INCLUDED)

| Flag | Records |
| --- | ---: |
| `duplicate_pair` | 203 |
| `short_output` | 93 |
| `repeated_punctuation` | 1 |

## Next Steps

1. DeepSeek-label the remaining 1,000 records:

```powershell
python scripts/04_teacher_judge.py `
  --input data/splits/teacher_judge/evergreen_test/teacher_candidates_all.jsonl `
  --output-dir data/labeled/teacher_judge/evergreen_test `
  --output-name evergreen_test_teacher_labels.jsonl `
  --no-dry-run --resume
```

2. Re-run script 18 to rebuild LF dataset, regenerate predict configs, re-run all 6 adapters, re-run script 17 aggregator.
