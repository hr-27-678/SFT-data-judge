# Binary Scorer Eval Report (valid)

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-02 12:50:01 |
| Report type | Split evaluation |
| Project stage | V1 binary confident scorer |
| Report status | Qwen3-8B capacity-check valid evaluation |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | `Qwen/Qwen3-8B` |
| Data version | `scorer_binary_confident_1000` |
| Split | valid |
| Evaluation mode | Greedy deterministic prediction |
| Run name | `scorer_binary_confident_1000_qwen3_8b_lora_e3` |
| Label policy | score 4/5 -> `keep`; score 1/2 -> `not_keep`; score 3 skipped |
| Current use | Compare 8B v1 capacity against 4B baseline and v2 conservative |

## Run Artifacts
- Run name: `scorer_binary_confident_1000_qwen3_8b_lora_e3`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_8b_lora_e3_predict_valid_greedy\generated_predictions.jsonl`
- Reference: `data\labeled\scorer_binary_sft\scorer_binary_confident_1000_valid.jsonl`

## Metrics Summary
| Metric | Value |
| --- | --- |
| Records | 95 |
| Prediction JSON valid | 95/95 (100.00%) |
| Prediction schema valid | 95/95 (100.00%) |
| Label JSON valid | 95/95 (100.00%) |
| Accuracy | 74/95 (77.89%) |
| Keep precision | 60/74 (81.08%) |
| Keep recall | 60/67 (89.55%) |
| Keep F1 | 0.851 |
| Not-keep precision | 14/21 (66.67%) |
| Not-keep recall | 14/28 (50.00%) |
| Not-keep F1 | 0.571 |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 67 | 74 |
| not_keep | 28 | 21 |

## Source Breakdown
| Source | Records | JSON valid | Schema valid | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| cot_zh | 36 | 100.00% | 100.00% | 75.00% |
| finetome | 40 | 100.00% | 100.00% | 75.00% |
| openmath_reasoning | 19 | 100.00% | 100.00% | 89.47% |

## Confusion Matrix

| Label \ Predict | keep | not_keep |
| --- | ---: | ---: |
| keep | 60 | 7 |
| not_keep | 14 | 14 |
