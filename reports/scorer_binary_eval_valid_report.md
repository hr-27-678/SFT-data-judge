# Binary Scorer Eval Report (valid_greedy)

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-01 18:24:50 |
| Report type | Split evaluation |
| Project stage | V1 binary confident scorer |
| Report status | Compact baseline valid evaluation |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | `Qwen/Qwen3-4B-Instruct-2507` |
| Data version | `scorer_binary_confident_1000` |
| Split | valid_greedy |
| Evaluation mode | Greedy deterministic prediction |
| Run name | `scorer_binary_confident_1000_qwen3_4b_lora_e3` |
| Label policy | score 4/5 -> `keep`; score 1/2 -> `not_keep`; score 3 skipped |
| Current use | Compact binary baseline valid metrics |

## Run Artifacts
- Run name: `scorer_binary_confident_1000_qwen3_4b_lora_e3`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_4b_lora_e3_predict_valid_greedy\generated_predictions.jsonl`
- Reference: `SFT-DataJudge\data\labeled\scorer_binary_sft\scorer_binary_confident_1000_valid.jsonl`

## Metrics Summary
| Metric | Value |
| --- | --- |
| Records | 95 |
| Prediction JSON valid | 95/95 (100.00%) |
| Prediction schema valid | 95/95 (100.00%) |
| Label JSON valid | 95/95 (100.00%) |
| Accuracy | 78/95 (82.11%) |
| Keep precision | 58/66 (87.88%) |
| Keep recall | 58/67 (86.57%) |
| Keep F1 | 0.872 |
| Not-keep precision | 20/29 (68.97%) |
| Not-keep recall | 20/28 (71.43%) |
| Not-keep F1 | 0.702 |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 67 | 66 |
| not_keep | 28 | 29 |

## Source Breakdown
| Source | Records | JSON valid | Schema valid | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| cot_zh | 36 | 100.00% | 100.00% | 86.11% |
| finetome | 40 | 100.00% | 100.00% | 72.50% |
| openmath_reasoning | 19 | 100.00% | 100.00% | 94.74% |

## Confusion Matrix

| Label \ Predict | keep | not_keep |
| --- | ---: | ---: |
| keep | 58 | 9 |
| not_keep | 8 | 20 |
