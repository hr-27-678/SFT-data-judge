# Scorer Eval Report (test_greedy)

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-01 17:32:42 |
| Report type | Split evaluation |
| Project stage | Original 1-5 scorer |
| Report status | Canonical greedy test evaluation for 1-5 scorer |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | Qwen3-4B LoRA scorer |
| Data version | `scorer_sft_1000` |
| Split | test_greedy |
| Evaluation mode | Greedy deterministic prediction |
| Run name | `scorer_sft_1000_qwen3_4b_lora_e3_greedy` |
| Label space | score 1-5 plus verdict `keep` / `maybe` / `drop` |
| Current use | Historical baseline showing why binary target was needed |

## Run Artifacts
- Run name: `scorer_sft_1000_qwen3_4b_lora_e3_greedy`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_sft_1000_qwen3_4b_lora_e3_predict_test_greedy\generated_predictions.jsonl`
- Reference: `SFT-DataJudge\data\labeled\scorer_sft\scorer_sft_1000_test.jsonl`

## Metrics Summary
| Metric | Value |
| --- | --- |
| Records | 104 |
| Prediction JSON valid | 104/104 (100.00%) |
| Prediction schema valid | 104/104 (100.00%) |
| Label JSON valid | 104/104 (100.00%) |
| Overall score exact accuracy | 59/104 (56.73%) |
| Overall score within +/-1 | 73/104 (70.19%) |
| Overall score MAE | 1.019 |
| Verdict accuracy | 72/104 (69.23%) |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 69 | 76 |
| maybe | 8 | 0 |
| drop | 27 | 28 |

| Score | Label | Prediction |
| --- | ---: | ---: |
| 1 | 13 | 12 |
| 2 | 14 | 16 |
| 3 | 8 | 0 |
| 4 | 14 | 0 |
| 5 | 55 | 76 |

## Source Breakdown
| Source | Records | JSON valid | Schema valid | Score exact | Score +/-1 | Verdict acc |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cot_zh | 42 | 100.00% | 100.00% | 35.71% | 57.14% | 54.76% |
| finetome | 42 | 100.00% | 100.00% | 64.29% | 71.43% | 71.43% |
| openmath_reasoning | 20 | 100.00% | 100.00% | 85.00% | 95.00% | 95.00% |

## Verdict Confusion Matrix

| Label \ Predict | keep | maybe | drop |
| --- | --- | --- | --- |
| keep | 59 | 0 | 10 |
| maybe | 3 | 0 | 5 |
| drop | 14 | 0 | 13 |

## Score Confusion Matrix

| Label \ Predict | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| 1 | 3 | 2 | 0 | 0 | 8 |
| 2 | 2 | 6 | 0 | 0 | 6 |
| 3 | 4 | 1 | 0 | 0 | 3 |
| 4 | 0 | 5 | 0 | 0 | 9 |
| 5 | 3 | 2 | 0 | 0 | 50 |

## Notes

- Text-overlap metrics such as BLEU/Rouge are secondary for this task.
- The main acceptance checks are valid JSON, score calibration, and verdict accuracy.
- This run is format-stable, but the validation set shows weak `maybe` recall and a tendency to over-predict `keep`.
