# Binary Scorer Eval Report (test)

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-03 15:29:14 |
| Report type | Greedy prediction evaluation |
| Project stage | V2 binary scorer |
| Report status | Completed split evaluation |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | `Qwen/Qwen3-8B` |
| Data version | `scorer_binary_v2_confident` |
| Split | test |
| Label policy | score 4/5 -> `keep`; score 1/2 -> `not_keep`; score 3 skipped |
| Current use | Evaluate high-confidence keep ablation |

## Run

- Run name: `scorer_binary_v2_confident_qwen3_8b_lora_e3`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_confident_qwen3_8b_lora_e3_predict_test_greedy\generated_predictions.jsonl`
- Reference: `data\labeled\scorer_binary_sft_v2\scorer_binary_v2_confident_test.jsonl`

## Summary

| Metric | Value |
| --- | --- |
| Records | 199 |
| Prediction JSON valid | 199/199 (100.00%) |
| Prediction schema valid | 199/199 (100.00%) |
| Label JSON valid | 199/199 (100.00%) |
| Accuracy | 164/199 (82.41%) |
| Keep precision | 127/154 (82.47%) |
| Keep recall | 127/135 (94.07%) |
| Keep F1 | 0.879 |
| Not-keep precision | 37/45 (82.22%) |
| Not-keep recall | 37/64 (57.81%) |
| Not-keep F1 | 0.679 |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 135 | 154 |
| not_keep | 64 | 45 |

## Per Source

| Source | Records | JSON valid | Schema valid | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| cot_zh | 103 | 100.00% | 100.00% | 77.67% |
| finetome | 67 | 100.00% | 100.00% | 83.58% |
| openmath_reasoning | 29 | 100.00% | 100.00% | 96.55% |

## Confusion Matrix

| Label \ Predict | keep | not_keep |
| --- | ---: | ---: |
| keep | 127 | 8 |
| not_keep | 27 | 37 |
