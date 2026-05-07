# Evergreen v1 Cross-Version Scorer Comparison

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-06 23:09:48 UTC |
| Test set | `data\labeled\teacher_judge\evergreen_test_merged_teacher_labels.jsonl` |
| Records | 600 (clean 500 + flagged 100) |
| Lock | `data\eval\evergreen_test_ids.json` |
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
| v3_conservative | 500 | 77.00% | 0.866 | 0.173 | 10.08% | 100.00% |
| v3_confident | 500 | 76.20% | 0.865 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 500 | 76.20% | 0.865 | 0.000 | 0.00% | 100.00% |
| v2_confident | 500 | 76.20% | 0.865 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 500 | 76.00% | 0.864 | 0.000 | 0.00% | 100.00% |
| v1_4B_confident | 500 | 72.60% | 0.832 | 0.259 | 20.17% | 100.00% |

### Conservative GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 100 | 79.00% | 0.861 | 0.571 | 50.00% | 100.00% |
| v3_confident | 100 | 76.00% | 0.855 | 0.294 | 17.86% | 100.00% |
| v2_conservative | 100 | 75.00% | 0.847 | 0.324 | 21.43% | 100.00% |
| v2_confident | 100 | 76.00% | 0.855 | 0.294 | 17.86% | 100.00% |
| v1_8B_confident | 100 | 76.00% | 0.844 | 0.478 | 39.29% | 100.00% |
| v1_4B_confident | 100 | 74.00% | 0.827 | 0.480 | 42.86% | 100.00% |

### Conservative GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 300 | 72.33% | 0.832 | 0.210 | 12.79% | 100.00% |
| v3_confident | 300 | 71.33% | 0.833 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 300 | 71.33% | 0.833 | 0.000 | 0.00% | 100.00% |
| v2_confident | 300 | 71.33% | 0.833 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 300 | 71.00% | 0.830 | 0.000 | 0.00% | 100.00% |
| v1_4B_confident | 300 | 67.67% | 0.792 | 0.271 | 20.93% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 125 | 81.60% | 0.898 | 0.080 | 4.17% | 100.00% |
| v3_confident | 125 | 80.80% | 0.894 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 125 | 80.80% | 0.894 | 0.000 | 0.00% | 100.00% |
| v2_confident | 125 | 80.80% | 0.894 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 125 | 80.80% | 0.894 | 0.000 | 0.00% | 100.00% |
| v1_4B_confident | 125 | 76.00% | 0.856 | 0.286 | 25.00% | 100.00% |

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
| v3_conservative | 464 | 82.11% | 0.900 | 0.162 | 9.64% | 100.00% |
| v3_confident | 464 | 82.11% | 0.902 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 464 | 82.11% | 0.902 | 0.000 | 0.00% | 100.00% |
| v2_confident | 464 | 82.11% | 0.902 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 464 | 81.90% | 0.900 | 0.000 | 0.00% | 100.00% |
| v1_4B_confident | 464 | 76.94% | 0.864 | 0.252 | 21.69% | 100.00% |

### Confident GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 92 | 81.52% | 0.884 | 0.541 | 50.00% | 100.00% |
| v3_confident | 92 | 82.61% | 0.899 | 0.385 | 25.00% | 100.00% |
| v2_conservative | 92 | 81.52% | 0.890 | 0.414 | 30.00% | 100.00% |
| v2_confident | 92 | 82.61% | 0.899 | 0.385 | 25.00% | 100.00% |
| v1_8B_confident | 92 | 79.35% | 0.872 | 0.457 | 40.00% | 100.00% |
| v1_4B_confident | 92 | 78.26% | 0.861 | 0.500 | 50.00% | 100.00% |

### Confident GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 272 | 78.31% | 0.875 | 0.192 | 12.07% | 100.00% |
| v3_confident | 272 | 78.68% | 0.881 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 272 | 78.68% | 0.881 | 0.000 | 0.00% | 100.00% |
| v2_confident | 272 | 78.68% | 0.881 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 272 | 78.31% | 0.878 | 0.000 | 0.00% | 100.00% |
| v1_4B_confident | 272 | 72.43% | 0.831 | 0.242 | 20.69% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 121 | 84.30% | 0.914 | 0.095 | 5.00% | 100.00% |
| v3_confident | 121 | 83.47% | 0.910 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 121 | 83.47% | 0.910 | 0.000 | 0.00% | 100.00% |
| v2_confident | 121 | 83.47% | 0.910 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 121 | 83.47% | 0.910 | 0.000 | 0.00% | 100.00% |
| v1_4B_confident | 121 | 78.51% | 0.873 | 0.316 | 30.00% | 100.00% |

#### source: openmath_reasoning

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v3_conservative | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v3_confident | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v2_confident | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v1_4B_confident | 71 | 91.55% | 0.956 | 0.000 | 0.00% | 100.00% |