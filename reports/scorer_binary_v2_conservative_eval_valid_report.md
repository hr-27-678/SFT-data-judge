# Binary Scorer Evaluation Report: Qwen3-8B V2 Conservative (Valid)

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-02 16:33:01 |
| Report type | Split evaluation |
| Project stage | V2 binary scorer |
| Report status | Canonical valid evaluation |
| Split | valid |
| Evaluation mode | Greedy deterministic prediction |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | `Qwen/Qwen3-8B` |
| Run name | `scorer_binary_v2_conservative_qwen3_8b_lora_e3` |
| Data version | `scorer_binary_v2_conservative` |
| Label policy | score 4/5 -> `keep`; score 1/2/3 -> `not_keep` |
| Predictions | `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_conservative_qwen3_8b_lora_e3_predict_valid_greedy\generated_predictions.jsonl` |
| Reference | `data\labeled\scorer_binary_sft_v2\scorer_binary_v2_conservative_valid.jsonl` |
| Related summary | `scorer_binary_v2_conservative_qwen3_8b_experiment_report.md` |

## Metrics Summary

| Metric | Value |
| --- | --- |
| Records | 224 |
| Prediction JSON valid | 224/224 (100.00%) |
| Prediction schema valid | 224/224 (100.00%) |
| Label JSON valid | 224/224 (100.00%) |
| Accuracy | 167/224 (74.55%) |
| Keep precision | 113/153 (73.86%) |
| Keep recall | 113/130 (86.92%) |
| Keep F1 | 0.799 |
| Not-keep precision | 54/71 (76.06%) |
| Not-keep recall | 54/94 (57.45%) |
| Not-keep F1 | 0.655 |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 130 | 153 |
| not_keep | 94 | 71 |

## Source Breakdown

| Source | Records | JSON valid | Schema valid | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| cot_zh | 122 | 100.00% | 100.00% | 67.21% |
| finetome | 73 | 100.00% | 100.00% | 83.56% |
| openmath_reasoning | 29 | 100.00% | 100.00% | 82.76% |

## Confusion Matrix

| Label \ Predict | keep | not_keep |
| --- | ---: | ---: |
| keep | 113 | 17 |
| not_keep | 40 | 54 |

## Interpretation

- Valid accuracy is lower than the v1 compact baseline, but the split is harder because score 3 maps to `not_keep`.
- Valid `not_keep` precision is solid at `76.06%`, but recall is only `57.45%`.
- `cot_zh` remains the weakest source on valid, with 67.21% accuracy.
- This split supports using the model as a review-routing scorer rather than an automatic dropper.

## Recommended Next Actions

1. Inspect `cot_zh` false positives and false negatives before adding more random data.
2. Use larger-pool inference to identify hard negatives and uncertain examples.
3. Compare against the completed v2 confident ablation if keep precision becomes the priority.
