# Evergreen v1 Cross-Version Scorer Comparison

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-07 23:26:40 UTC |
| Test set | `data\labeled\teacher_judge\evergreen_v2_merged_teacher_labels.jsonl` |
| Records | 900 (clean 800 + flagged 100) |
| LF source dir | `data\labeled\evergreen_lf_v2` |
| Models compared | v4_conservative |

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
| v4_conservative | 800 | 77.75% | 0.857 | 0.500 | 36.18% | 100.00% |

### Conservative GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative | 100 | 80.00% | 0.877 | 0.474 | 32.14% | 100.00% |

### Conservative GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative | 500 | 74.40% | 0.825 | 0.526 | 38.59% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative | 225 | 81.78% | 0.890 | 0.468 | 33.96% | 100.00% |

#### source: openmath_reasoning

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative | 75 | 88.00% | 0.936 | 0.000 | 0.00% | 100.00% |

## Confident GT

### Confident GT x clean stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative | 736 | 83.15% | 0.896 | 0.560 | 43.41% | 100.00% |

### Confident GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative | 92 | 86.96% | 0.922 | 0.600 | 45.00% | 100.00% |

### Confident GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative | 448 | 80.80% | 0.875 | 0.587 | 46.21% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative | 217 | 84.79% | 0.910 | 0.522 | 40.00% | 100.00% |

#### source: openmath_reasoning

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_conservative | 71 | 92.96% | 0.964 | 0.000 | 0.00% | 100.00% |