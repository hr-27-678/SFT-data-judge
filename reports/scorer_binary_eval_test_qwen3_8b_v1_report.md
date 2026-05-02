# Binary Scorer Eval Report (test)

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-02 12:50:00 |
| Report type | Split evaluation |
| Project stage | V1 binary confident scorer |
| Report status | Qwen3-8B capacity-check test evaluation |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | `Qwen/Qwen3-8B` |
| Data version | `scorer_binary_confident_1000` |
| Split | test |
| Evaluation mode | Greedy deterministic prediction |
| Run name | `scorer_binary_confident_1000_qwen3_8b_lora_e3` |
| Label policy | score 4/5 -> `keep`; score 1/2 -> `not_keep`; score 3 skipped |
| Current use | Compare 8B v1 capacity against 4B baseline and v2 conservative |

## Run Artifacts
- Run name: `scorer_binary_confident_1000_qwen3_8b_lora_e3`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_8b_lora_e3_predict_test_greedy\generated_predictions.jsonl`
- Reference: `data\labeled\scorer_binary_sft\scorer_binary_confident_1000_test.jsonl`

## Metrics Summary
| Metric | Value |
| --- | --- |
| Records | 96 |
| Prediction JSON valid | 96/96 (100.00%) |
| Prediction schema valid | 96/96 (100.00%) |
| Label JSON valid | 96/96 (100.00%) |
| Accuracy | 81/96 (84.38%) |
| Keep precision | 67/80 (83.75%) |
| Keep recall | 67/69 (97.10%) |
| Keep F1 | 0.899 |
| Not-keep precision | 14/16 (87.50%) |
| Not-keep recall | 14/27 (51.85%) |
| Not-keep F1 | 0.651 |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 69 | 80 |
| not_keep | 27 | 16 |

## Source Breakdown
| Source | Records | JSON valid | Schema valid | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| cot_zh | 36 | 100.00% | 100.00% | 80.56% |
| finetome | 40 | 100.00% | 100.00% | 85.00% |
| openmath_reasoning | 20 | 100.00% | 100.00% | 90.00% |

## Confusion Matrix

| Label \ Predict | keep | not_keep |
| --- | ---: | ---: |
| keep | 67 | 2 |
| not_keep | 13 | 14 |
