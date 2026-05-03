# Binary Scorer Eval Report (valid)

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-03 15:29:13 |
| Report type | Greedy prediction evaluation |
| Project stage | V2 binary scorer |
| Report status | Completed split evaluation |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | `Qwen/Qwen3-8B` |
| Data version | `scorer_binary_v2_confident` |
| Split | valid |
| Label policy | score 4/5 -> `keep`; score 1/2 -> `not_keep`; score 3 skipped |
| Current use | Evaluate high-confidence keep ablation |

## Run

- Run name: `scorer_binary_v2_confident_qwen3_8b_lora_e3`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_confident_qwen3_8b_lora_e3_predict_valid_greedy\generated_predictions.jsonl`
- Reference: `data\labeled\scorer_binary_sft_v2\scorer_binary_v2_confident_valid.jsonl`

## Summary

| Metric | Value |
| --- | --- |
| Records | 197 |
| Prediction JSON valid | 197/197 (100.00%) |
| Prediction schema valid | 197/197 (100.00%) |
| Label JSON valid | 197/197 (100.00%) |
| Accuracy | 150/197 (76.14%) |
| Keep precision | 116/149 (77.85%) |
| Keep recall | 116/130 (89.23%) |
| Keep F1 | 0.832 |
| Not-keep precision | 34/48 (70.83%) |
| Not-keep recall | 34/67 (50.75%) |
| Not-keep F1 | 0.591 |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 130 | 149 |
| not_keep | 67 | 48 |

## Per Source

| Source | Records | JSON valid | Schema valid | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| cot_zh | 101 | 100.00% | 100.00% | 68.32% |
| finetome | 69 | 100.00% | 100.00% | 81.16% |
| openmath_reasoning | 27 | 100.00% | 100.00% | 92.59% |

## Confusion Matrix

| Label \ Predict | keep | not_keep |
| --- | ---: | ---: |
| keep | 116 | 14 |
| not_keep | 33 | 34 |
