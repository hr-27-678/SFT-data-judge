# Binary Scorer Eval Report (test)

Generated: 2026-05-05 12:53:13

## Run

- Run name: `scorer_binary_v3_conservative_qwen3_8b`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3_predict_test_greedy\generated_predictions.jsonl`
- Reference: `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\scorer_binary_sft_v3\scorer_binary_v3_conservative_test.jsonl`

## Summary

| Metric | Value |
| --- | --- |
| Records | 264 |
| Prediction JSON valid | 264/264 (100.00%) |
| Prediction schema valid | 264/264 (100.00%) |
| Label JSON valid | 264/264 (100.00%) |
| Accuracy | 203/264 (76.89%) |
| Keep precision | 119/144 (82.64%) |
| Keep recall | 119/155 (76.77%) |
| Keep F1 | 0.796 |
| Not-keep precision | 84/120 (70.00%) |
| Not-keep recall | 84/109 (77.06%) |
| Not-keep F1 | 0.734 |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 155 | 144 |
| not_keep | 109 | 120 |

## Per Source

| Source | Records | JSON valid | Schema valid | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| cot_zh | 129 | 100.00% | 100.00% | 71.32% |
| finetome | 103 | 100.00% | 100.00% | 77.67% |
| openmath_reasoning | 32 | 100.00% | 100.00% | 96.88% |

## Confusion Matrix

| Label \ Predict | keep | not_keep |
| --- | ---: | ---: |
| keep | 119 | 36 |
| not_keep | 25 | 84 |
