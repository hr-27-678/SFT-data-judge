# Teacher Review Batch Report

## Report Metadata

| Field | Value |
| --- | --- |
| Report type | Active-learning teacher batch |
| Project stage | V2 scorer triage / teacher relabeling |
| Report status | Generated |
| Batch prefix | `v2active002` |

## Experiment Context

| Field | Value |
| --- | --- |
| Input priority file | `data\scored\v3_unlabeled_pool_5000_teacher_review_priority.jsonl` |
| Existing label exclusion | original sample `id` only |
| Max samples | 999999 |
| Ordering | deterministic_priority_order |
| Current use | Send selected unlabeled hard cases to the teacher model |

## Summary

| Metric | Count |
| --- | --- |
| Input records | 2365 |
| Already teacher-labeled by original id | 0 |
| Selected unlabeled records | 2365 |
| Duplicate ids inside input skipped | 0 |

## Known Label Files

| Path | Records |
| --- | --- |
| \\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\teacher_judge\pilot_teacher_labels.jsonl | 60 |
| \\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\teacher_judge\teacher_labels_1000.jsonl | 1000 |
| \\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\teacher_judge\targeted_1200_teacher_labels.jsonl | 1200 |
| \\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\teacher_judge\v2active001\v2active001_teacher_labels.jsonl | 390 |

## Outputs

| Artifact | Path |
| --- | --- |
| all_candidates | `data\splits\teacher_judge\v2_active_pilot_002\v2active002_teacher_candidates_all.jsonl` |
| train_candidates | `data\splits\teacher_judge\v2_active_pilot_002\v2active002_teacher_candidates_train.jsonl` |
| valid_candidates | `data\splits\teacher_judge\v2_active_pilot_002\v2active002_teacher_candidates_valid.jsonl` |
| test_candidates | `data\splits\teacher_judge\v2_active_pilot_002\v2active002_teacher_candidates_test.jsonl` |
| already_labeled_matches | `data\splits\teacher_judge\v2_active_pilot_002\v2active002_already_labeled_matches.jsonl` |
| duplicate_input_ids | `data\splits\teacher_judge\v2_active_pilot_002\v2active002_duplicate_input_ids.jsonl` |

## Selected By Source

| Source | Records |
| --- | --- |
| cot_zh | 1742 |
| finetome | 580 |
| openmath_reasoning | 43 |

## Selected By Split

| Split | Records |
| --- | --- |
| train | 1900 |
| valid | 233 |
| test | 232 |

## Selected By Agreement Bucket

| Agreement bucket | Records |
| --- | --- |
| conf_not_keep__cons_not_keep | 1237 |
| conf_keep__cons_not_keep | 644 |
| conf_keep__cons_keep | 480 |
| conf_not_keep__cons_keep | 4 |

## Selected By Priority Reason

| Priority reason | Records |
| --- | --- |
| conservative_clean_not_keep | 1617 |
| both_not_keep | 1237 |
| confident_clean_not_keep | 1068 |
| model_disagreement | 648 |
| flagged_but_model_keep | 485 |
| calibration_random | 88 |

## Already Labeled By Agreement Bucket

| Agreement bucket | Records |
| --- | --- |

## Recommended Commands

Render prompts:

```powershell
python scripts/04_teacher_judge.py --input data\splits\teacher_judge\v2_active_pilot_002\v2active002_teacher_candidates_all.jsonl --output-dir data/labeled/teacher_judge/v2active002 --output-name v2active002_teacher_prompts.jsonl --dry-run
```

Run teacher labeling:

```powershell
python scripts/04_teacher_judge.py --input data\splits\teacher_judge\v2_active_pilot_002\v2active002_teacher_candidates_all.jsonl --output-dir data/labeled/teacher_judge/v2active002 --output-name v2active002_teacher_labels.jsonl --no-dry-run --resume
```

Split/analyze labels after the teacher run:

```powershell
python scripts/05_analyze_teacher_labels.py --input data/labeled/teacher_judge/v2active002/v2active002_teacher_labels.jsonl --output-dir data/labeled/teacher_judge --split-prefix v2active002_teacher_labels --report-path reports/teacher_label_report_v2active002.md
```

Then add the new candidate file and label prefix to `scripts/09_build_binary_scorer_sft.py` when building v3.
