# Evergreen Cross-Version Scorer Comparison

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-08 19:25:01 UTC |
| Test set | `data\labeled\teacher_judge\evergreen_v2_merged_teacher_labels.jsonl` |
| Records | 900 (clean 800 + flagged 100) |
| LF source dir | `data\labeled\evergreen_lf_v2_noflag` |
| Models compared | v4_confident_noflag |

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
| v4_confident_noflag | 800 | 76.50% | 0.852 | 0.430 | 28.86% | 100.00% |

### Conservative GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_confident_noflag | 100 | 78.00% | 0.863 | 0.450 | 32.14% | 100.00% |

### Conservative GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_confident_noflag | 500 | 71.60% | 0.811 | 0.427 | 28.80% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_confident_noflag | 225 | 83.11% | 0.899 | 0.472 | 32.08% | 100.00% |

#### source: openmath_reasoning

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_confident_noflag | 75 | 89.33% | 0.943 | 0.200 | 11.11% | 100.00% |

## Confident GT

### Confident GT x clean stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_confident_noflag | 736 | 82.07% | 0.891 | 0.488 | 34.62% | 100.00% |

### Confident GT x flagged stratum

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_confident_noflag | 92 | 84.78% | 0.908 | 0.563 | 45.00% | 100.00% |

### Confident GT x clean stratum, by source

#### source: cot_zh

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_confident_noflag | 448 | 78.35% | 0.863 | 0.487 | 34.85% | 100.00% |

#### source: finetome

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_confident_noflag | 217 | 85.71% | 0.916 | 0.508 | 35.56% | 100.00% |

#### source: openmath_reasoning

| Model | N | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | --- | --- | --- | --- | --- | --- |
| v4_confident_noflag | 71 | 94.37% | 0.971 | 0.333 | 20.00% | 100.00% |