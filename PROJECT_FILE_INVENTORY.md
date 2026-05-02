# Project File Inventory

Last updated: 2026-05-02

This file is a GitHub handoff checklist for the current project directory. It
separates source files, reports, generated data, and local-only artifacts.

## Top-Level Files

- `README.md`
  - Main project entrypoint.
  - Up to date with the compact baseline, current v2 main candidate, and next
    actions.
- `PROJECT_PLAN.md`
  - Current plan, status board, completed artifacts, best result, and
    recommended next steps.
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
- `configs/llamafactory/scorer_binary_confident_1000_qwen3_8b_lora_e3.yaml`
  - LLaMA-Factory training config for the Qwen3-8B v1 binary scorer.
- `configs/llamafactory/scorer_binary_confident_1000_qwen3_8b_lora_predict_valid.yaml`
  - LLaMA-Factory greedy valid prediction config for the Qwen3-8B v1 scorer.
- `configs/llamafactory/scorer_binary_confident_1000_qwen3_8b_lora_predict_test.yaml`
  - LLaMA-Factory greedy test prediction config for the Qwen3-8B v1 scorer.
- `configs/llamafactory/scorer_binary_v2_conservative_qwen3_8b_lora_e3.yaml`
  - LLaMA-Factory training config for the Qwen3-8B v2 conservative scorer.
- `configs/llamafactory/scorer_binary_v2_conservative_qwen3_8b_lora_predict_valid.yaml`
  - LLaMA-Factory greedy valid prediction config for the Qwen3-8B v2 scorer.
- `configs/llamafactory/scorer_binary_v2_conservative_qwen3_8b_lora_predict_test.yaml`
  - LLaMA-Factory greedy test prediction config for the Qwen3-8B v2 scorer.
- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_e3.yaml`
  - Prepared LLaMA-Factory training config for the Qwen3-8B v2 confident
    ablation. Training was intentionally stopped on 2026-05-02 and is not a
    completed experiment yet.
- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_valid.yaml`
  - Prepared greedy valid prediction config for the Qwen3-8B v2 confident
    ablation.
- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_test.yaml`
  - Prepared greedy test prediction config for the Qwen3-8B v2 confident
    ablation.
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
- `scripts/11_build_targeted_teacher_batch.py`
- `scripts/start_llamafactory_webui.ps1`
- `scripts/README.md`

Do not commit `scripts/__pycache__/`; it is ignored.

## Reports

See `reports/README.md` for the report index.

All markdown files under `reports/` use the same opening structure:

- `Report Metadata`
- `Experiment Context`

Canonical current reports:

- `reports/scorer_binary_experiment_report.md`
- `reports/scorer_binary_eval_valid_report.md`
- `reports/scorer_binary_eval_test_report.md`
- `reports/scorer_binary_qwen3_8b_v1_experiment_report.md`
- `reports/scorer_binary_eval_valid_qwen3_8b_v1_report.md`
- `reports/scorer_binary_eval_test_qwen3_8b_v1_report.md`
- `reports/scorer_binary_v2_conservative_qwen3_8b_experiment_report.md`
- `reports/scorer_binary_v2_conservative_eval_valid_report.md`
- `reports/scorer_binary_v2_conservative_eval_test_report.md`
- `reports/training_lessons_and_notes.md`
- `reports/teacher_sampling_targeted_1200_report.md`
- `reports/teacher_label_report_targeted_1200.md`
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
- `data/labeled/scorer_binary_sft_v2/`
  - V2 binary scorer SFT JSONL files built from starter + targeted teacher
    labels.
  - `dataset_info.json`, `scorer_binary_v2_confident_report.md`, and
    `scorer_binary_v2_conservative_report.md` are useful metadata.
- `data/eval/`
  - Small generated metric JSON files.
  - Optional to commit. The markdown reports already summarize the important
    metrics.
  - Current v2 metrics:
    `scorer_binary_v2_conservative_eval_valid_metrics.json` and
    `scorer_binary_v2_conservative_eval_test_metrics.json`.

## Local-Only Model Artifacts

LLaMA-Factory outputs are outside this repository and should stay local:

- `C:\Users\haoran27\llamafactory_outputs\scorer_sft_1000_qwen3_4b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_4b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_8b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_conservative_qwen3_8b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_confident_qwen3_8b_lora_e3`
  - Partial/incomplete local output from an intentionally stopped run on
    2026-05-02. Overwrite or clean before restarting the ablation.

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
