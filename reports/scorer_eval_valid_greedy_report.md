# Scorer Eval Report (valid_greedy)

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-01 17:32:42 |
| Report type | Split evaluation |
| Project stage | Original 1-5 scorer |
| Report status | Canonical greedy valid evaluation for 1-5 scorer |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | Qwen3-4B LoRA scorer |
| Data version | `scorer_sft_1000` |
| Split | valid_greedy |
| Evaluation mode | Greedy deterministic prediction |
| Run name | `scorer_sft_1000_qwen3_4b_lora_e3_greedy` |
| Label space | score 1-5 plus verdict `keep` / `maybe` / `drop` |
| Current use | Historical baseline showing why binary target was needed |

## Run Artifacts
- Run name: `scorer_sft_1000_qwen3_4b_lora_e3_greedy`
- Predictions: `C:\Users\haoran27\llamafactory_outputs\scorer_sft_1000_qwen3_4b_lora_e3_predict_valid_greedy\generated_predictions.jsonl`
- Reference: `SFT-DataJudge\data\labeled\scorer_sft\scorer_sft_1000_valid.jsonl`

## Metrics Summary
| Metric | Value |
| --- | --- |
| Records | 104 |
| Prediction JSON valid | 104/104 (100.00%) |
| Prediction schema valid | 104/104 (100.00%) |
| Label JSON valid | 104/104 (100.00%) |
| Overall score exact accuracy | 58/104 (55.77%) |
| Overall score within +/-1 | 78/104 (75.00%) |
| Overall score MAE | 0.923 |
| Verdict accuracy | 77/104 (74.04%) |

## Distribution

| Verdict | Label | Prediction |
| --- | ---: | ---: |
| keep | 67 | 74 |
| maybe | 9 | 0 |
| drop | 28 | 30 |

| Score | Label | Prediction |
| --- | ---: | ---: |
| 1 | 16 | 15 |
| 2 | 12 | 15 |
| 3 | 9 | 0 |
| 4 | 13 | 0 |
| 5 | 54 | 74 |

## Source Breakdown
| Source | Records | JSON valid | Schema valid | Score exact | Score +/-1 | Verdict acc |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cot_zh | 42 | 100.00% | 100.00% | 47.62% | 76.19% | 73.81% |
| finetome | 42 | 100.00% | 100.00% | 50.00% | 69.05% | 69.05% |
| openmath_reasoning | 20 | 100.00% | 100.00% | 85.00% | 85.00% | 85.00% |

## Verdict Confusion Matrix

| Label \ Predict | keep | maybe | drop |
| --- | --- | --- | --- |
| keep | 58 | 0 | 9 |
| maybe | 7 | 0 | 2 |
| drop | 9 | 0 | 19 |

## Score Confusion Matrix

| Label \ Predict | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| 1 | 7 | 7 | 0 | 0 | 2 |
| 2 | 1 | 4 | 0 | 0 | 7 |
| 3 | 1 | 1 | 0 | 0 | 7 |
| 4 | 2 | 0 | 0 | 0 | 11 |
| 5 | 4 | 3 | 0 | 0 | 47 |

## Notes

- Text-overlap metrics such as BLEU/Rouge are secondary for this task.
- The main acceptance checks are valid JSON, score calibration, and verdict accuracy.
- This run is format-stable, but the validation set shows weak `maybe` recall and a tendency to over-predict `keep`.
