# Scorer Eval Report (test)

Generated: 2026-05-01 17:03:39

## Run

- Run name: `scorer_sft_1000_qwen3_4b_lora_e3`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_sft_1000_qwen3_4b_lora_e3_predict_test\generated_predictions.jsonl`
- Reference: `scorer_sft_1000_test.jsonl`

## Summary

| Metric | Value |
| --- | --- |
| Records | 104 |
| Prediction JSON valid | 104/104 (100.00%) |
| Prediction schema valid | 104/104 (100.00%) |
| Label JSON valid | 104/104 (100.00%) |
| Overall score exact accuracy | 45/104 (43.27%) |
| Overall score within +/-1 | 66/104 (63.46%) |
| Overall score MAE | 1.231 |
| Verdict accuracy | 62/104 (59.62%) |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 69 | 70 |
| maybe | 8 | 4 |
| drop | 27 | 30 |

| Score | Label | Prediction |
| --- | ---: | ---: |
| 1 | 13 | 11 |
| 2 | 14 | 19 |
| 3 | 8 | 4 |
| 4 | 14 | 7 |
| 5 | 55 | 63 |

## Per Source

| Source | Records | JSON valid | Schema valid | Score exact | Score +/-1 | Verdict acc |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cot_zh | 42 | 100.00% | 100.00% | 14.29% | 45.24% | 35.71% |
| finetome | 42 | 100.00% | 100.00% | 54.76% | 66.67% | 66.67% |
| openmath_reasoning | 20 | 100.00% | 100.00% | 80.00% | 95.00% | 95.00% |

## Verdict Confusion Matrix

| Label \ Predict | keep | maybe | drop |
| --- | --- | --- | --- |
| keep | 52 | 1 | 16 |
| maybe | 4 | 0 | 4 |
| drop | 14 | 3 | 10 |

## Score Confusion Matrix

| Label \ Predict | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| 1 | 2 | 3 | 1 | 1 | 6 |
| 2 | 3 | 2 | 2 | 2 | 5 |
| 3 | 3 | 1 | 0 | 0 | 4 |
| 4 | 1 | 5 | 1 | 0 | 7 |
| 5 | 2 | 8 | 0 | 4 | 41 |

## Notes

- Text-overlap metrics such as BLEU/Rouge are secondary for this task.
- The main acceptance checks are valid JSON, score calibration, and verdict accuracy.
- This run is format-stable, but the validation set shows weak `maybe` recall and a tendency to over-predict `keep`.
