# Binary Scorer Evaluation Report: Qwen3-8B V2 Conservative (Test)

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-02 16:33:03 |
| Report type | Split evaluation |
| Project stage | V2 binary scorer |
| Report status | Canonical test evaluation |
| Split | test |
| Evaluation mode | Greedy deterministic prediction |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | `Qwen/Qwen3-8B` |
| Run name | `scorer_binary_v2_conservative_qwen3_8b_lora_e3` |
| Data version | `scorer_binary_v2_conservative` |
| Label policy | score 4/5 -> `keep`; score 1/2/3 -> `not_keep` |
| Predictions | `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_conservative_qwen3_8b_lora_e3_predict_test_greedy\generated_predictions.jsonl` |
| Reference | `data\labeled\scorer_binary_sft_v2\scorer_binary_v2_conservative_test.jsonl` |
| Related summary | `scorer_binary_v2_conservative_qwen3_8b_experiment_report.md` |

## Metrics Summary

| Metric | Value |
| --- | --- |
| Records | 224 |
| Prediction JSON valid | 224/224 (100.00%) |
| Prediction schema valid | 224/224 (100.00%) |
| Label JSON valid | 224/224 (100.00%) |
| Accuracy | 179/224 (79.91%) |
| Keep precision | 122/154 (79.22%) |
| Keep recall | 122/135 (90.37%) |
| Keep F1 | 0.844 |
| Not-keep precision | 57/70 (81.43%) |
| Not-keep recall | 57/89 (64.04%) |
| Not-keep F1 | 0.717 |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 135 | 154 |
| not_keep | 89 | 70 |

## Source Breakdown

| Source | Records | JSON valid | Schema valid | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| cot_zh | 122 | 100.00% | 100.00% | 76.23% |
| finetome | 73 | 100.00% | 100.00% | 79.45% |
| openmath_reasoning | 29 | 100.00% | 100.00% | 96.55% |

## Confusion Matrix

| Label \ Predict | keep | not_keep |
| --- | ---: | ---: |
| keep | 122 | 13 |
| not_keep | 32 | 57 |

## Interpretation

- Test `not_keep` F1 is `0.717`, which is the strongest rejection result so far.
- The model still predicts more keep than not_keep: 154 keep vs 70 not_keep.
- 32/89 true `not_keep` examples are still missed, so this split does not justify blind automatic deletion.
- `openmath_reasoning` is strong on this split; `cot_zh` and `finetome` still need targeted inspection.

## Recommended Next Actions

1. Use this model for prioritization and review routing, not irreversible deletion.
2. Run the scorer on a larger unlabeled pool and sample high-confidence keep, high-confidence not_keep, and uncertain cases.
3. Use teacher relabeling on high-impact or conflicting examples.
