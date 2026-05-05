# Teacher Priority Queue Analysis Report

## Report Metadata

| Field | Value |
| --- | --- |
| Report type | Teacher-labeled priority queue analysis |
| Project stage | V2 active-learning analysis |
| Report status | Generated |

## Experiment Context

| Field | Value |
| --- | --- |
| Priority queue | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\scored\teacher_candidates_all_v2_teacher_review_priority.jsonl` |
| Records | 1215 |
| Joined output | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\scored\teacher_candidates_all_v2_priority_teacher_joined.jsonl` |
| Metrics JSON | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\scored\teacher_candidates_all_v2_priority_teacher_analysis_metrics.json` |
| Current use | Decide v3 training mix and hard-case priorities |

## Summary

| Metric | Count |
| --- | --- |
| Priority records | 1215 |
| Teacher-labeled records | 1215 |
| Missing/invalid labels | 0 |
| Teacher keep | 474 |
| Teacher maybe | 150 |
| Teacher drop | 591 |

## Agreement Bucket By Teacher Verdict

| Bucket | Total | Keep | Maybe | Drop | Missing | Drop rate | Quality-first not_keep rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `conf_keep__cons_keep` | 296 | 243 | 16 | 37 | 0 | 12.5% | 17.9% |
| `conf_keep__cons_not_keep` | 272 | 90 | 58 | 124 | 0 | 45.6% | 66.9% |
| `conf_not_keep__cons_keep` | 1 | 0 | 0 | 1 | 0 | 100.0% | 100.0% |
| `conf_not_keep__cons_not_keep` | 646 | 141 | 76 | 429 | 0 | 66.4% | 78.2% |

## Source By Teacher Verdict

| Source | Total | Keep | Maybe | Drop | Missing | Drop rate |
| --- | --- | --- | --- | --- | --- | --- |
| `cot_zh` | 620 | 215 | 116 | 289 | 0 | 46.6% |
| `finetome` | 495 | 235 | 33 | 227 | 0 | 45.9% |
| `openmath_reasoning` | 100 | 24 | 1 | 75 | 0 | 75.0% |

## Priority Reason By Teacher Verdict

| Reason | Total | Keep | Maybe | Drop | Missing | Drop rate |
| --- | --- | --- | --- | --- | --- | --- |
| `both_not_keep` | 646 | 141 | 76 | 429 | 0 | 66.4% |
| `confident_clean_not_keep` | 490 | 127 | 65 | 298 | 0 | 60.8% |
| `conservative_clean_not_keep` | 702 | 202 | 108 | 392 | 0 | 55.8% |
| `flagged_but_model_keep` | 355 | 258 | 31 | 66 | 0 | 18.6% |
| `model_disagreement` | 273 | 90 | 58 | 125 | 0 | 45.8% |

## Model Policy Checks

| Policy view | Records | Correct | Accuracy |
| --- | --- | --- | --- |
| Conservative target: score 4/5 keep, 1/2/3 not_keep | 1215 | 930 | 76.5% |
| Confident target: score 4/5 keep, 1/2 not_keep, score 3 skipped | 1065 | 763 | 71.6% |

## Critical Error Counts

| Error type | Count | Meaning |
| --- | --- | --- |
| `conservative_false_reject_keep` | 231 | Conservative predicted not_keep but teacher said keep |
| `conservative_missed_drop` | 38 | Conservative predicted keep but teacher said drop |
| `conservative_missed_not_keep_policy` | 54 | Conservative predicted keep but teacher score was 1/2/3 |
| `confident_false_reject_keep` | 141 | Confident predicted not_keep but teacher said keep |
| `confident_missed_drop` | 161 | Confident predicted keep but teacher said drop |

## Missing Or Invalid Labels

All priority records have valid teacher labels.

## Interpretation

- Use `drop` rows from `conf_not_keep__cons_not_keep` as the strongest teacher-confirmed hard negatives.
- Use teacher `keep` rows from conservative `not_keep` buckets as false-reject examples so v3 does not become too conservative.
- Use scorer `keep` but teacher `drop` rows as the highest-risk missed-bad-data examples.
- Keep score-3 / `maybe` rows separate in analysis; for conservative v3 they can map to `not_keep`, but they should not be treated as the same thing as severe `drop` examples.

## Recommended Next Actions

1. Build v3 confident and conservative datasets using starter, targeted, and `v2active001` labels.
2. Prioritize teacher-confirmed hard negatives from `conf_not_keep__cons_not_keep` and model-disagreement buckets.
3. Add a calibration slice from teacher-keep false rejects so the next scorer does not over-reject.
4. After v3 training, rerun scorer inference on a larger unlabeled pool and create `v2active002` from newly surfaced hard cases.
