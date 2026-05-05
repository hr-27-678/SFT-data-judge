# Script Index

Last updated: 2026-05-05

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
  - Use `--dedupe-by-id` when retry outputs were appended to the same JSONL;
    this keeps the last record for each original sample `id`.
- `11_build_targeted_teacher_batch.py`
  - Builds the next targeted 1,200-example teacher-labeling batch.
  - Prioritizes `cot_zh`, score-3-like review cases, rule-flagged review cases,
    and hard source-specific examples.
- `13_build_teacher_review_batch.py`
  - Builds deduplicated active-learning teacher batches from scorer priority
    JSONL files.
  - Excludes existing teacher labels by original sample `id`, not by
    `teacher_sample_id`.
  - Writes all/train/valid/test candidate files, already-labeled matches, and a
    markdown batch report.
  - Reuse this after larger local scorer runs by changing `--input`,
    `--batch-prefix`, `--output-dir`, and `--known-label-file`.

## Scorer Dataset Builders

- `06_build_scorer_sft.py`
  - Converts teacher labels into the original 1-5 scorer SFT dataset.
- `09_build_binary_scorer_sft.py`
  - Converts confident teacher labels into the binary scorer dataset.
  - Supports merging multiple teacher-label prefixes and candidate files.
  - In `confident` mode, uses score 4/5 as `keep`, score 1/2 as `not_keep`,
    and skips score 3.
  - In `all` mode, maps score 3 to `not_keep` for a conservative quality-first
    training target.
  - Current v3 data was built by merging starter, targeted, and `v2active001`
    labels into `data/labeled/scorer_binary_sft_v3/`.

## Evaluation

- `07_evaluate_scorer_predictions.py`
  - Evaluates original 1-5 scorer predictions.
- `08_analyze_scorer_errors.py`
  - Produces error-analysis reports for the original 1-5 scorer.
- `10_evaluate_binary_scorer_predictions.py`
  - Evaluates binary scorer predictions and writes markdown reports.
- `12_infer_binary_scorer.py`
  - Runs a trained binary scorer adapter on unlabeled candidate JSONL pools.
  - Uses the same prompt as `09_build_binary_scorer_sft.py`.
  - Supports resume-by-id, deterministic greedy generation, prompt-only dry runs,
    scored JSONL output, and source/rule-disagreement summary reports.
- `14_analyze_teacher_review_priority.py`
  - Joins scorer priority queues with all available Teacher Judge labels by
    original sample `id`.
  - Writes a full joined JSONL, metrics JSON, and markdown report for bucket,
    source, priority-reason, and scorer-vs-teacher analysis.
  - Current default analyzes the 1,215-record v2 priority queue using starter,
    targeted, and `v2active001` teacher labels.

## Local Utilities

- `start_llamafactory_webui.ps1`
  - Starts the LLaMA-Factory WebUI on the school Windows machine.
  - If PowerShell blocks scripts, run with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_llamafactory_webui.ps1
```
