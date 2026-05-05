# Project File Inventory

Last updated: 2026-05-05

This file is a GitHub handoff checklist for the current project directory. It
separates source files, reports, generated data, and local-only artifacts.

## Top-Level Files

- `README.md`
  - Main project entrypoint.
  - Up to date with the compact baseline, both v2 8B candidates, the 3,600-row
    pilot inference result, v3 training/evaluation results, and next actions.
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
  - LLaMA-Factory training config for the completed Qwen3-8B v2 confident
    ablation.
- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_valid.yaml`
  - Greedy valid prediction config for the Qwen3-8B v2 confident ablation.
- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_test.yaml`
  - Greedy test prediction config for the Qwen3-8B v2 confident ablation.
- `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_e3.yaml`
  - Prepared LLaMA-Factory training config for the Qwen3-8B v3 conservative
    scorer.
- `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_predict_valid.yaml`
  - Greedy valid prediction config for the Qwen3-8B v3 conservative scorer.
- `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_predict_test.yaml`
  - Greedy test prediction config for the Qwen3-8B v3 conservative scorer.
- `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_e3.yaml`
  - Prepared LLaMA-Factory training config for the Qwen3-8B v3 confident
    scorer.
- `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_predict_valid.yaml`
  - Greedy valid prediction config for the Qwen3-8B v3 confident scorer.
- `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_predict_test.yaml`
  - Greedy test prediction config for the Qwen3-8B v3 confident scorer.
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
- `scripts/12_infer_binary_scorer.py`
- `scripts/13_build_teacher_review_batch.py`
- `scripts/14_analyze_teacher_review_priority.py`
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
- `reports/scorer_binary_v2_confident_qwen3_8b_experiment_report.md`
- `reports/scorer_binary_v2_confident_eval_valid_report.md`
- `reports/scorer_binary_v2_confident_eval_test_report.md`
- `reports/teacher_candidates_all_v2_model_agreement_report.md`
- `reports/teacher_candidates_all_v2_conservative_inference_report.md`
- `reports/teacher_candidates_all_v2_confident_inference_report.md`
- `reports/teacher_candidates_all_v2_priority_teacher_analysis_report.md`
- `reports/teacher_label_report_v2active001.md`
- `reports/teacher_sampling_v2_active_pilot_001_report.md`
- `reports/scorer_binary_v3_qwen3_8b_experiment_report.md`
- `reports/scorer_binary_v3_conservative_eval_valid_report.md`
- `reports/scorer_binary_v3_conservative_eval_test_report.md`
- `reports/scorer_binary_v3_confident_eval_valid_report.md`
- `reports/scorer_binary_v3_confident_eval_test_report.md`
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
  - Current dry-run prompt file:
    `v2_pilot_top919/v2_pilot_top919_teacher_prompts.jsonl`.
  - Current active-learning dry-run prompt file:
    `v2active001/v2active001_teacher_prompts.jsonl`.
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
- `data/labeled/scorer_binary_sft_v3/`
  - V3 binary scorer SFT JSONL files built from starter + targeted +
    `v2active001` teacher labels.
  - Ready for training but not yet trained/evaluated.
  - Conservative: 2,588 records; score 3 maps to `not_keep`.
  - Confident: 2,326 records; score 3 is skipped.
  - `dataset_info.json`, `scorer_binary_v3_confident_report.md`, and
    `scorer_binary_v3_conservative_report.md` are useful metadata.
- `data/eval/`
  - Small generated metric JSON files.
  - Optional to commit. The markdown reports already summarize the important
    metrics.
  - Current v2 metrics:
    `scorer_binary_v2_conservative_eval_valid_metrics.json`,
    `scorer_binary_v2_conservative_eval_test_metrics.json`,
    `scorer_binary_v2_confident_eval_valid_metrics.json`, and
    `scorer_binary_v2_confident_eval_test_metrics.json`.
  - Current v3 metrics:
    `scorer_binary_v3_conservative_eval_valid_metrics.json`,
    `scorer_binary_v3_conservative_eval_test_metrics.json`,
    `scorer_binary_v3_confident_eval_valid_metrics.json`, and
    `scorer_binary_v3_confident_eval_test_metrics.json`.
- `data/scored/`
  - Batch scorer inference outputs for unlabeled or teacher-candidate pools.
  - Current important local pilot artifacts:
    `teacher_candidates_all_v2_model_agreement_metrics.json`,
    `teacher_candidates_all_v2_model_disagreements.jsonl`, and
    `teacher_candidates_all_v2_teacher_review_priority.jsonl`.
  - First teacher-labeling subset:
    `teacher_candidates_all_v2_teacher_review_top919.jsonl`.
  - Large prediction JSONL files are generated artifacts and should normally
    stay local.
- `data/splits/teacher_judge/v2_active_pilot_001/`
  - Deduplicated active-learning teacher candidates selected by
    `scripts/13_build_teacher_review_batch.py`.
  - Contains the 388-record `v2active001` teacher batch and 827
    already-labeled matches for analysis.
  - JSONL files are generated artifacts and should stay local.

## Local-Only Model Artifacts

LLaMA-Factory outputs are outside this repository and should stay local:

- `C:\Users\haoran27\llamafactory_outputs\scorer_sft_1000_qwen3_4b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_4b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_8b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_conservative_qwen3_8b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_confident_qwen3_8b_lora_e3`
  - Completed Qwen3-8B v2 confident ablation from 2026-05-03.

Current v3 local model outputs:

- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_confident_qwen3_8b_lora_e3`

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
