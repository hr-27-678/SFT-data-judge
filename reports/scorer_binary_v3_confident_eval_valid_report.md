# Binary Scorer Eval Report (valid)

Generated: 2026-05-05 12:53:13

## Run

- Run name: `scorer_binary_v3_confident_qwen3_8b`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_confident_qwen3_8b_lora_e3_predict_valid_greedy\generated_predictions.jsonl`
- Reference: `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\scorer_binary_sft_v3\scorer_binary_v3_confident_valid.jsonl`

## Summary

| Metric | Value |
| --- | --- |
| Records | 234 |
| Prediction JSON valid | 234/234 (100.00%) |
| Prediction schema valid | 234/234 (100.00%) |
| Label JSON valid | 234/234 (100.00%) |
| Accuracy | 170/234 (72.65%) |
| Keep precision | 123/168 (73.21%) |
| Keep recall | 123/142 (86.62%) |
| Keep F1 | 0.794 |
| Not-keep precision | 47/66 (71.21%) |
| Not-keep recall | 47/92 (51.09%) |
| Not-keep F1 | 0.595 |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 142 | 168 |
| not_keep | 92 | 66 |

## Per Source

| Source | Records | JSON valid | Schema valid | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| cot_zh | 109 | 100.00% | 100.00% | 65.14% |
| finetome | 94 | 100.00% | 100.00% | 77.66% |
| openmath_reasoning | 31 | 100.00% | 100.00% | 83.87% |

## Confusion Matrix

| Label \ Predict | keep | not_keep |
| --- | ---: | ---: |
| keep | 123 | 19 |
| not_keep | 45 | 47 |
