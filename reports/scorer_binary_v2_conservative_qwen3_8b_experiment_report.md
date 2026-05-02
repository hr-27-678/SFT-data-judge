# Qwen3-8B Binary Scorer V2 Conservative Experiment Report

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-02 |
| Report type | Training + evaluation summary |
| Project stage | V2 binary scorer |
| Report status | Current main candidate |
| Model | `Qwen/Qwen3-8B` |
| Training method | LoRA |
| Data version | `scorer_binary_v2_conservative` |
| Label policy | score 4/5 -> `keep`; score 1/2/3 -> `not_keep` |
| Current use | Quality-first scorer for prioritization and review routing |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | `Qwen/Qwen3-8B` |
| Data version | `scorer_binary_v2_conservative` |
| Run name | `scorer_binary_v2_conservative_qwen3_8b_lora_e3` |
| Training config | `configs/llamafactory/scorer_binary_v2_conservative_qwen3_8b_lora_e3.yaml` |
| Evaluation mode | Greedy deterministic valid/test prediction |
| Related split reports | `scorer_binary_v2_conservative_eval_valid_report.md`, `scorer_binary_v2_conservative_eval_test_report.md` |

## Objective

Train the main v2 binary scorer candidate after merging the starter teacher
labels with the targeted 1,200-example DeepSeek teacher-label batch.

This experiment uses the conservative policy:

- Teacher score 4/5 -> `keep`
- Teacher score 1/2/3 -> `not_keep`

The purpose is quality-first SFT filtering. Ambiguous score-3 samples should not
be auto-kept.

## Data Version

Dataset directory:

`data/labeled/scorer_binary_sft_v2`

Dataset:

| Split | Records |
| --- | ---: |
| Train | 1,752 |
| Valid | 224 |
| Test | 224 |

Full v2 conservative label mix:

| Label | Records |
| --- | ---: |
| keep | 1,283 |
| not_keep | 917 |

Compared with v1, this is not a pure model-capacity comparison: the dataset is
larger, includes targeted weak/boundary examples, and maps score 3 to
`not_keep`.

## Artifacts And Configs

Training and prediction configs:

- `configs/llamafactory/scorer_binary_v2_conservative_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_v2_conservative_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_v2_conservative_qwen3_8b_lora_predict_test.yaml`

Local adapter output:

`C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_conservative_qwen3_8b_lora_e3`

Prediction outputs:

- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_conservative_qwen3_8b_lora_e3_predict_valid_greedy`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_conservative_qwen3_8b_lora_e3_predict_test_greedy`

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

- Total steps: 330
- Runtime: about 31.9 minutes
- Train loss: `0.2763112103397196`
- Best checkpoint: `checkpoint-250`
- Best valid eval loss: `0.055845100432634354`

Eval loss stayed stable near the end, with the best value at step 250 and only
minor movement at step 300.

## Evaluation Summary

| Split | Dataset/Model | Accuracy | Keep precision | Keep recall | Keep F1 | Not-keep precision | Not-keep recall | Not-keep F1 | JSON valid |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Valid | v1 Qwen3-4B confident | 82.11% | 87.88% | 86.57% | 0.872 | 68.97% | 71.43% | 0.702 | 100.00% |
| Valid | v1 Qwen3-8B confident | 77.89% | 81.08% | 89.55% | 0.851 | 66.67% | 50.00% | 0.571 | 100.00% |
| Valid | v2 Qwen3-8B conservative | 74.55% | 73.86% | 86.92% | 0.799 | 76.06% | 57.45% | 0.655 | 100.00% |
| Test | v1 Qwen3-4B confident | 76.04% | 87.10% | 78.26% | 0.824 | 55.88% | 70.37% | 0.623 | 100.00% |
| Test | v1 Qwen3-8B confident | 84.38% | 83.75% | 97.10% | 0.899 | 87.50% | 51.85% | 0.651 | 100.00% |
| Test | v2 Qwen3-8B conservative | 79.91% | 79.22% | 90.37% | 0.844 | 81.43% | 64.04% | 0.717 | 100.00% |

## Source Breakdown

Per-source accuracy for v2 conservative:

| Split | cot_zh | finetome | openmath_reasoning |
| --- | ---: | ---: | ---: |
| Valid | 67.21% | 83.56% | 82.76% |
| Test | 76.23% | 79.45% | 96.55% |

## Confusion Matrix

Confusion matrix:

| Split | Keep -> keep | Keep -> not_keep | Not_keep -> keep | Not_keep -> not_keep |
| --- | ---: | ---: | ---: | ---: |
| Valid | 113 | 17 | 40 | 54 |
| Test | 122 | 13 | 32 | 57 |

## Interpretation

The v2 conservative 8B model is a better quality-first candidate than the v1 8B
capacity check.

What improved:

- Test `not_keep` F1 improved from v1 8B `0.651` to v2 conservative `0.717`.
- Test `not_keep` recall improved from v1 8B `51.85%` to `64.04%`.
- Test `not_keep` precision stayed strong at `81.43%`.
- JSON/schema validity stayed at `100%`.
- The model is less extremely keep-biased than v1 8B: test predictions were
  154 keep / 70 not_keep instead of v1 8B's 80 keep / 16 not_keep on a much
  smaller test set.

What needs caution:

- Valid accuracy is lower than both v1 baselines.
- Keep F1 is lower than v1 8B, which is expected because score-3 and targeted
  boundary cases make the task harder.
- `cot_zh` is still the weakest source, especially on valid accuracy.
- The model still misses 32/89 test `not_keep` examples, so it should not be
  used for blind automatic deletion yet.

## Recommended Next Actions

Use this adapter as the current main v2 candidate for scoring and prioritizing
candidate data, especially for surfacing likely low-quality examples.

Do not yet use it as an irreversible auto-dropper. A practical policy is:

- high-confidence keep -> can be prioritized for SFT
- predicted not_keep -> review, teacher relabel, or soft filtering
- uncertain/contradictory cases -> send to the teacher model

Next useful experiment:

1. Train Qwen3-8B on `scorer_binary_v2_confident` as an ablation.
2. Compare whether skipping score 3 gives better keep precision without losing
   too much rejection strength.
3. Add an inference script for unlabeled JSONL pools with resume support and
   source-wise summary reporting.
