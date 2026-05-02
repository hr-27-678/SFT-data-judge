# Binary Scorer Experiment Report

Generated: 2026-05-01

## Goal

The original 1-5 scorer was format-stable but weak on calibration, especially for `maybe`.
This experiment converts the task into a confident binary filter:

- Teacher score 4/5 -> `keep`
- Teacher score 1/2 -> `not_keep`
- Teacher score 3 -> skipped

The goal is to test whether the student model is useful as a practical SFT data filter rather than a full teacher-score replica.

## Dataset

Built by `scripts/09_build_binary_scorer_sft.py`.

Output directory:

`SFT-DataJudge/data/labeled/scorer_binary_sft`

Dataset names:

- `scorer_binary_confident_1000_train`
- `scorer_binary_confident_1000_valid`
- `scorer_binary_confident_1000_test`

Counts:

| Split | Records |
| --- | ---: |
| train | 726 |
| valid | 95 |
| test | 96 |
| all | 917 |

Binary label distribution:

| Verdict | Records |
| --- | ---: |
| keep | 636 |
| not_keep | 281 |

Skipped:

| Reason | Records |
| --- | ---: |
| score_3_skipped | 83 |

## Training

Base model:

`Qwen/Qwen3-4B-Instruct-2507`

Adapter output:

`C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_4b_lora_e3`

Key settings:

| Setting | Value |
| --- | --- |
| finetuning | LoRA |
| epochs | 3 |
| learning rate | 1e-4 |
| effective batch | 16 |
| cutoff len | 4096 |
| eval strategy | steps |
| eval steps | 25 |
| decoding for eval/predict | greedy |

The first training command was interrupted by timeout after checkpoint 75. Training was resumed from `checkpoint-75` and completed. LLaMA-Factory selected `checkpoint-125` as the best checkpoint by `eval_loss`.

Final training/eval files include:

- `training_loss.png`
- `training_eval_loss.png`
- `train_results.json`
- `eval_results.json`
- `trainer_state.json`

## Evaluation

Evaluation was run with deterministic generation:

```text
--do_sample False
--temperature 1.0
--top_p 1.0
--max_new_tokens 64
```

Reports:

- `reports/scorer_binary_eval_valid_report.md`
- `reports/scorer_binary_eval_test_report.md`

## Results

### Valid

| Metric | Value |
| --- | ---: |
| JSON valid | 100.00% |
| Schema valid | 100.00% |
| Accuracy | 82.11% |
| Keep precision | 87.88% |
| Keep recall | 86.57% |
| Keep F1 | 0.872 |
| Not-keep precision | 68.97% |
| Not-keep recall | 71.43% |
| Not-keep F1 | 0.702 |

Per-source accuracy:

| Source | Accuracy |
| --- | ---: |
| cot_zh | 86.11% |
| finetome | 72.50% |
| openmath_reasoning | 94.74% |

### Test

| Metric | Value |
| --- | ---: |
| JSON valid | 100.00% |
| Schema valid | 100.00% |
| Accuracy | 76.04% |
| Keep precision | 87.10% |
| Keep recall | 78.26% |
| Keep F1 | 0.824 |
| Not-keep precision | 55.88% |
| Not-keep recall | 70.37% |
| Not-keep F1 | 0.623 |

Per-source accuracy:

| Source | Accuracy |
| --- | ---: |
| cot_zh | 63.89% |
| finetome | 77.50% |
| openmath_reasoning | 95.00% |

## Interpretation

The binary formulation is a better fit for the current dataset size.

Compared with the 1-5 scorer, the model is now useful as a conservative first-pass filter:

- It still outputs valid JSON reliably.
- `keep` precision is strong on both valid and test, around 87%.
- `not_keep` recall is around 70%, which is better than the previous drop recall, but still not strong enough for fully automatic rejection.
- `cot_zh` remains the weakest source on test, so the next data labeling round should be targeted rather than random.

## Recommendation

Use this binary scorer as the next project baseline.

Recommended immediate policy:

- Auto-keep can be tested on a small downstream subset, with spot checks.
- Do not auto-drop yet; route `not_keep` predictions to review or use them only for soft filtering.
- Next teacher labeling should target `cot_zh`, teacher score 2/4 boundary cases, and fluent-but-wrong outputs.
- Keep score 3 excluded from training for now. Reintroduce it later only after defining a clearer boundary policy.
