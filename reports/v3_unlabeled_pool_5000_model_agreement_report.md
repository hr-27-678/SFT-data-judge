# v3_unlabeled_pool_5000 Model Agreement Report

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-06 18:37:32 UTC |
| Report type | Model agreement / active-learning triage |
| Project stage | V3 scorer deployment / teacher relabeling selection |
| Report status | Generated |

## Experiment Context

| Field | Value |
| --- | --- |
| Input pool | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\splits\teacher_judge\v3_unlabeled_pool_5000\teacher_candidates_all.jsonl` |
| Records | 5000 |
| Conservative model | scorer_binary_v3_conservative_qwen3_8b_lora_e3 |
| Confident model | scorer_binary_v3_confident_qwen3_8b_lora_e3 |
| Pool teacher-label exclusion | applied at sampling time (script 02) |
| Locked test overlap | verified 0 (2026-05-06) |

## Headline

The two Qwen3-8B v3 scorers agree on 4352 / 5000 records (87.04%) and disagree on 648 records.

## Agreement Buckets

| bucket | count |
| --- | --- |
| conf_keep__cons_keep | 3115 |
| conf_keep__cons_not_keep | 644 |
| conf_not_keep__cons_keep | 4 |
| conf_not_keep__cons_not_keep | 1237 |

## By Source

| source | conf_keep__cons_keep | conf_keep__cons_not_keep | conf_not_keep__cons_keep | conf_not_keep__cons_not_keep |
| --- | --- | --- | --- | --- |
| cot_zh | 1511 | 511 | 1 | 977 |
| finetome | 879 | 123 | 3 | 245 |
| openmath_reasoning | 725 | 10 | 0 | 15 |

## By Rule Flag

| rule status | conf_keep__cons_keep | conf_keep__cons_not_keep | conf_not_keep__cons_keep | conf_not_keep__cons_not_keep |
| --- | --- | --- | --- | --- |
| clean | 2723 | 552 | 3 | 1065 |
| flagged | 392 | 92 | 1 | 172 |

## Priority Queue

| Metric | Count |
| --- | --- |
| Priority records (any reason) | 2277 |
| Calibration random (after dedup vs priority) | 88 |
| Combined output rows | 2365 |

## Priority Records By Reason

| reason | count |
| --- | --- |
| conservative_clean_not_keep | 1617 |
| both_not_keep | 1237 |
| confident_clean_not_keep | 1068 |
| model_disagreement | 648 |
| flagged_but_model_keep | 485 |

## Outputs

| Artifact | Path |
| --- | --- |
| Agreement metrics | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\scored\v3_unlabeled_pool_5000_model_agreement_metrics.json` |
| Disagreements JSONL | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\scored\v3_unlabeled_pool_5000_model_disagreements.jsonl` |
| Priority + calibration JSONL | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\scored\v3_unlabeled_pool_5000_teacher_review_priority.jsonl` |

## Interpretation

- `conf_keep__cons_keep`: most likely usable; sampled randomly as calibration to detect silent scorer errors.
- `conf_keep__cons_not_keep`: conservative-only rejection; tests if conservative is over-rejecting.
- `conf_not_keep__cons_keep`: confident-only rejection; small but high-signal boundary cases.
- `conf_not_keep__cons_not_keep`: strongest hard-negative candidates; sampled randomly as calibration too.
- `calibration_random`: marked with `selection_reason=calibration` so downstream analysis can
  separately measure how often teacher disagrees with both scorers when both scorers agree.

## Next Step

Run `scripts/13_build_teacher_review_batch.py` with `--input \\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\scored\v3_unlabeled_pool_5000_teacher_review_priority.jsonl`
and a fresh `--batch-prefix` (e.g. `v2active002`) to dedup against existing teacher labels
and produce the next teacher-labeling batch.
