# Qwen3-8B Binary Scorer V1 Experiment Report

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-02 |
| Report type | Training + evaluation summary |
| Project stage | V1 binary confident scorer |
| Report status | Qwen3-8B capacity check |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | `Qwen/Qwen3-8B` |
| Data version | `scorer_binary_confident_1000` |
| Run name | `scorer_binary_confident_1000_qwen3_8b_lora_e3` |
| Label policy | score 4/5 -> `keep`; score 1/2 -> `not_keep`; score 3 skipped |
| Current use | Capacity check before v2 targeted data training |

## Goal

Test whether upgrading the binary confident scorer from Qwen3-4B to Qwen3-8B
improves the v1 dataset baseline before the targeted 1,200-example teacher
labels are ready.

This is a capacity check, not the final v2 experiment.

## Dataset

Same binary confident v1 dataset as the Qwen3-4B baseline:

- Train: `scorer_binary_confident_1000_train` (726 records)
- Valid: `scorer_binary_confident_1000_valid` (95 records)
- Test: `scorer_binary_confident_1000_test` (96 records)

The mapping is unchanged:

- Teacher score 4/5 -> `keep`
- Teacher score 1/2 -> `not_keep`
- Teacher score 3 -> skipped

## Configs

Training and prediction configs:

- `configs/llamafactory/scorer_binary_confident_1000_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_confident_1000_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_confident_1000_qwen3_8b_lora_predict_test.yaml`

Local adapter output:

`C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_8b_lora_e3`

Prediction outputs:

- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_8b_lora_e3_predict_valid_greedy`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_8b_lora_e3_predict_test_greedy`

## Training

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
| eval steps | 25 |
| decoding for eval/predict | greedy |

The first launch used `dataloader_num_workers: 4` and failed on Windows during
CUDA tensor sharing with an out-of-memory error. The run was restarted with
`dataloader_num_workers: 0`, which completed successfully.

Training completed in about 15.5 minutes.

Best checkpoint by `eval_loss`:

- `checkpoint-100`
- Best valid eval loss: `0.05344891920685768`

## Results

Compared with the Qwen3-4B v1 binary confident baseline:

| Split | Model | Accuracy | Keep precision | Keep recall | Keep F1 | Not-keep precision | Not-keep recall | Not-keep F1 | JSON valid |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Valid | Qwen3-4B | 82.11% | 87.88% | 86.57% | 0.872 | 68.97% | 71.43% | 0.702 | 100.00% |
| Valid | Qwen3-8B | 77.89% | 81.08% | 89.55% | 0.851 | 66.67% | 50.00% | 0.571 | 100.00% |
| Test | Qwen3-4B | 76.04% | 87.10% | 78.26% | 0.824 | 55.88% | 70.37% | 0.623 | 100.00% |
| Test | Qwen3-8B | 84.38% | 83.75% | 97.10% | 0.899 | 87.50% | 51.85% | 0.651 | 100.00% |

Per-source accuracy:

| Split | Model | cot_zh | finetome | openmath_reasoning |
| --- | --- | ---: | ---: | ---: |
| Valid | Qwen3-4B | 86.11% | 72.50% | 94.74% |
| Valid | Qwen3-8B | 75.00% | 75.00% | 89.47% |
| Test | Qwen3-4B | 63.89% | 77.50% | 95.00% |
| Test | Qwen3-8B | 80.56% | 85.00% | 90.00% |

## Interpretation

The 8B model is not a clean universal win on v1.

What improved:

- Test accuracy increased from 76.04% to 84.38%.
- Test keep recall increased from 78.26% to 97.10%.
- Test `cot_zh` accuracy improved from 63.89% to 80.56%.
- JSON/schema validity stayed at 100%.

What regressed or needs caution:

- Valid accuracy dropped from 82.11% to 77.89%.
- Valid not_keep F1 dropped from 0.702 to 0.571.
- Test not_keep recall dropped from 70.37% to 51.85%.
- The 8B model predicts `keep` more often: 80/96 test predictions vs 62/96 for
  the 4B baseline.

This means the 8B v1 adapter is a stronger keep-first scorer, but not yet a
better automatic rejection model. The higher test accuracy mostly comes from
recovering keep examples, while the reject boundary is still under-trained.

## Recommendation

Use Qwen3-8B as the main candidate for v2 training once the targeted 1,200
teacher labels are ready, but do not use the v1 8B model for automatic dropping.

For v2, prioritize:

- More `not_keep` examples from targeted `cot_zh` and `finetome` weaknesses.
- A conservative variant where score 3 is mapped to `not_keep` or review.
- Comparing 8B v2 against the 4B v1 and 8B v1 baselines with the same greedy
  valid/test evaluation.
