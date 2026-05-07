# Evergreen v1 Cross-Version Scorer Comparison

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-07 23:26:51 UTC |
| Test set | `data\labeled\teacher_judge\evergreen_v2_merged_teacher_labels.jsonl` |
| Records | 900 (clean 800 + flagged 100) |
| LF source dir | `data\labeled\evergreen_lf_v2_noflag` |
| Models compared | v4_conservative_noflag |

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
| v4_conservative_noflag | 800 | 77.75% | 0.857 | 0.500 | 36.18% | 100.00% |

### Conservative GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative_noflag | 100 | 80.00% | 0.873 | 0.524 | 39.29% | 100.00% |

### Conservative GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative_noflag | 500 | 74.40% | 0.825 | 0.526 | 38.59% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative_noflag | 225 | 81.78% | 0.890 | 0.468 | 33.96% | 100.00% |

#### source: openmath_reasoning

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative_noflag | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |

## Confident GT

### Confident GT x clean stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative_noflag | 736 | 83.02% | 0.895 | 0.555 | 42.86% | 100.00% |

### Confident GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative_noflag | 92 | 85.87% | 0.914 | 0.606 | 50.00% | 100.00% |

### Confident GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative_noflag | 448 | 80.58% | 0.874 | 0.580 | 45.45% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative_noflag | 217 | 84.79% | 0.910 | 0.522 | 40.00% | 100.00% |

#### source: openmath_reasoning

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative_noflag | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |