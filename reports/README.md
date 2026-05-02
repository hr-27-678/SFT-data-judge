# Report Index

Last updated: 2026-05-01

This folder contains both canonical reports and historical diagnostic reports.
Use this index to avoid confusing older experiments with the current baseline.

## Current Canonical Reports

- `scorer_binary_experiment_report.md`
  - Summary of the binary confident scorer experiment.
  - This is the current best baseline.
- `scorer_binary_eval_valid_report.md`
  - Valid-set evaluation for the binary confident scorer.
- `scorer_binary_eval_test_report.md`
  - Test-set evaluation for the binary confident scorer.
- `scorer_error_analysis_greedy_report.md`
  - Error analysis for the original 1-5 scorer using greedy predictions.
  - Useful for understanding why the binary simplification was needed.

## Teacher Data Reports

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
