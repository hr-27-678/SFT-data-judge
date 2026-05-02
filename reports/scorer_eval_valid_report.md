# Scorer Eval Report (valid)

Generated: 2026-05-01 16:41:52

## Run

- Run name: `scorer_sft_1000_qwen3_4b_lora_e3`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_sft_1000_qwen3_4b_lora_e3_predict_valid\generated_predictions.jsonl`
- Reference: `scorer_sft_1000_valid.jsonl`

## Summary

| Metric | Value |
| --- | --- |
| Records | 104 |
| Prediction JSON valid | 104/104 (100.00%) |
| Prediction schema valid | 104/104 (100.00%) |
| Label JSON valid | 104/104 (100.00%) |
| Overall score exact accuracy | 54/104 (51.92%) |
| Overall score within +/-1 | 75/104 (72.12%) |
| Overall score MAE | 0.971 |
| Verdict accuracy | 71/104 (68.27%) |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 67 | 74 |
| maybe | 9 | 2 |
| drop | 28 | 28 |

| Score | Label | Prediction |
| --- | ---: | ---: |
| 1 | 16 | 10 |
| 2 | 12 | 18 |
| 3 | 9 | 2 |
| 4 | 13 | 8 |
| 5 | 54 | 66 |

## Per Source

| Source | Records | JSON valid | Schema valid | Score exact | Score +/-1 | Verdict acc |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cot_zh | 42 | 100.00% | 100.00% | 38.10% | 64.29% | 57.14% |
| finetome | 42 | 100.00% | 100.00% | 52.38% | 73.81% | 71.43% |
| openmath_reasoning | 20 | 100.00% | 100.00% | 80.00% | 85.00% | 85.00% |

## Verdict Confusion Matrix

| Label \ Predict | keep | maybe | drop |
| --- | --- | --- | --- |
| keep | 56 | 0 | 11 |
| maybe | 7 | 0 | 2 |
| drop | 11 | 2 | 15 |

## Score Confusion Matrix

| Label \ Predict | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| 1 | 6 | 6 | 0 | 1 | 3 |
| 2 | 0 | 3 | 2 | 1 | 6 |
| 3 | 1 | 1 | 0 | 1 | 6 |
| 4 | 1 | 4 | 0 | 1 | 7 |
| 5 | 2 | 4 | 0 | 4 | 44 |

## Notes

- Text-overlap metrics such as BLEU/Rouge are secondary for this task.
- The main acceptance checks are valid JSON, score calibration, and verdict accuracy.
- This run is format-stable, but the validation set shows weak `maybe` recall and a tendency to over-predict `keep`.
