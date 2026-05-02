# Script Index

Last updated: 2026-05-01

Run scripts from the repository root unless a script says otherwise.

## Data Preparation

- `01_prepare_data.py`
  - Normalizes source datasets and writes processed JSONL files.
- `02_sample_for_teacher.py`
  - Builds teacher-candidate splits with source-aware sampling.
- `03_build_pilot.py`
  - Builds a small pilot set for teacher-label sanity checks.

## Teacher Labeling

- `04_teacher_judge.py`
  - Calls the teacher model and writes labels incrementally.
  - Supports resume-style operation by skipping examples already written.
- `05_analyze_teacher_labels.py`
  - Summarizes teacher labels and writes label reports.

## Scorer Dataset Builders

- `06_build_scorer_sft.py`
  - Converts teacher labels into the original 1-5 scorer SFT dataset.
- `09_build_binary_scorer_sft.py`
  - Converts confident teacher labels into the binary scorer dataset.
  - Uses score 4/5 as `keep`, score 1/2 as `not_keep`, and skips score 3.

## Evaluation

- `07_evaluate_scorer_predictions.py`
  - Evaluates original 1-5 scorer predictions.
- `08_analyze_scorer_errors.py`
  - Produces error-analysis reports for the original 1-5 scorer.
- `10_evaluate_binary_scorer_predictions.py`
  - Evaluates binary scorer predictions and writes markdown reports.

## Local Utilities

- `start_llamafactory_webui.ps1`
  - Starts the LLaMA-Factory WebUI on the school Windows machine.
  - If PowerShell blocks scripts, run with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_llamafactory_webui.ps1
```
