# Report Index

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | Maintained manually |
| Report type | Report index |
| Project stage | Project navigation |
| Report status | Canonical index |

## Experiment Context

| Field | Value |
| --- | --- |
| Model | N/A |
| Data version | N/A |
| Current use | Identify canonical, historical, and incomplete reports |
| Start here after | `PROJECT_PLAN.md`, `PROJECT_FILE_INVENTORY.md` |

Last updated: 2026-05-02

This folder contains both canonical reports and historical diagnostic reports.
Use this index to avoid confusing older experiments with the current baseline.

## Report Format Standard

Every markdown file in `reports/` now starts with:

1. `Report Metadata`
   - generated time or maintenance status
   - report type
   - project stage
   - report status
2. `Experiment Context`
   - model or tool
   - data version
   - split / run / script / label policy where relevant
   - current use

Common metric sections use similar names where possible:

- `Metrics Summary`
- `Source Breakdown`
- `Split Breakdown`
- `Run Artifacts`
- `Confusion Matrix`
- `Recommended Next Actions`

## Current Canonical Reports

- `scorer_binary_experiment_report.md`
  - Summary of the binary confident scorer experiment.
  - This is the compact Qwen3-4B baseline.
- `scorer_binary_eval_valid_report.md`
  - Valid-set evaluation for the binary confident scorer.
- `scorer_binary_eval_test_report.md`
  - Test-set evaluation for the binary confident scorer.
- `scorer_binary_qwen3_8b_v1_experiment_report.md`
  - Qwen3-8B capacity check on the same v1 binary confident dataset.
  - Useful for deciding how to train v2, but not a replacement for the 4B
    baseline as an automatic drop filter.
- `scorer_binary_eval_valid_qwen3_8b_v1_report.md`
  - Valid-set evaluation for the Qwen3-8B v1 binary scorer.
- `scorer_binary_eval_test_qwen3_8b_v1_report.md`
  - Test-set evaluation for the Qwen3-8B v1 binary scorer.
- `scorer_binary_v2_conservative_qwen3_8b_experiment_report.md`
  - Main v2 conservative Qwen3-8B experiment after adding the targeted 1,200
    teacher labels.
  - Current quality-first candidate.
- `scorer_binary_v2_conservative_eval_valid_report.md`
  - Valid-set evaluation for the Qwen3-8B v2 conservative scorer.
- `scorer_binary_v2_conservative_eval_test_report.md`
  - Test-set evaluation for the Qwen3-8B v2 conservative scorer.
- `scorer_error_analysis_greedy_report.md`
  - Error analysis for the original 1-5 scorer using greedy predictions.
  - Useful for understanding why the binary simplification was needed.
- `training_lessons_and_notes.md`
  - Consolidated Chinese notes on training settings, observed behaviors,
    evaluation logic, and practical lessons from the scorer experiments.
  - Includes early-stop/checkpoint guidance and training tricks used or worth
    trying.

## Prepared But Not Completed

- Qwen3-8B v2 confident ablation
  - Configs exist in `configs/llamafactory/`.
  - The 2026-05-02 run was intentionally stopped before completion.
  - No valid/test report exists yet, and any partial local output should not be
    treated as a finished experiment.

## Teacher Data Reports

- `teacher_sampling_targeted_1200_report.md`
  - Targeted sampling report for the next 1,200-example teacher-labeling batch.
  - Prioritizes current scorer weaknesses rather than random expansion.
- `teacher_label_report_targeted_1200.md`
  - DeepSeek teacher-label report for the targeted 1,200-example batch.
  - This is the canonical targeted-label report for v2 data construction.
- `teacher_sampling_starter_1000_report.md`
  - Source-aware sampling report for the 1,000-example starter set.
- `teacher_label_report_1000.md`
  - Distribution and quality summary for teacher labels.
- `teacher_sampling_report.md`
  - Larger teacher-candidate sampling report.
- `pilot_sampling_report.md`
  - Early pilot sampling report.
- `pilot_label_review.md`
  - Early pilot label sanity check.

## Original 1-5 Scorer Reports

Canonical greedy reports:

- `scorer_eval_valid_greedy_report.md`
- `scorer_eval_test_greedy_report.md`

Historical sampling-based reports:

- `scorer_eval_valid_report.md`
- `scorer_eval_test_report.md`
- `scorer_error_analysis_report.md`

The sampling-based reports are kept for traceability, but the greedy reports are
the better reference for deterministic evaluation.

## Project Setup Reports

- `data_report.md`
  - Source data summary.
- `quality_rubric.md`
  - Teacher label rubric.
- `llamafactory_startup.md`
  - Local LLaMA-Factory WebUI startup notes for this machine.

## Related Data Reports

These reports live outside the `reports/` directory because they describe
specific generated datasets:

- `data/labeled/scorer_sft/scorer_sft_report.md`
- `data/labeled/scorer_binary_sft/scorer_binary_confident_1000_report.md`
- `data/labeled/scorer_binary_sft_v2/scorer_binary_v2_confident_report.md`
- `data/labeled/scorer_binary_sft_v2/scorer_binary_v2_conservative_report.md`
