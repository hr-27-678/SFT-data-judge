# Teacher Candidate Pool v2 Model Agreement Report

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-03 16:19:29 |
| Report type | Model agreement / active-learning triage |
| Project stage | Scorer deployment / teacher relabeling selection |
| Report status | Generated |

## Experiment Context

| Field | Value |
| --- | --- |
| Input pool | `data/splits/teacher_judge/teacher_candidates_all.jsonl` |
| Records | 3,600 |
| Conservative model | `scorer_binary_v2_conservative_qwen3_8b_lora_e3` |
| Confident model | `scorer_binary_v2_confident_qwen3_8b_lora_e3` |
| Current use | Select priority samples for teacher labeling before retraining |

Input pool: `data/splits/teacher_judge/teacher_candidates_all.jsonl` (3600 records)

Models:
- Conservative: `scorer_binary_v2_conservative_qwen3_8b_lora_e3`
- Confident: `scorer_binary_v2_confident_qwen3_8b_lora_e3`

## Headline

The two 8B v2 scorers agree on 3327 / 3600 records (92.42%) and disagree on 273 records.

The confident scorer is wider: it keeps 2953 / 3600 records, while the conservative scorer keeps 2682 / 3600. This is useful: the disagreement set is a compact review queue for ambiguous policy-boundary samples, while the both-not-keep set is a stronger candidate pool for teacher relabeling and future hard negatives.

## Agreement Buckets

| bucket | count |
|---|---:|
| `conf_keep__cons_keep` | 2681 |
| `conf_keep__cons_not_keep` | 272 |
| `conf_not_keep__cons_keep` | 1 |
| `conf_not_keep__cons_not_keep` | 646 |

Interpretation:
- `conf_keep__cons_keep`: likely usable; low priority for teacher unless we need positive calibration samples.
- `conf_keep__cons_not_keep`: conservative-only rejection. Good for checking whether conservative is over-rejecting clean-but-short or terse samples.
- `conf_not_keep__cons_keep`: confident-only rejection. Smallest but important, because it exposes cases where the "keep" boundary may still be too loose.
- `conf_not_keep__cons_not_keep`: strongest candidate hard negatives for teacher verification.

## By Source

| source | `conf_keep__cons_keep` | `conf_keep__cons_not_keep` | `conf_not_keep__cons_keep` | `conf_not_keep__cons_not_keep` |
|---|---:|---:|---:|---:|
| cot_zh | 692 | 188 | 0 | 320 |
| finetome | 887 | 79 | 1 | 233 |
| openmath_reasoning | 1102 | 5 | 0 | 93 |

## By Clean Flag

| rule status | `conf_keep__cons_keep` | `conf_keep__cons_not_keep` | `conf_not_keep__cons_keep` | `conf_not_keep__cons_not_keep` |
|---|---:|---:|---:|---:|
| clean | 2385 | 213 | 1 | 489 |
| flagged_or_rule_dirty | 296 | 59 | 0 | 157 |

## By Length Bucket

| length bucket | `conf_keep__cons_keep` | `conf_keep__cons_not_keep` | `conf_not_keep__cons_keep` | `conf_not_keep__cons_not_keep` |
|---|---:|---:|---:|---:|
| long | 877 | 104 | 0 | 204 |
| medium | 855 | 93 | 1 | 275 |
| short | 949 | 75 | 0 | 167 |

## Priority Review Queue

Wrote 1215 records to `data/scored/teacher_candidates_all_v2_teacher_review_priority.jsonl`.

The first teacher-labeling subset is
`data/scored/teacher_candidates_all_v2_teacher_review_top919.jsonl`, containing
all 273 model disagreements plus all 646 both-not-keep records.

Dry-run teacher prompts were rendered to
`data/labeled/teacher_judge/v2_pilot_top919/v2_pilot_top919_teacher_prompts.jsonl`.

Priority reason counts:

| reason | count |
|---|---:|
| `both_not_keep` | 646 |
| `confident_clean_not_keep` | 490 |
| `conservative_clean_not_keep` | 702 |
| `flagged_but_model_keep` | 355 |
| `model_disagreement` | 273 |


Also wrote 273 model-disagreement records to `data/scored/teacher_candidates_all_v2_model_disagreements.jsonl`.

## Recommended Next Step

Do not run all 188k unlabeled rows yet. Send this 3,600-row pilot's priority queue to the teacher first, starting with all 273 disagreements plus the 646 both-not-keep records. After teacher labels return, build a v3 training mix that includes existing labeled data, teacher-confirmed hard negatives, teacher-confirmed false rejects, and a small set of normal keep samples from `conf_keep__cons_keep`.

This keeps the loop as active learning rather than self-training: the student models choose where to ask questions, but the teacher supplies the labels.
