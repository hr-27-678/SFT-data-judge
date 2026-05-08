# Evergreen Cross-Version Scorer Comparison

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-08 19:59:53 UTC |
| Test set | `data\labeled\teacher_judge\evergreen_v2_merged_teacher_labels.jsonl` |
| Records | 900 (clean 800 + flagged 100) |
| LF source dir | `data\labeled\evergreen_lf_v2_noflag` |
| Models compared | v1_4B_confident_noflag, v1_8B_confident_noflag, v2_conservative_noflag, v2_confident_noflag, v3_conservative_noflag, v3_confident_noflag, v4_conservative_noflag, v4_confident_noflag |

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
| v1_4B_confident_noflag | 800 | 72.50% | 0.808 | 0.515 | 47.56% | 100.00% |
| v1_8B_confident_noflag | 800 | 74.50% | 0.837 | 0.410 | 28.86% | 100.00% |
| v2_conservative_noflag | 800 | 75.25% | 0.841 | 0.441 | 31.71% | 100.00% |
| v2_confident_noflag | 800 | 74.25% | 0.839 | 0.364 | 23.98% | 100.00% |
| v3_conservative_noflag | 800 | 76.00% | 0.839 | 0.532 | 44.31% | 100.00% |
| v3_confident_noflag | 800 | 74.75% | 0.841 | 0.392 | 26.42% | 100.00% |
| v4_conservative_noflag | 800 | 77.75% | 0.857 | 0.500 | 36.18% | 100.00% |
| v4_confident_noflag | 800 | 76.50% | 0.852 | 0.430 | 28.86% | 100.00% |

### Conservative GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident_noflag | 100 | 74.00% | 0.824 | 0.500 | 46.43% | 100.00% |
| v1_8B_confident_noflag | 100 | 75.00% | 0.839 | 0.444 | 35.71% | 100.00% |
| v2_conservative_noflag | 100 | 75.00% | 0.843 | 0.390 | 28.57% | 100.00% |
| v2_confident_noflag | 100 | 74.00% | 0.840 | 0.316 | 21.43% | 100.00% |
| v3_conservative_noflag | 100 | 74.00% | 0.822 | 0.519 | 50.00% | 100.00% |
| v3_confident_noflag | 100 | 76.00% | 0.850 | 0.400 | 28.57% | 100.00% |
| v4_conservative_noflag | 100 | 80.00% | 0.873 | 0.524 | 39.29% | 100.00% |
| v4_confident_noflag | 100 | 78.00% | 0.863 | 0.450 | 32.14% | 100.00% |

### Conservative GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident_noflag | 500 | 67.80% | 0.753 | 0.536 | 50.54% | 100.00% |
| v1_8B_confident_noflag | 500 | 70.00% | 0.795 | 0.440 | 32.07% | 100.00% |
| v2_conservative_noflag | 500 | 71.00% | 0.801 | 0.469 | 34.78% | 100.00% |
| v2_confident_noflag | 500 | 69.80% | 0.799 | 0.389 | 26.09% | 100.00% |
| v3_conservative_noflag | 500 | 71.40% | 0.790 | 0.552 | 47.83% | 100.00% |
| v3_confident_noflag | 500 | 70.60% | 0.803 | 0.424 | 29.35% | 100.00% |
| v4_conservative_noflag | 500 | 74.40% | 0.825 | 0.526 | 38.59% | 100.00% |
| v4_confident_noflag | 500 | 71.60% | 0.811 | 0.427 | 28.80% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident_noflag | 225 | 78.22% | 0.861 | 0.495 | 45.28% | 100.00% |
| v1_8B_confident_noflag | 225 | 80.00% | 0.882 | 0.348 | 22.64% | 100.00% |
| v2_conservative_noflag | 225 | 80.44% | 0.884 | 0.389 | 26.42% | 100.00% |
| v2_confident_noflag | 225 | 79.56% | 0.880 | 0.324 | 20.75% | 100.00% |
| v3_conservative_noflag | 225 | 82.22% | 0.891 | 0.512 | 39.62% | 100.00% |
| v3_confident_noflag | 225 | 79.56% | 0.880 | 0.324 | 20.75% | 100.00% |
| v4_conservative_noflag | 225 | 81.78% | 0.890 | 0.468 | 33.96% | 100.00% |
| v4_confident_noflag | 225 | 83.11% | 0.899 | 0.472 | 32.08% | 100.00% |

#### source: openmath_reasoning

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident_noflag | 75 | 86.67% | 0.929 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident_noflag | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v2_conservative_noflag | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v2_confident_noflag | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v3_conservative_noflag | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v3_confident_noflag | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v4_conservative_noflag | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |
| v4_confident_noflag | 75 | 89.33% | 0.943 | 0.200 | 11.11% | 100.00% |

## Confident GT

### Confident GT x clean stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident_noflag | 736 | 75.95% | 0.840 | 0.520 | 52.75% | 100.00% |
| v1_8B_confident_noflag | 736 | 79.35% | 0.874 | 0.437 | 32.42% | 100.00% |
| v2_conservative_noflag | 736 | 80.03% | 0.877 | 0.469 | 35.71% | 100.00% |
| v2_confident_noflag | 736 | 79.35% | 0.876 | 0.392 | 26.92% | 100.00% |
| v3_conservative_noflag | 736 | 80.03% | 0.872 | 0.550 | 49.45% | 100.00% |
| v3_confident_noflag | 736 | 79.62% | 0.877 | 0.414 | 29.12% | 100.00% |
| v4_conservative_noflag | 736 | 83.02% | 0.895 | 0.555 | 42.86% | 100.00% |
| v4_confident_noflag | 736 | 82.07% | 0.891 | 0.488 | 34.62% | 100.00% |

### Confident GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident_noflag | 92 | 77.17% | 0.853 | 0.488 | 50.00% | 100.00% |
| v1_8B_confident_noflag | 92 | 78.26% | 0.867 | 0.412 | 35.00% | 100.00% |
| v2_conservative_noflag | 92 | 81.52% | 0.887 | 0.485 | 40.00% | 100.00% |
| v2_confident_noflag | 92 | 80.43% | 0.883 | 0.400 | 30.00% | 100.00% |
| v3_conservative_noflag | 92 | 76.09% | 0.845 | 0.476 | 50.00% | 100.00% |
| v3_confident_noflag | 92 | 81.52% | 0.889 | 0.452 | 35.00% | 100.00% |
| v4_conservative_noflag | 92 | 85.87% | 0.914 | 0.606 | 50.00% | 100.00% |
| v4_confident_noflag | 92 | 84.78% | 0.908 | 0.563 | 45.00% | 100.00% |

### Confident GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident_noflag | 448 | 71.21% | 0.792 | 0.531 | 55.30% | 100.00% |
| v1_8B_confident_noflag | 448 | 75.67% | 0.842 | 0.468 | 36.36% | 100.00% |
| v2_conservative_noflag | 448 | 76.56% | 0.847 | 0.498 | 39.39% | 100.00% |
| v2_confident_noflag | 448 | 75.89% | 0.848 | 0.419 | 29.55% | 100.00% |
| v3_conservative_noflag | 448 | 75.67% | 0.832 | 0.562 | 53.03% | 100.00% |
| v3_confident_noflag | 448 | 76.34% | 0.849 | 0.448 | 32.58% | 100.00% |
| v4_conservative_noflag | 448 | 80.58% | 0.874 | 0.580 | 45.45% | 100.00% |
| v4_confident_noflag | 448 | 78.35% | 0.863 | 0.487 | 34.85% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident_noflag | 217 | 80.65% | 0.879 | 0.523 | 51.11% | 100.00% |
| v1_8B_confident_noflag | 217 | 82.49% | 0.898 | 0.367 | 24.44% | 100.00% |
| v2_conservative_noflag | 217 | 82.95% | 0.900 | 0.413 | 28.89% | 100.00% |
| v2_confident_noflag | 217 | 82.03% | 0.896 | 0.339 | 22.22% | 100.00% |
| v3_conservative_noflag | 217 | 84.79% | 0.909 | 0.548 | 44.44% | 100.00% |
| v3_confident_noflag | 217 | 82.03% | 0.896 | 0.339 | 22.22% | 100.00% |
| v4_conservative_noflag | 217 | 84.79% | 0.910 | 0.522 | 40.00% | 100.00% |
| v4_confident_noflag | 217 | 85.71% | 0.916 | 0.508 | 35.56% | 100.00% |

#### source: openmath_reasoning

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v1_4B_confident_noflag | 71 | 91.55% | 0.956 | 0.000 | 0.00% | 100.00% |
| v1_8B_confident_noflag | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v2_conservative_noflag | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v2_confident_noflag | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v3_conservative_noflag | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v3_confident_noflag | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v4_conservative_noflag | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |
| v4_confident_noflag | 71 | 94.37% | 0.971 | 0.333 | 20.00% | 100.00% |