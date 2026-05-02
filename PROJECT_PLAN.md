# Project Plan

Last updated: 2026-05-02

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
7. `reports/training_lessons_and_notes.md`
8. `reports/teacher_sampling_targeted_1200_report.md`

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

The current best direction is the binary scorer family, not the original 1-5
scorer.

On 2026-05-02, the targeted teacher-labeling batch was completed with DeepSeek.
Four initial API/parse failures were retried, then merged into the canonical
`data/labeled/teacher_judge/targeted_1200_teacher_labels.jsonl`, giving
1,200/1,200 valid teacher labels.

Also on 2026-05-02, Qwen3-8B v2 confident configs were created, but the run was
intentionally stopped before completion. Do not treat any local partial output
for `scorer_binary_v2_confident_qwen3_8b_lora_e3` as a completed experiment.

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
- Training lessons note:
  `reports/training_lessons_and_notes.md`

Prepared but not completed:

- Qwen3-8B v2 confident ablation configs:
  - `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_e3.yaml`
  - `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_valid.yaml`
  - `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_test.yaml`
- The first attempted run was intentionally stopped on 2026-05-02. Restart it
  from scratch with `overwrite_output_dir: true` if this ablation is needed.

Current main candidate:

- `Qwen/Qwen3-8B` LoRA on `scorer_binary_v2_conservative`
- Local adapter:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_conservative_qwen3_8b_lora_e3`
- Use it for prioritization, review routing, and selecting teacher relabeling
  candidates. Do not use it for blind automatic deletion.

Best next action:

- Prefer building a scorer inference script for larger unlabeled JSONL pools
  before doing more training. This will show how the current v2 conservative
  model behaves on realistic candidate data.
- If the next goal is a controlled ablation instead, run the prepared Qwen3-8B
  v2 confident experiment from scratch and compare it against v2 conservative.

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
11. Train and evaluate Qwen3-8B v2 conservative as the current main candidate.

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

Qwen3-8B v2 confident prepared artifacts:

- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_test.yaml`
- Status: config-only / interrupted partial local run, not evaluated.

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
- Qwen3-8B binary confident v2 partial/incomplete run:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_confident_qwen3_8b_lora_e3`
  This should be overwritten or cleaned before restarting the ablation.

Use the binary setup for future scorer experiments. The 4B adapter is the
compact baseline, while the v2 conservative 8B adapter is the current main
quality-first candidate.

## Why the Binary Task Exists

The original 1-5 score task worked technically, but the middle class was noisy:

- `maybe` had near-zero recall.
- Many mistakes were off-by-one score disagreements.
- The teacher rubric itself has fuzzy boundaries around score 3.

The binary confident dataset removes score-3 examples and asks a cleaner
question: "Is this clearly useful training data or clearly not?"

## Next Steps

Recommended next work:

1. Build an inference script that applies the v2 conservative binary scorer to
   unlabeled candidate JSONL files with resume support.
2. Run the v2 conservative binary scorer on a larger unlabeled candidate pool.
3. Sample three buckets for inspection:
   - high-confidence keep
   - high-confidence not_keep
   - uncertain or conflicting examples
4. Use the teacher model only on uncertain or high-impact examples.
5. Optionally train Qwen3-8B on `scorer_binary_v2_confident` for comparison.
6. Keep Qwen3-4B as the compact
   comparison baseline if time permits.
7. Add more negative examples, especially from `cot_zh` and `finetome`.
8. Retrain binary scorer on the expanded confident dataset.
9. Only after the binary scorer is stable, consider adding a second-stage
   severity score or a calibrated confidence score.

Concrete next implementation plan:

1. Implement `scripts/12_infer_binary_scorer.py` or equivalent.
   Desired behavior:
   - input JSONL candidate pool
   - output JSONL predictions
   - resume by sample id or line count
   - deterministic greedy generation
   - source/label-count summary
2. Run it on the remaining teacher-candidate pool or a larger clean processed
   pool.
3. Build an analysis report with:
   - predicted keep/not_keep counts
   - source-wise distribution
   - high-confidence examples
   - likely false positives and false negatives
4. Pick a small review set for teacher relabeling:
   - uncertain cases
   - confident `not_keep` cases from weak sources
   - examples where rule flags and model prediction disagree
5. Use the new teacher labels to expand the binary confident/conservative
   training set.
6. Train Qwen3-8B on `scorer_binary_v2_confident` as an ablation, if we want to
   know whether skipping score 3 improves keep precision enough to matter.
   Configs already exist, but the 2026-05-02 run was intentionally stopped
   before completion and should not be treated as a finished experiment.
7. Compare against:
   - Qwen3-4B v1 binary confident
   - Qwen3-8B v1 binary confident
   - Qwen3-8B v2 conservative

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
