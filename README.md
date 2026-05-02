# SFT-DataJudge

SFT-DataJudge is a data-centric pipeline for judging whether supervised fine-tuning
samples are useful training data. The project builds a small local scorer by
distilling labels from a stronger teacher model.

## Current Status

Last updated: 2026-05-02

The compact baseline is a binary "confident scorer":

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

A Qwen3-8B v1 capacity check has also been trained on the same binary confident
dataset. It improves test accuracy and keep recall, but is more keep-biased and
weaker on valid/not_keep recall, so it is best treated as a v2 candidate rather
than a full replacement for the current 4B baseline.

The targeted 1,200-example DeepSeek teacher-label batch is now complete with
1,200/1,200 valid labels. V2 binary scorer data is ready in
`data/labeled/scorer_binary_sft_v2/`.

The current main candidate is the Qwen3-8B v2 conservative scorer, trained on
`scorer_binary_v2_conservative`, which maps score 3 to `not_keep`.

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 74.55% | 0.799 | 0.655 | 100% |
| Test | 79.91% | 0.844 | 0.717 | 100% |

This is the best quality-first candidate so far because the reject boundary is
healthier than v1 8B. It should still be used for prioritization and review
routing, not blind automatic deletion.

Prepared but not completed:

- Qwen3-8B v2 confident ablation configs exist under `configs/llamafactory/`.
- The first v2 confident run was intentionally stopped on 2026-05-02 and should
  not be treated as a completed experiment.

Recommended next action:

- Build a binary scorer inference script for larger unlabeled JSONL pools, then
  sample high-confidence keep, high-confidence not_keep, and uncertain cases for
  review or teacher relabeling.

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
9. Add targeted teacher labels for weak and boundary cases.
10. Build v2 binary scorer datasets with confident and conservative score-3
    policies.
11. Train and evaluate the Qwen3-8B v2 conservative scorer.
12. Next: run the scorer over larger unlabeled pools and use teacher relabeling
    only where it is most useful.

## Key Reports

Start here:

- `PROJECT_PLAN.md` - current project plan and next steps.
- `PROJECT_FILE_INVENTORY.md` - GitHub handoff checklist.
- `reports/README.md` - report index and which reports are canonical.
- `scripts/README.md` - script index and pipeline order.

Most useful current reports:

- `reports/scorer_binary_experiment_report.md`
- `reports/scorer_binary_qwen3_8b_v1_experiment_report.md`
- `reports/scorer_binary_v2_conservative_qwen3_8b_experiment_report.md`
- `reports/scorer_binary_eval_valid_report.md`
- `reports/scorer_binary_eval_test_report.md`
- `reports/scorer_binary_v2_conservative_eval_valid_report.md`
- `reports/scorer_binary_v2_conservative_eval_test_report.md`
- `reports/training_lessons_and_notes.md`
- `reports/teacher_label_report_targeted_1200.md`
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
