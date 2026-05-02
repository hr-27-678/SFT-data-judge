# Project File Inventory

Last updated: 2026-05-01

This file is a GitHub handoff checklist for the current project directory. It
separates source files, reports, generated data, and local-only artifacts.

## Top-Level Files

- `README.md`
  - Main project entrypoint.
  - Up to date with the current binary scorer baseline.
- `PROJECT_PLAN.md`
  - Current plan, completed artifacts, best result, and recommended next steps.
- `PROJECT_FILE_INVENTORY.md`
  - This file.
- `.gitignore`
  - Updated to ignore generated JSONL data, local model outputs, logs, caches,
    and environment files.
- `explore_data.ipynb`
  - Exploratory notebook from the data-inspection stage.
  - Optional for GitHub. It is not the canonical pipeline.

## Configs And Prompts

- `configs/teacher_sampling.json`
  - Teacher sampling configuration.
- `configs/teacher_judge.json`
  - Teacher-labeling configuration.
- `prompts/teacher_judge_prompt.md`
  - Teacher rubric prompt template.

These should be committed unless they contain private paths or secrets.

## Scripts

See `scripts/README.md` for the ordered script index.

Current scripts:

- `scripts/01_prepare_data.py`
- `scripts/02_sample_for_teacher.py`
- `scripts/03_build_pilot.py`
- `scripts/04_teacher_judge.py`
- `scripts/05_analyze_teacher_labels.py`
- `scripts/06_build_scorer_sft.py`
- `scripts/07_evaluate_scorer_predictions.py`
- `scripts/08_analyze_scorer_errors.py`
- `scripts/09_build_binary_scorer_sft.py`
- `scripts/10_evaluate_binary_scorer_predictions.py`
- `scripts/start_llamafactory_webui.ps1`
- `scripts/README.md`

Do not commit `scripts/__pycache__/`; it is ignored.

## Reports

See `reports/README.md` for the report index.

Canonical current reports:

- `reports/scorer_binary_experiment_report.md`
- `reports/scorer_binary_eval_valid_report.md`
- `reports/scorer_binary_eval_test_report.md`
- `reports/scorer_error_analysis_greedy_report.md`
- `reports/teacher_label_report_1000.md`
- `reports/teacher_sampling_starter_1000_report.md`
- `data/labeled/scorer_binary_sft/scorer_binary_confident_1000_report.md`
- `data/labeled/scorer_sft/scorer_sft_report.md`

Historical reports are kept for traceability, especially the original 1-5 scorer
reports and pilot reports.

## Generated Data Directories

These directories contain generated artifacts and are mostly ignored by
`.gitignore`.

- `data/processed/`
  - Normalized source data and summary JSON.
  - JSONL files should not be committed.
- `data/splits/`
  - Teacher-candidate splits and sampling summaries.
  - JSONL files should not be committed.
- `data/labeled/teacher_judge/`
  - Teacher prompts and teacher labels.
  - JSONL files should not be committed unless the repository is private and
    the data-sharing policy is clear.
- `data/labeled/scorer_sft/`
  - Original 1-5 scorer SFT JSONL files.
  - `dataset_info.json` and `scorer_sft_report.md` are useful metadata.
- `data/labeled/scorer_binary_sft/`
  - Binary confident scorer SFT JSONL files.
  - `dataset_info.json` and `scorer_binary_confident_1000_report.md` are useful
    metadata.
- `data/eval/`
  - Small generated metric JSON files.
  - Optional to commit. The markdown reports already summarize the important
    metrics.

## Local-Only Model Artifacts

LLaMA-Factory outputs are outside this repository and should stay local:

- `C:\Users\haoran27\llamafactory_outputs\scorer_sft_1000_qwen3_4b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_4b_lora_e3`

Do not commit model checkpoints, adapter weights, Hugging Face caches, or
training logs unless there is a specific release plan.

## GitHub Checklist

Before pushing:

1. Initialize Git if needed. This directory currently may not have `.git`.
2. Check `git status --short --ignored`.
3. Confirm no API keys or `.env` files are tracked.
4. Confirm generated JSONL files are ignored.
5. Decide whether to commit `explore_data.ipynb`.
6. Commit source scripts, configs, prompts, markdown reports, and small metadata
   files.
