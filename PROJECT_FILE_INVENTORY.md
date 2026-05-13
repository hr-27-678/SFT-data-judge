# Project File Inventory

Last updated: 2026-05-13

This is the repository hygiene checklist for SFT-DataJudge. It separates files
that should be versioned from generated artifacts that should stay local.

## Canonical Entry Points

- `README.md`
  - Public project overview and current headline result.
  - Current conclusion: Phase E downstream validation favors
    `v4_both_keep`; the per-source follow-up has completed train/predict and
    awaits five-model teacher pairwise judging.
- `PROJECT_PLAN.md`
  - Working project memory: current decisions, completed work, metrics, open
    questions, and next phase.
- `PROJECT_FILE_INVENTORY.md`
  - This repository cleanup and handoff checklist.
- `scripts/README.md`
  - Current script map from data prep through Phase E pairwise judging.
- `reports/README.md`
  - Current report map with canonical vs historical status.

## Source Files To Commit

### Scripts

Commit all files under `scripts/` except caches. The current script sequence is
`01_*` through `32_*`, plus PowerShell runners:

- Data preparation and teacher labeling: `01` through `05`, `11`, `13`, `14`.
- Binary scorer build/eval/inference: `06` through `10`, `12`.
- Evergreen and v4 data construction: `15` through `26`.
- Phase E downstream validation: `27` through `32`.
- Local runners/utilities:
  - `run_all_evergreen_inferences.ps1`
  - `run_all_evergreen_noflag_inferences.ps1`
  - `run_all_evergreen_v2_inferences.ps1`
  - `run_phase_e_downstream_train.ps1`
  - `start_llamafactory_webui.ps1`
  - `verify_evergreen_labels.py`

Do not commit `scripts/__pycache__/`.

### Configs And Prompts

- `configs/teacher_sampling.json`
- `configs/teacher_judge.json`
- `configs/llamafactory/*.yaml`
  - Scorer train/predict configs for v1 through v4.
  - Evergreen and evergreen_v2 predict configs.
  - Phase E downstream train/predict configs.
- `prompts/teacher_judge_prompt.md`
- `prompts/teacher_judge_pairwise_prompt.md`

These should be committed unless a future config contains a private path,
credential, or machine-specific secret.

### Reports And Metadata

Commit markdown reports and small metadata JSON files that explain generated
datasets or completed experiments:

- `reports/*.md`
- `data/labeled/**/dataset_info.json`
- `data/labeled/**/*_report.md`
- `data/eval/**/*_metrics.json`
- `data/eval/*_ids.json`

The markdown reports are intentionally kept even when historical; they are the
experiment audit trail.

## Generated Data To Keep Local

These are generated artifacts and should normally remain ignored:

- `data/raw/`
- `data/processed/`
- `data/splits/**/*.jsonl`
- `data/splits/**/*.json`
- `data/labeled/**/*.jsonl`
- `data/labeled/teacher_judge/`
- `data/scored/`
- `data/_archive/`
- `outputs/`
- local LLaMA-Factory outputs/checkpoints/logs

Important local generated artifacts include:

- Phase E candidate pool:
  - `data/splits/phase_e/phase_e_clean_candidate_15k.jsonl`
- Phase E scored pools:
  - `data/scored/phase_e_v4_conservative_clean_15k.jsonl`
  - `data/scored/phase_e_v4_confident_clean_15k.jsonl`
- Phase E downstream training datasets:
  - `data/labeled/phase_e_sft/*.jsonl`
- Phase E eval generated artifacts:
  - `data/eval/phase_e_downstream_eval/phase_e_downstream_prediction_comparison.jsonl`
  - `data/eval/phase_e_downstream_eval/phase_e_downstream_pairwise_labels.jsonl`
  - `data/eval/phase_e_downstream_eval/phase_e_downstream_pairwise_labels_5model.jsonl`

These may be valuable locally, but they are too large or too data-sensitive for
the normal source repository.

## Local-Only Model Artifacts

LLaMA-Factory outputs are outside this repository and should stay local:

- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v4_conservative_qwen3_8b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v4_confident_qwen3_8b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\phase_e_unfiltered_clean_15k_qwen3_8b_lora_e1`
- `C:\Users\haoran27\llamafactory_outputs\phase_e_v4_conservative_keep_clean_15k_qwen3_8b_lora_e1`
- `C:\Users\haoran27\llamafactory_outputs\phase_e_v4_confident_keep_clean_15k_qwen3_8b_lora_e1`
- `C:\Users\haoran27\llamafactory_outputs\phase_e_v4_both_keep_clean_15k_qwen3_8b_lora_e1`
- `C:\Users\haoran27\llamafactory_outputs\phase_e_v4_persource_keep_clean_15k_qwen3_8b_lora_e1`

Older v1-v3 scorer outputs are also local-only. Do not commit adapter weights,
checkpoints, Hugging Face caches, or training logs unless there is a specific
release plan.

## Optional Or Non-Canonical Files

- `explore_data.ipynb`
  - Exploratory notebook from the data-inspection stage. It is not part of the
    canonical pipeline. Keep it only if the notebook remains useful for manual
    exploration.
- `notebooks/`
  - Currently not used by the canonical pipeline.
- `outputs/`
  - Smoke-test outputs; ignored and safe to regenerate.

## Ignored Cleanup Rules

`.gitignore` should keep the working tree quiet for generated data:

- JSONL/JSON under `data/processed`, `data/labeled`, `data/scored`, and
  `data/splits`.
- `data/_archive/`.
- Dry-run eval JSONL files matching `data/eval/**/*_dryrun.jsonl`.
- Backup files matching `*.bak_before_*`.
- Caches, logs, local environments, model weights, and output directories.

## GitHub Checklist

Before pushing:

1. Run `git status --short --ignored`.
2. Confirm only source, configs, prompts, markdown reports, and small metadata
   are staged.
3. Confirm no API keys, `.env` files, model weights, checkpoint directories, or
   large JSONL files are staged.
4. Re-read `README.md`, `PROJECT_PLAN.md`, `scripts/README.md`, and
   `reports/README.md` after major experiment phases.
5. Decide explicitly whether to keep or remove `explore_data.ipynb` before a
   public release.
