# SFT-DataJudge

SFT-DataJudge is a data-centric pipeline for judging whether supervised fine-tuning
samples are useful training data. The project builds a small local scorer by
distilling labels from a stronger teacher model.

## Current Status

Last updated: 2026-05-05

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

The Qwen3-8B v2 confident ablation has also been trained and evaluated on
`scorer_binary_v2_confident`, which skips score 3. It is better as a
high-confidence keep filter, but weaker as a reject model:

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 76.14% | 0.832 | 0.591 | 100% |
| Test | 82.41% | 0.879 | 0.679 | 100% |

Recommended use:

- v2 confident: high-confidence keep prioritization.
- v2 conservative: review routing and quality-first not_keep surfacing.
- Disagreements between the two 8B v2 models are good teacher-relabeling
  candidates.

Both Qwen3-8B v2 adapters have now been run on the 3,600-row
`teacher_candidates_all` pilot pool. They agree on 3,327 / 3,600 records
(92.42%), with 273 model disagreements and 646 both-not-keep records. The
priority teacher-review queue is in
`data/scored/teacher_candidates_all_v2_teacher_review_priority.jsonl`; the
first 919-record teacher batch is
`data/scored/teacher_candidates_all_v2_teacher_review_top919.jsonl`, with
dry-run prompts rendered at
`data/labeled/teacher_judge/v2_pilot_top919/v2_pilot_top919_teacher_prompts.jsonl`.

The priority queue has now been deduplicated against existing starter and
targeted teacher labels by original sample `id`. The first active-learning
teacher batch is `v2active001`: 388 records selected from previously unlabeled
priority cases, with prompts at
`data/labeled/teacher_judge/v2active001/v2active001_teacher_prompts.jsonl`.
After teacher labeling and retry, `v2active001` has 388/388 deduplicated valid
teacher labels. The full 1,215-record priority analysis has 1,215/1,215 valid
teacher labels joined from starter, targeted, and `v2active001`; the report is
`reports/teacher_candidates_all_v2_priority_teacher_analysis_report.md`.

Recommended next action:

- V3 Qwen3-8B conservative/confident scorers are now trained and evaluated.
  Use v3 conservative as the current quality-first scorer, and v3 confident as
  the high-confidence keep companion.

V3 data ready for training:

| Dataset | Records | Train | Valid | Test | Keep | Not-keep | Score 3 Policy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `scorer_binary_v3_conservative` | 2,588 | 2,057 | 267 | 264 | 1,438 | 1,150 | mapped to `not_keep` |
| `scorer_binary_v3_confident` | 2,326 | 1,855 | 234 | 237 | 1,438 | 888 | skipped |

V3 test metrics:

| Model | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall |
| --- | ---: | ---: | ---: | ---: |
| v3 conservative Qwen3-8B | 76.89% | 0.796 | 0.734 | 77.06% |
| v3 confident Qwen3-8B | 78.90% | 0.851 | 0.638 | 53.66% |

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
12. Train and evaluate the Qwen3-8B v2 confident ablation.
13. Run both Qwen3-8B v2 scorers over the 3,600-row teacher-candidate pilot.
14. Analyze the teacher-labeled priority review queue and retrain from
    teacher-confirmed hard cases.
15. Build v3 binary scorer datasets from starter + targeted + `v2active001`.
16. Train/evaluate Qwen3-8B v3 conservative and confident variants.
17. Next: run both v3 scorers on a larger unlabeled pool and build the next
    active-learning teacher batch.

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
- `reports/scorer_binary_v2_confident_qwen3_8b_experiment_report.md`
- `reports/scorer_binary_v3_qwen3_8b_experiment_report.md`
- `reports/scorer_binary_v3_conservative_eval_valid_report.md`
- `reports/scorer_binary_v3_conservative_eval_test_report.md`
- `reports/scorer_binary_v3_confident_eval_valid_report.md`
- `reports/scorer_binary_v3_confident_eval_test_report.md`
- `reports/scorer_binary_eval_valid_report.md`
- `reports/scorer_binary_eval_test_report.md`
- `reports/scorer_binary_v2_conservative_eval_valid_report.md`
- `reports/scorer_binary_v2_conservative_eval_test_report.md`
- `reports/scorer_binary_v2_confident_eval_valid_report.md`
- `reports/scorer_binary_v2_confident_eval_test_report.md`
- `reports/teacher_candidates_all_v2_model_agreement_report.md`
- `reports/teacher_candidates_all_v2_conservative_inference_report.md`
- `reports/teacher_candidates_all_v2_confident_inference_report.md`
- `reports/teacher_candidates_all_v2_priority_teacher_analysis_report.md`
- `reports/training_lessons_and_notes.md`
- `reports/teacher_label_report_targeted_1200.md`
- `reports/teacher_label_report_v2active001.md`
- `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_conservative_report.md`
- `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_confident_report.md`
- `reports/scorer_error_analysis_greedy_report.md`
- `reports/teacher_label_report_1000.md`
- `reports/teacher_sampling_starter_1000_report.md`
- `data/labeled/scorer_binary_sft/scorer_binary_confident_1000_report.md`

## Reproduction Notes

Run scripts from the repository root.

`scripts/09_build_binary_scorer_sft.py` defaults to the v1 starter_1000 dataset.
To rebuild the current v3 datasets, pass all candidate files and all label
prefixes explicitly. Example:

```powershell
python scripts/09_build_binary_scorer_sft.py `
  --candidates `
    data/splits/teacher_judge/starter_1000/teacher_candidates_all.jsonl `
    data/splits/teacher_judge/targeted_1200/targeted_teacher_candidates_all.jsonl `
    data/splits/teacher_judge/v2_active_pilot_001/v2active001_teacher_candidates_all.jsonl `
  --labels-dir data/labeled/teacher_judge `
  --label-prefix teacher_labels_1000 `
  --label-prefix targeted_1200_teacher_labels `
  --label-prefix v2active001/v2active001_teacher_labels `
  --output-dir data/labeled/scorer_binary_sft_v3 `
  --dataset-prefix scorer_binary_v3_conservative `
  --mode all
python scripts/10_evaluate_binary_scorer_predictions.py --help
```

The locked evaluation set at `data/eval/locked_test_ids.json` is applied
automatically when present, so any sample id listed there is forced into the
test split regardless of the candidate file's original split assignment.

LLaMA-Factory WebUI startup is documented in:

```text
reports/llamafactory_startup.md
```

Do not commit API keys, raw datasets, generated JSONL label files, Hugging Face
caches, or LLaMA-Factory model outputs.
