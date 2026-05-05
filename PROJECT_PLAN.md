# Project Plan

Last updated: 2026-05-05

## Resume Here

This is the first file a future Codex session should read.

Current repository:

- Local path: `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge`
- GitHub: `https://github.com/hr-27-678/SFT-data-judge.git`
- Branch: `main`
- Initial pushed commit: `7b701c6 Initial project cleanup and scorer reports`

Recommended reading order for a fresh session:

1. `PROJECT_PLAN.md`
2. `PROJECT_FILE_INVENTORY.md`
3. `reports/README.md`
4. `scripts/README.md`
5. `reports/scorer_binary_experiment_report.md`
6. `reports/scorer_binary_v2_conservative_qwen3_8b_experiment_report.md`
7. `reports/scorer_binary_v2_confident_qwen3_8b_experiment_report.md`
8. `reports/teacher_candidates_all_v2_model_agreement_report.md`
9. `reports/training_lessons_and_notes.md`
10. `reports/scorer_binary_v3_qwen3_8b_experiment_report.md`
11. `reports/scorer_binary_v3_conservative_eval_test_report.md`
12. `reports/scorer_binary_v3_confident_eval_test_report.md`
13. `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_conservative_report.md`
14. `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_confident_report.md`
15. `reports/teacher_candidates_all_v2_priority_teacher_analysis_report.md`
16. `reports/teacher_sampling_v2_active_pilot_001_report.md`
17. `reports/teacher_sampling_targeted_1200_report.md`

The school computer does not preserve conversation progress, so this file should
be treated as the project memory.

## Current State Snapshot

The project has completed one full starter loop:

1. sampled 1,000 teacher-label candidates
2. labeled them with the teacher model
3. built original 1-5 scorer SFT data
4. trained a Qwen3-4B LoRA scorer
5. evaluated valid/test behavior
6. found that the 1-5 score task was too fuzzy around score 3 / `maybe`
7. rebuilt a binary confident dataset
8. trained and evaluated the binary confident scorer
9. organized project files and pushed the current repo to GitHub
10. trained and evaluated a Qwen3-8B v1 capacity-check scorer on the same
    binary confident dataset
11. labeled the targeted 1,200-example teacher batch
12. merged starter + targeted labels into v2 binary scorer datasets
13. trained and evaluated the Qwen3-8B v2 conservative scorer
14. standardized all markdown reports under `reports/` with consistent
    metadata/context headers and common section names
15. implemented `scripts/12_infer_binary_scorer.py` for batch scorer inference
    on unlabeled JSONL pools with resume support and summary reporting
16. trained and evaluated the Qwen3-8B v2 confident ablation
17. ran both Qwen3-8B v2 scorers on the 3,600-row teacher-candidate pool and
    built a conservative/confident agreement report plus a teacher-review
    priority queue
18. implemented `scripts/13_build_teacher_review_batch.py` and built the first
    deduplicated active-learning teacher batch, `v2active001`
19. analyzed `v2active001` labels and joined all available teacher labels back
    to the 1,215-record priority queue with
    `scripts/14_analyze_teacher_review_priority.py`
20. built v3 binary scorer datasets from starter + targeted + `v2active001`
    teacher labels
21. prepared Qwen3-8B v3 conservative/confident LLaMA-Factory training configs
    and matching greedy valid/test prediction configs
22. trained and evaluated both Qwen3-8B v3 scorer variants

The current best direction is the binary scorer family, not the original 1-5
scorer.

On 2026-05-02, the targeted teacher-labeling batch was completed with DeepSeek.
Four initial API/parse failures were retried, then merged into the canonical
`data/labeled/teacher_judge/targeted_1200_teacher_labels.jsonl`, giving
1,200/1,200 valid teacher labels.

On 2026-05-03, the Qwen3-8B v2 confident ablation was restarted from scratch
with `overwrite_output_dir: true`, trained successfully, and evaluated on
valid/test with greedy decoding. Treat the current local adapter as complete.

On 2026-05-03, both Qwen3-8B v2 scorers were run on
`data/splits/teacher_judge/teacher_candidates_all.jsonl` (3,600 records).
They agreed on 3,327 / 3,600 records (92.42%) and disagreed on 273 records.
The strongest teacher-labeling queue is the 273 disagreements plus the 646
both-not-keep records, before expanding to the full 188,103-row processed pool.

On 2026-05-04, the 1,215-record pilot priority queue was deduplicated against
existing teacher labels using the original sample `id` only. Do not deduplicate
across batches by `teacher_sample_id`; those ids can be reused by different
sampling runs. The result:

- 827 priority records already have teacher labels from the starter/targeted
  batches.
- 388 priority records were unlabeled at selection time and were written as
  batch `v2active001`.
- Dry-run teacher prompts were rendered to
  `data/labeled/teacher_judge/v2active001/v2active001_teacher_prompts.jsonl`.

After teacher labeling and retry, `v2active001` has 388 deduplicated valid
labels. The raw output file has 390 rows because the two failed rows were
retried with `--resume` and appended; downstream analysis keeps the last record
per original sample `id`. The 1,215-record priority queue now has 1,215 valid
teacher labels joined from starter, targeted, and `v2active001`; the current
analysis report is
`reports/teacher_candidates_all_v2_priority_teacher_analysis_report.md`.

On 2026-05-04, v3 binary scorer datasets were generated in
`data/labeled/scorer_binary_sft_v3/` from the starter, targeted, and
`v2active001` teacher labels:

- `scorer_binary_v3_conservative`: 2,588 total records, with score 3 mapped to
  `not_keep` (train 2,057 / valid 267 / test 264).
- `scorer_binary_v3_confident`: 2,326 total records, with score 3 skipped
  (train 1,855 / valid 234 / test 237).
- Both variants use the same binary prompt/schema as v2 and have
  `dataset_info.json` entries ready for LLaMA-Factory.

On 2026-05-05, both v3 Qwen3-8B LoRA variants were trained and evaluated with
greedy valid/test prediction:

- v3 conservative best checkpoint: `checkpoint-250`, best valid eval loss
  `0.05724373087286949`.
- v3 confident best checkpoint: `checkpoint-100`, best valid eval loss
  `0.053558845072984695`.
- v3 conservative test: accuracy 76.89%, keep F1 0.796, not_keep F1 0.734,
  not_keep recall 77.06%.
- v3 confident test: accuracy 78.90%, keep F1 0.851, not_keep F1 0.638,
  not_keep recall 53.66%.
- Current report:
  `reports/scorer_binary_v3_qwen3_8b_experiment_report.md`.

## Status Board

Completed and usable:

- Qwen3-4B v1 binary confident baseline.
- Qwen3-8B v1 binary confident capacity check.
- Targeted 1,200 DeepSeek teacher labels.
- V2 binary scorer datasets:
  - `scorer_binary_v2_confident`
  - `scorer_binary_v2_conservative`
- Qwen3-8B v2 conservative training, valid/test prediction, evaluation, and
  experiment report.
- Qwen3-8B v2 confident training, valid/test prediction, evaluation, and
  experiment report.
- Batch inference script:
  `scripts/12_infer_binary_scorer.py`
- Active-learning teacher batch script:
  `scripts/13_build_teacher_review_batch.py`
- Priority teacher analysis script:
  `scripts/14_analyze_teacher_review_priority.py`
- 3,600-row teacher-candidate pilot inference with both Qwen3-8B v2 adapters:
  - `reports/teacher_candidates_all_v2_conservative_inference_report.md`
  - `reports/teacher_candidates_all_v2_confident_inference_report.md`
  - `reports/teacher_candidates_all_v2_model_agreement_report.md`
  - `data/scored/teacher_candidates_all_v2_teacher_review_priority.jsonl`
  - `data/scored/teacher_candidates_all_v2_teacher_review_top919.jsonl`
  - `data/labeled/teacher_judge/v2_pilot_top919/v2_pilot_top919_teacher_prompts.jsonl`
- Deduplicated first active-learning teacher batch:
  - `reports/teacher_sampling_v2_active_pilot_001_report.md`
  - `reports/teacher_label_report_v2active001.md`
  - `reports/teacher_candidates_all_v2_priority_teacher_analysis_report.md`
  - `data/splits/teacher_judge/v2_active_pilot_001/v2active001_teacher_candidates_all.jsonl`
  - `data/labeled/teacher_judge/v2active001/v2active001_teacher_prompts.jsonl`
- V3 binary scorer datasets:
  - `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_conservative_report.md`
  - `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_confident_report.md`
  - `data/labeled/scorer_binary_sft_v3/dataset_info.json`
- V3 Qwen3-8B LLaMA-Factory configs:
  - `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_e3.yaml`
  - `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_predict_valid.yaml`
  - `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_predict_test.yaml`
  - `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_e3.yaml`
  - `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_predict_valid.yaml`
  - `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_predict_test.yaml`
- Qwen3-8B v3 conservative/confident training, valid/test prediction,
  evaluation, and experiment report:
  - `reports/scorer_binary_v3_qwen3_8b_experiment_report.md`
  - `reports/scorer_binary_v3_conservative_eval_valid_report.md`
  - `reports/scorer_binary_v3_conservative_eval_test_report.md`
  - `reports/scorer_binary_v3_confident_eval_valid_report.md`
  - `reports/scorer_binary_v3_confident_eval_test_report.md`
  - `data/eval/scorer_binary_v3_conservative_eval_valid_metrics.json`
  - `data/eval/scorer_binary_v3_conservative_eval_test_metrics.json`
  - `data/eval/scorer_binary_v3_confident_eval_valid_metrics.json`
  - `data/eval/scorer_binary_v3_confident_eval_test_metrics.json`
- Training lessons note:
  `reports/training_lessons_and_notes.md`

Current main candidate:

- `Qwen/Qwen3-8B` LoRA on `scorer_binary_v3_conservative`
- Local adapter:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3`
- Use it for prioritization, review routing, and selecting teacher relabeling
  candidates. Do not use it for blind automatic deletion.

Current companion candidate:

- `Qwen/Qwen3-8B` LoRA on `scorer_binary_v3_confident`
- Local adapter:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_confident_qwen3_8b_lora_e3`
- Use it as a high-confidence keep filter and as a contrast model against v3
  conservative. Disagreements between the two v3 8B models are useful
  teacher-relabeling candidates.

Best next action:

- Run both v3 scorers on a larger unlabeled pool, exclude all already
  teacher-labeled original sample `id`s, then build the next active-learning
  teacher batch from v3 disagreements, conservative `not_keep` predictions,
  and rule/model conflicts.

## Goal

Build a small local data-quality scorer for supervised fine-tuning samples. The
scorer should imitate a stronger teacher model well enough to filter or
prioritize future SFT data at lower cost.

## Current Pipeline

1. Normalize source datasets into a shared schema.
2. Apply light rule-based quality checks.
3. Sample a 1,000-example starter set with source-aware allocation.
4. Label the starter set with a teacher model.
5. Convert teacher labels into LLaMA-Factory SFT format.
6. Train a Qwen3-4B LoRA scorer.
7. Evaluate on held-out valid/test splits.
8. Simplify the target into a binary confident scorer because the original
   1-5 score task had ambiguous middle labels.
9. Add targeted teacher labels for known weak/boundary areas.
10. Build v2 binary datasets with both confident and conservative score-3
    policies.
11. Train and evaluate Qwen3-8B v2 conservative as the current quality-first
    candidate.
12. Train and evaluate Qwen3-8B v2 confident as the high-confidence keep
    ablation.
13. Run both Qwen3-8B v2 scorers on the 3,600-row teacher-candidate pilot pool.
14. Build and label the deduplicated active-learning batch `v2active001`.
15. Build v3 binary datasets from starter + targeted + `v2active001`.
16. Train and evaluate Qwen3-8B v3 conservative/confident variants.
17. Next: run v3 scorer inference on a larger unlabeled pool and build
    `v2active002`/next teacher-review batch.

## Data Sources

- `cot_zh`: Chinese chain-of-thought style reasoning data.
- `finetome`: broad instruction-following data.
- `openmath_reasoning`: math reasoning data.

The starter split is intentionally not equal-weighted. It keeps the source mix
closer to the project goal and gives enough examples to compare behavior by
source.

## Completed Artifacts

Teacher-label artifacts:

- `reports/teacher_sampling_starter_1000_report.md`
- `reports/teacher_label_report_1000.md`
- `data/labeled/teacher_judge/pilot_teacher_labels.jsonl`
- `data/labeled/teacher_judge/starter_1000_teacher_labels.jsonl`

Original 1-5 scorer artifacts:

- `data/labeled/scorer_sft/scorer_sft_report.md`
- `reports/scorer_eval_valid_greedy_report.md`
- `reports/scorer_eval_test_greedy_report.md`
- `reports/scorer_error_analysis_greedy_report.md`

Binary confident scorer artifacts:

- `data/labeled/scorer_binary_sft/scorer_binary_confident_1000_report.md`
- `reports/scorer_binary_eval_valid_report.md`
- `reports/scorer_binary_eval_test_report.md`
- `reports/scorer_binary_experiment_report.md`

Qwen3-8B v1 capacity-check artifacts:

- `configs/llamafactory/scorer_binary_confident_1000_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_confident_1000_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_confident_1000_qwen3_8b_lora_predict_test.yaml`
- `reports/scorer_binary_qwen3_8b_v1_experiment_report.md`
- `reports/scorer_binary_eval_valid_qwen3_8b_v1_report.md`
- `reports/scorer_binary_eval_test_qwen3_8b_v1_report.md`

Next teacher-labeling batch artifacts:

- `scripts/11_build_targeted_teacher_batch.py`
- `reports/teacher_sampling_targeted_1200_report.md`
- `reports/teacher_label_report_targeted_1200.md`
- `data/splits/teacher_judge/targeted_1200/targeted_teacher_candidates_all.jsonl`
- `data/labeled/teacher_judge/targeted_1200_teacher_prompts.jsonl`
- `data/labeled/teacher_judge/targeted_1200_teacher_labels.jsonl`

V2 binary scorer dataset artifacts:

- `data/labeled/scorer_binary_sft_v2/scorer_binary_v2_confident_report.md`
- `data/labeled/scorer_binary_sft_v2/scorer_binary_v2_conservative_report.md`
- `data/labeled/scorer_binary_sft_v2/dataset_info.json`

V3 binary scorer dataset artifacts:

- `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_confident_report.md`
- `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_conservative_report.md`
- `data/labeled/scorer_binary_sft_v3/dataset_info.json`

Qwen3-8B v3 training/evaluation configs:

- `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_predict_test.yaml`
- `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_predict_test.yaml`

Qwen3-8B v2 conservative artifacts:

- `configs/llamafactory/scorer_binary_v2_conservative_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_v2_conservative_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_v2_conservative_qwen3_8b_lora_predict_test.yaml`
- `reports/scorer_binary_v2_conservative_qwen3_8b_experiment_report.md`
- `reports/scorer_binary_v2_conservative_eval_valid_report.md`
- `reports/scorer_binary_v2_conservative_eval_test_report.md`
- `data/eval/scorer_binary_v2_conservative_eval_valid_metrics.json`
- `data/eval/scorer_binary_v2_conservative_eval_test_metrics.json`

Qwen3-8B v2 confident artifacts:

- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_test.yaml`
- `reports/scorer_binary_v2_confident_qwen3_8b_experiment_report.md`
- `reports/scorer_binary_v2_confident_eval_valid_report.md`
- `reports/scorer_binary_v2_confident_eval_test_report.md`
- `data/eval/scorer_binary_v2_confident_eval_valid_metrics.json`
- `data/eval/scorer_binary_v2_confident_eval_test_metrics.json`

Teacher-candidate v2 inference artifacts:

- `reports/teacher_candidates_all_v2_conservative_inference_report.md`
- `reports/teacher_candidates_all_v2_confident_inference_report.md`
- `reports/teacher_candidates_all_v2_model_agreement_report.md`
- `data/scored/teacher_candidates_all_v2_conservative_predictions.jsonl`
- `data/scored/teacher_candidates_all_v2_confident_predictions.jsonl`
- `data/scored/teacher_candidates_all_v2_model_agreement_metrics.json`
- `data/scored/teacher_candidates_all_v2_model_disagreements.jsonl`
- `data/scored/teacher_candidates_all_v2_teacher_review_priority.jsonl`
- `data/scored/teacher_candidates_all_v2_teacher_review_top919.jsonl`
- `data/labeled/teacher_judge/v2_pilot_top919/v2_pilot_top919_teacher_prompts.jsonl`

Learning and handoff notes:

- `reports/training_lessons_and_notes.md`
- All `reports/*.md` files now use a common report header:
  `Report Metadata` followed by `Experiment Context`.

## Current Best Result

The Qwen3-8B v3 conservative scorer is the current main quality-first candidate.
The Qwen3-8B v3 confident scorer is the companion high-confidence keep filter.
The Qwen3-4B v1 binary confident scorer remains the compact baseline.

Qwen3-8B v3 conservative (current main candidate, `scorer_binary_v3_conservative`):

| Split | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | ---: | ---: | ---: | ---: | ---: |
| Valid | 74.16% | 0.756 | 0.725 | 72.80% | 100% |
| Test | 76.89% | 0.796 | 0.734 | 77.06% | 100% |

Interpretation:

- Best reject-boundary metrics to date: test not_keep F1 0.734 and not_keep
  recall 77.06%.
- Prediction distribution is balanced: 144 keep / 120 not_keep on test split.
- Per-source test accuracy: cot_zh 71.32%, finetome 77.67%, openmath 96.88%.
  cot_zh remains the weakest source.
- Use for review routing, hard-negative mining, and teacher-relabeling
  prioritization. Do not use for blind automatic deletion.

Qwen3-8B v3 confident (companion high-confidence keep filter, `scorer_binary_v3_confident`):

| Split | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | ---: | ---: | ---: | ---: | ---: |
| Valid | 72.65% | 0.794 | 0.595 | 51.09% | 100% |
| Test | 78.90% | 0.851 | 0.638 | 53.66% | 100% |

Interpretation:

- Keep recall 92.26% on test; useful for prioritizing likely keep examples.
- Not-keep recall only 53.66%; do not use as a reject model.
- Disagreements between v3 conservative and v3 confident are the highest-value
  teacher-relabeling candidates.

Historical results for reference:

Qwen3-4B v1 binary confident (compact baseline):

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 82.11% | 0.872 | 0.702 | 100% |
| Test | 76.04% | 0.824 | 0.623 | 100% |

Qwen3-8B v1 binary confident capacity check (same 1,000-example dataset):

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 77.89% | 0.851 | 0.571 | 100% |
| Test | 84.38% | 0.899 | 0.651 | 100% |

- Test not_keep recall was only 51.85%; too keep-biased for reject routing.

Qwen3-8B v2 conservative:

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 74.55% | 0.799 | 0.655 | 100% |
| Test | 79.91% | 0.844 | 0.717 | 100% |

- Test not_keep recall 64.04%. Superseded by v3 conservative.

Qwen3-8B v2 confident:

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 76.14% | 0.832 | 0.591 | 100% |
| Test | 82.41% | 0.879 | 0.679 | 100% |

- Test not_keep recall 57.81%. Superseded by v3 confident.

Training notes:

- `reports/training_lessons_and_notes.md` summarizes the practical training
  settings, observed model behavior, Windows/LLaMA-Factory pitfalls, metric
  interpretation, and recommended next learning experiments.

V2 binary scorer datasets are now ready:

| Dataset | Records | Train | Valid | Test | Keep | Not-keep | Score 3 Policy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `scorer_binary_v2_confident` | 1,968 | 1,572 | 197 | 199 | 1,283 | 685 | skipped |
| `scorer_binary_v2_conservative` | 2,200 | 1,752 | 224 | 224 | 1,283 | 917 | mapped to `not_keep` |

`scorer_binary_v2_conservative` was used as the first v2 training target
because the project policy is quality-first and score 3 should not be
auto-kept.

V3 binary scorer datasets (trained and evaluated on 2026-05-05):

| Dataset | Records | Train | Valid | Test | Keep | Not-keep | Score 3 Policy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `scorer_binary_v3_confident` | 2,326 | 1,855 | 234 | 237 | 1,438 | 888 | skipped |
| `scorer_binary_v3_conservative` | 2,588 | 2,057 | 267 | 264 | 1,438 | 1,150 | mapped to `not_keep` |

Compared with v2, v3 adds the 388 teacher-confirmed active-learning examples
from `v2active001`. V3 conservative has now been trained and is the current
main quality-first scorer; v3 confident is the companion high-confidence keep
ablation.

Local model artifacts are not committed to GitHub. The important local adapter
paths are:

- Original 1-5 scorer:
  `C:\Users\haoran27\llamafactory_outputs\scorer_sft_1000_qwen3_4b_lora_e3`
- Binary confident scorer:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_4b_lora_e3`
- Qwen3-8B binary confident v1 capacity check:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_8b_lora_e3`
- Qwen3-8B binary conservative v2:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_conservative_qwen3_8b_lora_e3`
- Qwen3-8B binary confident v2:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_confident_qwen3_8b_lora_e3`
- Qwen3-8B binary conservative v3:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3`
- Qwen3-8B binary confident v3:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_confident_qwen3_8b_lora_e3`

Use the binary setup for future scorer experiments. The 4B adapter is the
compact baseline, while the v3 conservative 8B adapter is the current main
quality-first candidate and the v3 confident 8B adapter is the companion
high-confidence keep candidate.

3,600-row teacher-candidate pilot result:

| Bucket | Count |
| --- | ---: |
| confident keep + conservative keep | 2,681 |
| confident keep + conservative not_keep | 272 |
| confident not_keep + conservative keep | 1 |
| confident not_keep + conservative not_keep | 646 |

Interpretation:

- The two Qwen3-8B v2 scorers agree on 92.42% of the teacher-candidate pilot.
- The 273 disagreements are compact boundary cases for teacher relabeling.
- The 646 both-not-keep examples are the strongest hard-negative candidates.
- The priority review queue has 1,215 records after adding clean-not_keep and
  flagged-but-kept cases.
- The original top919 file
  `data/scored/teacher_candidates_all_v2_teacher_review_top919.jsonl` contains
  all 273 model disagreements plus all 646 both-not-keep records, but it is not
  fully unlabeled. Some records were already labeled in the starter/targeted
  teacher batches.
- The deduplicated first teacher-labeling batch is
  `data/splits/teacher_judge/v2_active_pilot_001/v2active001_teacher_candidates_all.jsonl`
  with 388 priority records that were unlabeled at selection time, and prompts
  are in
  `data/labeled/teacher_judge/v2active001/v2active001_teacher_prompts.jsonl`.

## Why the Binary Task Exists

The original 1-5 score task worked technically, but the middle class was noisy:

- `maybe` had near-zero recall.
- Many mistakes were off-by-one score disagreements.
- The teacher rubric itself has fuzzy boundaries around score 3.

The binary confident dataset removes score-3 examples and asks a cleaner
question: "Is this clearly useful training data or clearly not?"

## Next Steps

Recommended next work:

1. Treat v3 training/evaluation as complete and use
   `reports/scorer_binary_v3_qwen3_8b_experiment_report.md` as the current
   scorer report.
2. Use v3 conservative as the main quality-first scorer for review routing and
   hard-negative mining.
3. Use v3 confident as the high-confidence keep companion.
4. Run both v3 scorers on a larger unlabeled pool, excluding all already
   teacher-labeled original sample `id`s.
5. Keep a small calibration sample from three buckets:
   - high-confidence keep
   - high-confidence not_keep
   - conservative/confident disagreement examples
6. Use the teacher model only on uncertain or high-impact examples.
7. Add more negative examples, especially from `cot_zh` and `finetome`.
8. Keep Qwen3-4B as the compact comparison baseline, but do not prioritize
   v2 4B training until the 8B models have been used to mine hard cases.
9. Only after the binary scorer is stable, consider adding a second-stage
   severity score or a calibrated confidence score.

Concrete next implementation plan:

1. Run v3 conservative and v3 confident inference on the next candidate pool
   with `scripts/12_infer_binary_scorer.py`.
2. Build a v3 agreement/disagreement report similar to the v2 3,600-row pilot
   report.
3. Use `scripts/13_build_teacher_review_batch.py` again with a new batch prefix
   such as `v2active002`, excluding all prior teacher-label files by original
   sample `id`.
4. Prioritize teacher review from:
   - v3 conservative/confident disagreements
   - v3 conservative predicted `not_keep`
   - rule-flagged examples predicted `keep`
   - `cot_zh` examples near the current weak boundary
5. After the next teacher batch is labeled, rebuild the binary scorer dataset
   as the next data version and compare against v3 conservative/confident.

Avoid spending much more effort on the 1-5 score setup until the binary filter
is more stable. The 1-5 scorer is useful as an error-analysis reference, but it
is not the best current training target.

## GitHub Notes

Commit:

- scripts
- prompts
- configs
- markdown reports
- small metadata files

Use `PROJECT_FILE_INVENTORY.md` as the pre-GitHub checklist.

Do not commit:

- raw datasets
- generated JSONL data
- API keys
- Hugging Face cache files
- LLaMA-Factory model outputs
- local checkpoint directories

Current `.gitignore` is set up to ignore generated JSONL files, processed data,
splits, Python caches, local checkpoints, model weights, and environment files.
If future work creates new generated directories, update `.gitignore` before
committing.
