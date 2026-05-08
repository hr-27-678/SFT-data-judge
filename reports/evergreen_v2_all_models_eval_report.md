# Evergreen Cross-Version Scorer Comparison

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-08 19:59:32 UTC |
| Test set | `data\labeled\teacher_judge\evergreen_v2_merged_teacher_labels.jsonl` |
| Records | 900 (clean 800 + flagged 100) |
| LF source dir | `data\labeled\evergreen_lf_v2` |
| Models compared | v1_4B_confident, v1_8B_confident, v2_conservative, v2_confident, v3_conservative, v3_confident, v4_conservative, v4_confident |

## Ground Truth Mapping

Two ground-truth mappings are reported. Each scorer was originally trained
with one of these mappings; both are reported here so cross-mapping
comparisons are also possible.

- **Conservative GT** (900 records): teacher score 1-2-3 -> not_keep, 4-5 -> keep.
- **Confident GT** (828 records): teacher score 1-2 -> not_keep, 4-5 -> keep, score 3 (72 records) skipped.

## Stratum Definition

- **Clean stratum** (800 records): cot_zh 500, finetome 225, openmath_reasoning 75.
- **Flagged stratum** (100 records): cot_zh 40, finetome 60.

Primary metric: **Not-keep recall**. Higher = scorer correctly rejects more poor samples.

## Conservative GT

### Conservative GT x clean stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident | 800 | 72.38% | 0.811 | 0.490 | 43.09% | 100.00% |
| v1_8B_confident | 800 | 74.12% | 0.836 | 0.386 | 26.42% | 100.00% |
| v2_conservative | 800 | 75.00% | 0.842 | 0.408 | 28.05% | 100.00% |
| v2_confident | 800 | 74.25% | 0.839 | 0.356 | 23.17% | 100.00% |
| v3_conservative | 800 | 76.25% | 0.842 | 0.520 | 41.87% | 100.00% |
| v3_confident | 800 | 74.62% | 0.841 | 0.379 | 25.20% | 100.00% |
| v4_conservative | 800 | 77.75% | 0.857 | 0.500 | 36.18% | 100.00% |
| v4_confident | 800 | 76.50% | 0.852 | 0.427 | 28.46% | 100.00% |

### Conservative GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident | 100 | 74.00% | 0.827 | 0.480 | 42.86% | 100.00% |
| v1_8B_confident | 100 | 76.00% | 0.844 | 0.478 | 39.29% | 100.00% |
| v2_conservative | 100 | 75.00% | 0.847 | 0.324 | 21.43% | 100.00% |
| v2_confident | 100 | 76.00% | 0.855 | 0.294 | 17.86% | 100.00% |
| v3_conservative | 100 | 79.00% | 0.861 | 0.571 | 50.00% | 100.00% |
| v3_confident | 100 | 76.00% | 0.855 | 0.294 | 17.86% | 100.00% |
| v4_conservative | 100 | 80.00% | 0.877 | 0.474 | 32.14% | 100.00% |
| v4_confident | 100 | 80.00% | 0.877 | 0.474 | 32.14% | 100.00% |

### Conservative GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident | 500 | 67.80% | 0.761 | 0.508 | 45.11% | 100.00% |
| v1_8B_confident | 500 | 69.60% | 0.795 | 0.415 | 29.35% | 100.00% |
| v2_conservative | 500 | 70.40% | 0.801 | 0.426 | 29.89% | 100.00% |
| v2_confident | 500 | 69.40% | 0.798 | 0.370 | 24.46% | 100.00% |
| v3_conservative | 500 | 71.60% | 0.795 | 0.539 | 45.11% | 100.00% |
| v3_confident | 500 | 70.20% | 0.802 | 0.397 | 26.63% | 100.00% |
| v4_conservative | 500 | 74.40% | 0.825 | 0.526 | 38.59% | 100.00% |
| v4_confident | 500 | 71.40% | 0.811 | 0.416 | 27.72% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident | 225 | 77.78% | 0.859 | 0.479 | 43.40% | 100.00% |
| v1_8B_confident | 225 | 79.56% | 0.880 | 0.324 | 20.75% | 100.00% |
| v2_conservative | 225 | 80.89% | 0.887 | 0.394 | 26.42% | 100.00% |
| v2_confident | 225 | 80.44% | 0.885 | 0.353 | 22.64% | 100.00% |
| v3_conservative | 225 | 82.67% | 0.895 | 0.506 | 37.74% | 100.00% |
| v3_confident | 225 | 80.00% | 0.881 | 0.366 | 24.53% | 100.00% |
| v4_conservative | 225 | 81.78% | 0.890 | 0.468 | 33.96% | 100.00% |
| v4_confident | 225 | 83.56% | 0.902 | 0.493 | 33.96% | 100.00% |

#### source: openmath_reasoning

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident | 75 | 86.67% | 0.929 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v2_confident | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v3_conservative | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v3_confident | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v4_conservative | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v4_confident | 75 | 89.33% | 0.943 | 0.200 | 11.11% | 100.00% |

## Confident GT

### Confident GT x clean stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident | 736 | 75.95% | 0.842 | 0.493 | 47.25% | 100.00% |
| v1_8B_confident | 736 | 79.21% | 0.873 | 0.418 | 30.22% | 100.00% |
| v2_conservative | 736 | 79.89% | 0.878 | 0.435 | 31.32% | 100.00% |
| v2_confident | 736 | 79.48% | 0.877 | 0.389 | 26.37% | 100.00% |
| v3_conservative | 736 | 80.30% | 0.875 | 0.537 | 46.15% | 100.00% |
| v3_confident | 736 | 79.62% | 0.877 | 0.405 | 28.02% | 100.00% |
| v4_conservative | 736 | 83.15% | 0.896 | 0.560 | 43.41% | 100.00% |
| v4_confident | 736 | 82.07% | 0.891 | 0.484 | 34.07% | 100.00% |

### Confident GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident | 92 | 78.26% | 0.861 | 0.500 | 50.00% | 100.00% |
| v1_8B_confident | 92 | 79.35% | 0.872 | 0.457 | 40.00% | 100.00% |
| v2_conservative | 92 | 81.52% | 0.890 | 0.414 | 30.00% | 100.00% |
| v2_confident | 92 | 82.61% | 0.899 | 0.385 | 25.00% | 100.00% |
| v3_conservative | 92 | 81.52% | 0.884 | 0.541 | 50.00% | 100.00% |
| v3_confident | 92 | 82.61% | 0.899 | 0.385 | 25.00% | 100.00% |
| v4_conservative | 92 | 86.96% | 0.922 | 0.600 | 45.00% | 100.00% |
| v4_confident | 92 | 86.96% | 0.922 | 0.600 | 45.00% | 100.00% |

### Confident GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident | 448 | 71.43% | 0.800 | 0.500 | 48.48% | 100.00% |
| v1_8B_confident | 448 | 75.45% | 0.842 | 0.444 | 33.33% | 100.00% |
| v2_conservative | 448 | 76.12% | 0.847 | 0.451 | 33.33% | 100.00% |
| v2_confident | 448 | 75.45% | 0.846 | 0.396 | 27.27% | 100.00% |
| v3_conservative | 448 | 75.89% | 0.836 | 0.546 | 49.24% | 100.00% |
| v3_confident | 448 | 76.12% | 0.850 | 0.422 | 29.55% | 100.00% |
| v4_conservative | 448 | 80.80% | 0.875 | 0.587 | 46.21% | 100.00% |
| v4_confident | 448 | 78.12% | 0.862 | 0.473 | 33.33% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident | 217 | 80.18% | 0.876 | 0.506 | 48.89% | 100.00% |
| v1_8B_confident | 217 | 82.49% | 0.898 | 0.367 | 24.44% | 100.00% |
| v2_conservative | 217 | 83.41% | 0.903 | 0.419 | 28.89% | 100.00% |
| v2_confident | 217 | 83.41% | 0.904 | 0.400 | 26.67% | 100.00% |
| v3_conservative | 217 | 85.25% | 0.912 | 0.543 | 42.22% | 100.00% |
| v3_confident | 217 | 82.49% | 0.898 | 0.387 | 26.67% | 100.00% |
| v4_conservative | 217 | 84.79% | 0.910 | 0.522 | 40.00% | 100.00% |
| v4_confident | 217 | 86.18% | 0.919 | 0.531 | 37.78% | 100.00% |

#### source: openmath_reasoning

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident | 71 | 91.55% | 0.956 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v2_conservative | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v2_confident | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v3_conservative | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v3_confident | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v4_conservative | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v4_confident | 71 | 94.37% | 0.971 | 0.333 | 20.00% | 100.00% |