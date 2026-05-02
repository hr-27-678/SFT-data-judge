# Binary Scorer Eval Report (test_greedy)

Generated: 2026-05-01 18:24:51

## Run

- Run name: `scorer_binary_confident_1000_qwen3_4b_lora_e3`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_4b_lora_e3_predict_test_greedy\generated_predictions.jsonl`
- Reference: `SFT-DataJudge\data\labeled\scorer_binary_sft\scorer_binary_confident_1000_test.jsonl`

## Summary

| Metric | Value |
| --- | --- |
| Records | 96 |
| Prediction JSON valid | 96/96 (100.00%) |
| Prediction schema valid | 96/96 (100.00%) |
| Label JSON valid | 96/96 (100.00%) |
| Accuracy | 73/96 (76.04%) |
| Keep precision | 54/62 (87.10%) |
| Keep recall | 54/69 (78.26%) |
| Keep F1 | 0.824 |
| Not-keep precision | 19/34 (55.88%) |
| Not-keep recall | 19/27 (70.37%) |
| Not-keep F1 | 0.623 |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 69 | 62 |
| not_keep | 27 | 34 |

## Per Source

| Source | Records | JSON valid | Schema valid | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| cot_zh | 36 | 100.00% | 100.00% | 63.89% |
| finetome | 40 | 100.00% | 100.00% | 77.50% |
| openmath_reasoning | 20 | 100.00% | 100.00% | 95.00% |

## Confusion Matrix

| Label \ Predict | keep | not_keep |
| --- | ---: | ---: |
| keep | 54 | 15 |
| not_keep | 8 | 19 |
