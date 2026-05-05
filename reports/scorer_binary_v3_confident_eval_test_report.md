# Binary Scorer Eval Report (test)

Generated: 2026-05-05 12:53:11

## Run

- Run name: `scorer_binary_v3_confident_qwen3_8b`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_confident_qwen3_8b_lora_e3_predict_test_greedy\generated_predictions.jsonl`
- Reference: `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\scorer_binary_sft_v3\scorer_binary_v3_confident_test.jsonl`

## Summary

| Metric | Value |
| --- | --- |
| Records | 237 |
| Prediction JSON valid | 237/237 (100.00%) |
| Prediction schema valid | 237/237 (100.00%) |
| Label JSON valid | 237/237 (100.00%) |
| Accuracy | 187/237 (78.90%) |
| Keep precision | 143/181 (79.01%) |
| Keep recall | 143/155 (92.26%) |
| Keep F1 | 0.851 |
| Not-keep precision | 44/56 (78.57%) |
| Not-keep recall | 44/82 (53.66%) |
| Not-keep F1 | 0.638 |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 155 | 181 |
| not_keep | 82 | 56 |

## Per Source

| Source | Records | JSON valid | Schema valid | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| cot_zh | 110 | 100.00% | 100.00% | 74.55% |
| finetome | 95 | 100.00% | 100.00% | 77.89% |
| openmath_reasoning | 32 | 100.00% | 100.00% | 96.88% |

## Confusion Matrix

| Label \ Predict | keep | not_keep |
| --- | ---: | ---: |
| keep | 143 | 12 |
| not_keep | 38 | 44 |
