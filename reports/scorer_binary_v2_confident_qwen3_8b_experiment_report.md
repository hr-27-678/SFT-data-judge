# Qwen3-8B Binary Scorer V2 Confident Experiment Report

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-03 |
| Report type | Training + evaluation summary |
| Project stage | V2 binary scorer |
| Report status | Completed ablation |
| Model | `Qwen/Qwen3-8B` |
| Training method | LoRA |
| Data version | `scorer_binary_v2_confident` |
| Label policy | score 4/5 -> `keep`; score 1/2 -> `not_keep`; score 3 skipped |
| Current use | High-confidence keep filter and contrast model against v2 conservative |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | `Qwen/Qwen3-8B` |
| Data version | `scorer_binary_v2_confident` |
| Run name | `scorer_binary_v2_confident_qwen3_8b_lora_e3` |
| Training config | `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_e3.yaml` |
| Evaluation mode | Greedy deterministic valid/test prediction |
| Related split reports | `scorer_binary_v2_confident_eval_valid_report.md`, `scorer_binary_v2_confident_eval_test_report.md` |

## Objective

Train the v2 confident ablation after merging the starter teacher labels with
the targeted 1,200-example DeepSeek teacher-label batch.

This experiment uses the confident policy:

- Teacher score 4/5 -> `keep`
- Teacher score 1/2 -> `not_keep`
- Teacher score 3 -> skipped

The purpose is to test whether a cleaner keep/not_keep boundary produces a
better high-confidence keep model than the v2 conservative policy.

## Data Version

Dataset directory:

`data/labeled/scorer_binary_sft_v2`

Dataset:

| Split | Records |
| --- | ---: |
| Train | 1,572 |
| Valid | 197 |
| Test | 199 |

Full v2 confident label mix:

| Label | Records |
| --- | ---: |
| keep | 1,283 |
| not_keep | 685 |

Skipped score-3 records:

| Reason | Records |
| --- | ---: |
| score_3_skipped | 232 |

## Artifacts And Configs

Training and prediction configs:

- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_test.yaml`

Local adapter output:

`C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_confident_qwen3_8b_lora_e3`

Prediction outputs:

- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_confident_qwen3_8b_lora_e3_predict_valid_greedy`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_confident_qwen3_8b_lora_e3_predict_test_greedy`

## Training Setup And Outcome

Base model:

`Qwen/Qwen3-8B`

Key settings:

| Setting | Value |
| --- | --- |
| finetuning | LoRA |
| LoRA rank | 8 |
| LoRA target | all |
| epochs | 3 |
| learning rate | 1e-4 |
| effective batch | 16 |
| per-device train batch | 1 |
| gradient accumulation | 16 |
| cutoff len | 4096 |
| gradient checkpointing | true |
| dataloader workers | 0 |
| eval strategy | steps |
| eval/save steps | 50 |
| decoding for predict | greedy |

Training completed successfully:

- Total steps: 297
- Runtime: about 30.7 minutes
- Train loss: `0.29945938715629705`
- Best checkpoint: `checkpoint-150`
- Best valid eval loss: `0.050177909433841705`

Eval loss improved through step 150, worsened at step 200, then partially
recovered at step 250. The best checkpoint is therefore the mid-training
checkpoint, not the final checkpoint.

## Evaluation Summary

| Split | Dataset/Model | Accuracy | Keep precision | Keep recall | Keep F1 | Not-keep precision | Not-keep recall | Not-keep F1 | JSON valid |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Valid | v2 Qwen3-8B conservative | 74.55% | 73.86% | 86.92% | 0.799 | 76.06% | 57.45% | 0.655 | 100.00% |
| Valid | v2 Qwen3-8B confident | 76.14% | 77.85% | 89.23% | 0.832 | 70.83% | 50.75% | 0.591 | 100.00% |
| Test | v2 Qwen3-8B conservative | 79.91% | 79.22% | 90.37% | 0.844 | 81.43% | 64.04% | 0.717 | 100.00% |
| Test | v2 Qwen3-8B confident | 82.41% | 82.47% | 94.07% | 0.879 | 82.22% | 57.81% | 0.679 | 100.00% |

## Source Breakdown

Per-source accuracy for v2 confident:

| Split | cot_zh | finetome | openmath_reasoning |
| --- | ---: | ---: | ---: |
| Valid | 68.32% | 81.16% | 92.59% |
| Test | 77.67% | 83.58% | 96.55% |

## Confusion Matrix

Confusion matrix:

| Split | Keep -> keep | Keep -> not_keep | Not_keep -> keep | Not_keep -> not_keep |
| --- | ---: | ---: | ---: | ---: |
| Valid | 116 | 14 | 33 | 34 |
| Test | 127 | 8 | 27 | 37 |

## Interpretation

The v2 confident 8B model is a better high-confidence keep scorer than v2
conservative, but a weaker reject-boundary model.

What improved:

- Test accuracy improved from v2 conservative `79.91%` to `82.41%`.
- Test keep F1 improved from `0.844` to `0.879`.
- Test keep recall improved from `90.37%` to `94.07%`.
- JSON/schema validity stayed at `100%`.

What got worse:

- Test `not_keep` F1 dropped from v2 conservative `0.717` to `0.679`.
- Test `not_keep` recall dropped from `64.04%` to `57.81%`.
- The model predicts fewer `not_keep` examples: test predictions were
  154 keep / 45 not_keep, compared with v2 conservative's 154 keep /
  70 not_keep on its larger conservative test set.

## Recommended Next Actions

Do not choose a single v2 model as the only scorer yet. Use the two 8B v2
models as complementary tools:

- v2 confident -> high-confidence keep prioritization
- v2 conservative -> review routing and not_keep surfacing
- model disagreement -> best candidates for teacher relabeling

The next useful work is not training 4B v2 immediately. First run both 8B v2
models on the same larger unlabeled JSONL pool and inspect:

1. confident keep + conservative keep
2. confident keep + conservative not_keep
3. confident not_keep + conservative keep
4. confident not_keep + conservative not_keep

Those buckets will show whether the label policy difference is useful in real
candidate data and will produce a better targeted teacher-labeling batch.
