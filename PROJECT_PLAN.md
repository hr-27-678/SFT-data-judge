# Project Plan

Last updated: 2026-05-01

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
