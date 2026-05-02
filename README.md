# SFT-DataJudge

SFT-DataJudge is a data-centric pipeline for judging whether supervised fine-tuning
samples are useful training data. The project builds a small local scorer by
distilling labels from a stronger teacher model.

## Current Status

Last updated: 2026-05-01

The current best baseline is a binary "confident scorer":

- Base model: `Qwen/Qwen3-4B-Instruct-2507`
- Fine-tuning: LoRA, 3 epochs, LLaMA-Factory
- Task: classify confident teacher labels only
  - teacher score 4/5 -> `keep`
  - teacher score 1/2 -> `not_keep`
  - teacher score 3 is skipped because it is ambiguous
- Adapter output:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_4b_lora_e3`

Binary scorer metrics:

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 82.11% | 0.872 | 0.702 | 100% |
| Test | 76.04% | 0.824 | 0.623 | 100% |

This is better than the original 1-5 score scorer for a first useful baseline.
The model is currently more reliable as a conservative keep-first filter than as
an automatic drop filter.

## Repository Layout

```text
SFT-DataJudge/
  configs/                 Dataset and run configuration files
  prompts/                 Teacher and scorer prompt templates
  reports/                 Human-readable experiment reports
  scripts/                 Pipeline scripts, ordered by stage
  data/                    Local/generated data artifacts
```

Most JSONL data and model outputs are generated artifacts and are ignored by
`.gitignore`. The reports and scripts are the main files to commit.

## Main Workflow

1. Prepare unified source data.
2. Sample teacher candidates with source-aware allocation.
3. Label candidates with the teacher model.
4. Analyze teacher labels.
5. Convert teacher labels into SFT data for a scorer model.
6. Train and evaluate the original 1-5 scorer.
7. Convert confident labels into a binary scorer dataset.
8. Train and evaluate the binary confident scorer.

## Key Reports

Start here:

- `PROJECT_PLAN.md` - current project plan and next steps.
- `PROJECT_FILE_INVENTORY.md` - GitHub handoff checklist.
- `reports/README.md` - report index and which reports are canonical.
- `scripts/README.md` - script index and pipeline order.

Most useful current reports:

- `reports/scorer_binary_experiment_report.md`
- `reports/scorer_binary_eval_valid_report.md`
- `reports/scorer_binary_eval_test_report.md`
- `reports/scorer_error_analysis_greedy_report.md`
- `reports/teacher_label_report_1000.md`
- `reports/teacher_sampling_starter_1000_report.md`
- `data/labeled/scorer_binary_sft/scorer_binary_confident_1000_report.md`

## Reproduction Notes

Run scripts from the repository root.

```powershell
python scripts/09_build_binary_scorer_sft.py
python scripts/10_evaluate_binary_scorer_predictions.py --help
```

LLaMA-Factory WebUI startup is documented in:

```text
reports/llamafactory_startup.md
```

Do not commit API keys, raw datasets, generated JSONL label files, Hugging Face
caches, or LLaMA-Factory model outputs.
