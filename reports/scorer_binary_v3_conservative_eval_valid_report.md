# Binary Scorer Eval Report (valid)

Generated: 2026-05-05 12:53:10

## Run

- Run name: `scorer_binary_v3_conservative_qwen3_8b`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3_predict_valid_greedy\generated_predictions.jsonl`
- Reference: `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\scorer_binary_sft_v3\scorer_binary_v3_conservative_valid.jsonl`

## Summary

| Metric | Value |
| --- | --- |
| Records | 267 |
| Prediction JSON valid | 267/267 (100.00%) |
| Prediction schema valid | 267/267 (100.00%) |
| Label JSON valid | 267/267 (100.00%) |
| Accuracy | 198/267 (74.16%) |
| Keep precision | 107/141 (75.89%) |
| Keep recall | 107/142 (75.35%) |
| Keep F1 | 0.756 |
| Not-keep precision | 91/126 (72.22%) |
| Not-keep recall | 91/125 (72.80%) |
| Not-keep F1 | 0.725 |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 142 | 141 |
| not_keep | 125 | 126 |

## Per Source

| Source | Records | JSON valid | Schema valid | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| cot_zh | 132 | 100.00% | 100.00% | 71.21% |
| finetome | 102 | 100.00% | 100.00% | 76.47% |
| openmath_reasoning | 33 | 100.00% | 100.00% | 78.79% |

## Confusion Matrix

| Label \ Predict | keep | not_keep |
| --- | ---: | ---: |
| keep | 107 | 35 |
| not_keep | 34 | 91 |
