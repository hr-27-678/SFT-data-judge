# Evergreen v1 Cross-Version Scorer Comparison

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-07 19:21:50 UTC |
| Test set | `data\labeled\teacher_judge\evergreen_test_merged_teacher_labels.jsonl` |
| Records | 600 (clean 500 + flagged 100) |
| LF source dir | `data\labeled\evergreen_lf_noflag` |
| Models compared | v3_conservative, v3_confident, v2_conservative, v2_confident, v1_8B_confident, v1_4B_confident |

## Ground Truth Mapping

Two ground-truth mappings are reported. Each scorer was originally trained
with one of these mappings; both are reported here so cross-mapping
comparisons are also possible.

- **Conservative GT** (600 records): teacher score 1-2-3 -> not_keep, 4-5 -> keep.
- **Confident GT** (556 records): teacher score 1-2 -> not_keep, 4-5 -> keep, score 3 (44 records) skipped.

## Stratum Definition

- **Clean stratum** (500 records): cot_zh 300, finetome 125, openmath_reasoning 75.
- **Flagged stratum** (100 records): cot_zh 40, finetome 60. duplicate_pair flag excluded.

Primary metric: **Not-keep recall**. Higher = scorer correctly rejects more poor samples.

## Conservative GT

### Conservative GT x clean stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 500 | 76.40% | 0.862 | 0.203 | 12.61% | 100.00% |
| v3_confident | 500 | 76.20% | 0.865 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 500 | 76.40% | 0.866 | 0.017 | 0.84% | 100.00% |
| v2_confident | 500 | 76.20% | 0.865 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 500 | 76.60% | 0.867 | 0.033 | 1.68% | 100.00% |
| v1_4B_confident | 500 | 72.00% | 0.825 | 0.293 | 24.37% | 100.00% |

### Conservative GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 100 | 74.00% | 0.822 | 0.519 | 50.00% | 100.00% |
| v3_confident | 100 | 76.00% | 0.850 | 0.400 | 28.57% | 100.00% |
| v2_conservative | 100 | 75.00% | 0.843 | 0.390 | 28.57% | 100.00% |
| v2_confident | 100 | 74.00% | 0.840 | 0.316 | 21.43% | 100.00% |
| v1_8B_confident | 100 | 75.00% | 0.839 | 0.444 | 35.71% | 100.00% |
| v1_4B_confident | 100 | 74.00% | 0.824 | 0.500 | 46.43% | 100.00% |

### Conservative GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 300 | 71.67% | 0.826 | 0.234 | 15.12% | 100.00% |
| v3_confident | 300 | 71.33% | 0.833 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 300 | 71.67% | 0.834 | 0.023 | 1.16% | 100.00% |
| v2_confident | 300 | 71.33% | 0.833 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 300 | 72.00% | 0.836 | 0.045 | 2.33% | 100.00% |
| v1_4B_confident | 300 | 66.33% | 0.777 | 0.313 | 26.74% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 125 | 80.80% | 0.892 | 0.143 | 8.33% | 100.00% |
| v3_confident | 125 | 80.80% | 0.894 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 125 | 80.80% | 0.894 | 0.000 | 0.00% | 100.00% |
| v2_confident | 125 | 80.80% | 0.894 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 125 | 80.80% | 0.894 | 0.000 | 0.00% | 100.00% |
| v1_4B_confident | 125 | 76.80% | 0.861 | 0.293 | 25.00% | 100.00% |

#### source: openmath_reasoning

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v3_confident | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v2_confident | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v1_4B_confident | 75 | 86.67% | 0.929 | 0.000 | 0.00% | 100.00% |

## Confident GT

### Confident GT x clean stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 464 | 81.47% | 0.895 | 0.204 | 13.25% | 100.00% |
| v3_confident | 464 | 82.11% | 0.902 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 464 | 82.33% | 0.903 | 0.024 | 1.20% | 100.00% |
| v2_confident | 464 | 82.11% | 0.902 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 464 | 82.33% | 0.903 | 0.024 | 1.20% | 100.00% |
| v1_4B_confident | 464 | 76.08% | 0.856 | 0.284 | 26.51% | 100.00% |

### Confident GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 92 | 76.09% | 0.845 | 0.476 | 50.00% | 100.00% |
| v3_confident | 92 | 81.52% | 0.889 | 0.452 | 35.00% | 100.00% |
| v2_conservative | 92 | 81.52% | 0.887 | 0.485 | 40.00% | 100.00% |
| v2_confident | 92 | 80.43% | 0.883 | 0.400 | 30.00% | 100.00% |
| v1_8B_confident | 92 | 78.26% | 0.867 | 0.412 | 35.00% | 100.00% |
| v1_4B_confident | 92 | 77.17% | 0.853 | 0.488 | 50.00% | 100.00% |

### Confident GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 272 | 77.57% | 0.869 | 0.228 | 15.52% | 100.00% |
| v3_confident | 272 | 78.68% | 0.881 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 272 | 79.04% | 0.882 | 0.034 | 1.72% | 100.00% |
| v2_confident | 272 | 78.68% | 0.881 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 272 | 79.04% | 0.882 | 0.034 | 1.72% | 100.00% |
| v1_4B_confident | 272 | 70.59% | 0.815 | 0.286 | 27.59% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 121 | 83.47% | 0.908 | 0.167 | 10.00% | 100.00% |
| v3_confident | 121 | 83.47% | 0.910 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 121 | 83.47% | 0.910 | 0.000 | 0.00% | 100.00% |
| v2_confident | 121 | 83.47% | 0.910 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 121 | 83.47% | 0.910 | 0.000 | 0.00% | 100.00% |
| v1_4B_confident | 121 | 79.34% | 0.878 | 0.324 | 30.00% | 100.00% |

#### source: openmath_reasoning

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v3_confident | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v2_confident | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v1_4B_confident | 71 | 91.55% | 0.956 | 0.000 | 0.00% | 100.00% |