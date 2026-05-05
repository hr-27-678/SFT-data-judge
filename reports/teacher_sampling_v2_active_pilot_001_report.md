# Teacher Review Batch Report

## Report Metadata

| Field | Value |
| --- | --- |
| Report type | Active-learning teacher batch |
| Project stage | V2 scorer triage / teacher relabeling |
| Report status | Generated |
| Batch prefix | `v2active001` |

## Experiment Context

| Field | Value |
| --- | --- |
| Input priority file | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\scored\teacher_candidates_all_v2_teacher_review_priority.jsonl` |
| Existing label exclusion | original sample `id` only |
| Max samples | 500 |
| Ordering | deterministic_priority_order |
| Current use | Send selected unlabeled hard cases to the teacher model |

## Summary

| Metric | Count |
| --- | --- |
| Input records | 1215 |
| Already teacher-labeled by original id | 827 |
| Selected unlabeled records | 388 |
| Duplicate ids inside input skipped | 0 |

## Known Label Files

| Path | Records |
| --- | --- |
| \\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\teacher_judge\teacher_labels_1000.jsonl | 1000 |
| \\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\labeled\teacher_judge\targeted_1200_teacher_labels.jsonl | 1200 |

## Outputs

| Artifact | Path |
| --- | --- |
| all_candidates | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\splits\teacher_judge\v2_active_pilot_001\v2active001_teacher_candidates_all.jsonl` |
| train_candidates | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\splits\teacher_judge\v2_active_pilot_001\v2active001_teacher_candidates_train.jsonl` |
| valid_candidates | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\splits\teacher_judge\v2_active_pilot_001\v2active001_teacher_candidates_valid.jsonl` |
| test_candidates | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\splits\teacher_judge\v2_active_pilot_001\v2active001_teacher_candidates_test.jsonl` |
| already_labeled_matches | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\splits\teacher_judge\v2_active_pilot_001\v2active001_already_labeled_matches.jsonl` |
| duplicate_input_ids | `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\splits\teacher_judge\v2_active_pilot_001\v2active001_duplicate_input_ids.jsonl` |

## Selected By Source

| Source | Records |
| --- | --- |
| finetome | 260 |
| cot_zh | 93 |
| openmath_reasoning | 35 |

## Selected By Split

| Split | Records |
| --- | --- |
| train | 305 |
| valid | 43 |
| test | 40 |

## Selected By Agreement Bucket

| Agreement bucket | Records |
| --- | --- |
| conf_not_keep__cons_not_keep | 246 |
| conf_keep__cons_not_keep | 89 |
| conf_keep__cons_keep | 52 |
| conf_not_keep__cons_keep | 1 |

## Selected By Priority Reason

| Priority reason | Records |
| --- | --- |
| conservative_clean_not_keep | 321 |
| both_not_keep | 246 |
| confident_clean_not_keep | 236 |
| model_disagreement | 90 |
| flagged_but_model_keep | 55 |

## Already Labeled By Agreement Bucket

| Agreement bucket | Records |
| --- | --- |
| conf_not_keep__cons_not_keep | 400 |
| conf_keep__cons_keep | 244 |
| conf_keep__cons_not_keep | 183 |

## Recommended Commands

Render prompts:

```powershell
python scripts/04_teacher_judge.py --input \\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\splits\teacher_judge\v2_active_pilot_001\v2active001_teacher_candidates_all.jsonl --output-dir data/labeled/teacher_judge/v2active001 --output-name v2active001_teacher_prompts.jsonl --dry-run
```

Run teacher labeling:

```powershell
python scripts/04_teacher_judge.py --input \\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge\data\splits\teacher_judge\v2_active_pilot_001\v2active001_teacher_candidates_all.jsonl --output-dir data/labeled/teacher_judge/v2active001 --output-name v2active001_teacher_labels.jsonl --no-dry-run --resume
```

Split/analyze labels after the teacher run:

```powershell
python scripts/05_analyze_teacher_labels.py --input data/labeled/teacher_judge/v2active001/v2active001_teacher_labels.jsonl --output-dir data/labeled/teacher_judge --split-prefix v2active001_teacher_labels --report-path reports/teacher_label_report_v2active001.md --dedupe-by-id
```

Then add the new candidate file and label prefix to `scripts/09_build_binary_scorer_sft.py` when building v3.
