# Project Plan

Last updated: 2026-05-03

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
10. `reports/teacher_sampling_targeted_1200_report.md`

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
- 3,600-row teacher-candidate pilot inference with both Qwen3-8B v2 adapters:
  - `reports/teacher_candidates_all_v2_conservative_inference_report.md`
  - `reports/teacher_candidates_all_v2_confident_inference_report.md`
  - `reports/teacher_candidates_all_v2_model_agreement_report.md`
  - `data/scored/teacher_candidates_all_v2_teacher_review_priority.jsonl`
  - `data/scored/teacher_candidates_all_v2_teacher_review_top919.jsonl`
  - `data/labeled/teacher_judge/v2_pilot_top919/v2_pilot_top919_teacher_prompts.jsonl`
- Training lessons note:
  `reports/training_lessons_and_notes.md`

Current main candidate:

- `Qwen/Qwen3-8B` LoRA on `scorer_binary_v2_conservative`
- Local adapter:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_conservative_qwen3_8b_lora_e3`
- Use it for prioritization, review routing, and selecting teacher relabeling
  candidates. Do not use it for blind automatic deletion.

Current companion candidate:

- `Qwen/Qwen3-8B` LoRA on `scorer_binary_v2_confident`
- Local adapter:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_confident_qwen3_8b_lora_e3`
- Use it as a high-confidence keep filter and as a contrast model against v2
  conservative. Disagreements between the two v2 8B models are useful
  teacher-relabeling candidates.

Best next action:

- Send the 3,600-row pilot priority queue to the teacher model first, starting
  with model disagreements and both-not-keep records. Do not spend the next
  run on 4B v2 or full 188k inference until this teacher-labeled pilot tells
  us which scorer errors are real.

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

The Qwen3-8B v2 conservative scorer is the current main candidate. The Qwen3-4B
binary confident scorer remains the compact baseline.

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 82.11% | 0.872 | 0.702 | 100% |
| Test | 76.04% | 0.824 | 0.623 | 100% |

Interpretation:

- The scorer learned the teacher's confident keep/not-keep boundary better than
  the original 1-5 score task.
- It is currently useful as a keep-first filter.
- It is not yet strong enough to automatically discard data without a human or
  teacher-model review layer.

Qwen3-8B v1 capacity check on the same data:

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 77.89% | 0.851 | 0.571 | 100% |
| Test | 84.38% | 0.899 | 0.651 | 100% |

Interpretation:

- The 8B model is stronger as a keep-first scorer, especially on the test split.
- It is more keep-biased than the 4B model: test keep recall is 97.10%, but
  test not_keep recall is only 51.85%.
- Do not use the 8B v1 adapter for automatic dropping. Treat it as the main v2
  candidate once targeted negatives and boundary cases are added.

Qwen3-8B v2 conservative result:

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 74.55% | 0.799 | 0.655 | 100% |
| Test | 79.91% | 0.844 | 0.717 | 100% |

Interpretation:

- This is the best current quality-first candidate because test `not_keep` F1
  improved to 0.717 and test `not_keep` recall improved to 64.04%.
- It is not directly comparable to v1 as a pure capacity test, because v2 is
  larger, targeted, and maps score 3 to `not_keep`.
- Keep F1 is lower than v1 8B, but the reject boundary is healthier.
- Do not use it for blind automatic deletion yet; use it for prioritization,
  review routing, and selecting examples for teacher relabeling.

Qwen3-8B v2 confident result:

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 76.14% | 0.832 | 0.591 | 100% |
| Test | 82.41% | 0.879 | 0.679 | 100% |

Interpretation:

- This is the best current high-confidence keep candidate because test
  accuracy and keep F1 are higher than v2 conservative.
- It is more keep-biased than v2 conservative: test predictions were
  154 keep / 45 not_keep, and test `not_keep` recall was 57.81%.
- It should not replace v2 conservative for reject routing. Use the two
  together: confident for keep prioritization, conservative for surfacing
  questionable examples, and disagreements for teacher relabeling.

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

Use the binary setup for future scorer experiments. The 4B adapter is the
compact baseline, while the v2 conservative 8B adapter is the current main
quality-first candidate and the v2 confident 8B adapter is the companion
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
- The first teacher-labeling file is
  `data/scored/teacher_candidates_all_v2_teacher_review_top919.jsonl`.
- A dry-run prompt file for the first batch has been rendered at
  `data/labeled/teacher_judge/v2_pilot_top919/v2_pilot_top919_teacher_prompts.jsonl`.

## Why the Binary Task Exists

The original 1-5 score task worked technically, but the middle class was noisy:

- `maybe` had near-zero recall.
- Many mistakes were off-by-one score disagreements.
- The teacher rubric itself has fuzzy boundaries around score 3.

The binary confident dataset removes score-3 examples and asks a cleaner
question: "Is this clearly useful training data or clearly not?"

## Next Steps

Recommended next work:

1. Send the 3,600-row pilot priority queue to the teacher model.
2. Label the 273 model-disagreement cases and 646 both-not-keep cases first.
3. Keep a small calibration sample from three buckets:
   - high-confidence keep
   - high-confidence not_keep
   - conservative/confident disagreement examples
4. Use the teacher model only on uncertain or high-impact examples.
5. Add more negative examples, especially from `cot_zh` and `finetome`.
6. Retrain binary scorer on the expanded confident/conservative datasets.
7. Keep Qwen3-4B as the compact comparison baseline, but do not prioritize
   v2 4B training until the 8B models have been used to mine hard cases.
8. Only after the binary scorer is stable, consider adding a second-stage
   severity score or a calibrated confidence score.

Concrete next implementation plan:

1. Convert `data/scored/teacher_candidates_all_v2_teacher_review_priority.jsonl`
   into teacher prompts. This has been done for the first 919 records.
2. Run the teacher model on the priority queue, starting with the 919 records
   from model disagreements plus both-not-keep.
3. Analyze teacher labels by source, rule flags, and agreement bucket.
4. Use the new teacher labels to expand both v2 policies and retrain.
5. Compare the retrained scorer against:
   - Qwen3-4B v1 binary confident
   - Qwen3-8B v1 binary confident
   - Qwen3-8B v2 conservative
   - Qwen3-8B v2 confident

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
