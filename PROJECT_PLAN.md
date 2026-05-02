# Project Plan

Last updated: 2026-05-01

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

The current best direction is the binary confident scorer, not the original
1-5 scorer.

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

## Current Best Result

The binary confident scorer is the best current baseline.

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

Local model artifacts are not committed to GitHub. The important local adapter
paths are:

- Original 1-5 scorer:
  `C:\Users\haoran27\llamafactory_outputs\scorer_sft_1000_qwen3_4b_lora_e3`
- Binary confident scorer:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_4b_lora_e3`

Use the binary confident adapter for future scorer experiments unless there is
a specific reason to inspect the older 1-5 scorer.

## Why the Binary Task Exists

The original 1-5 score task worked technically, but the middle class was noisy:

- `maybe` had near-zero recall.
- Many mistakes were off-by-one score disagreements.
- The teacher rubric itself has fuzzy boundaries around score 3.

The binary confident dataset removes score-3 examples and asks a cleaner
question: "Is this clearly useful training data or clearly not?"

## Next Steps

Recommended next work:

1. Run the binary scorer on a larger unlabeled candidate pool.
2. Sample three buckets for inspection:
   - high-confidence keep
   - high-confidence not_keep
   - uncertain or conflicting examples
3. Use the teacher model only on the uncertain or high-impact examples.
4. Add more negative examples, especially from `cot_zh` and `finetome`.
5. Retrain binary scorer on the expanded confident dataset.
6. Only after the binary scorer is stable, consider adding a second-stage
   severity score or a calibrated confidence score.

Concrete next implementation plan:

1. Add an inference script that applies the binary scorer to unlabeled candidate
   JSONL files and writes predictions incrementally with resume support.
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
5. Use the new teacher labels to expand the binary confident training set.

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
