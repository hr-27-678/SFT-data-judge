# Binary Scorer Inference Report

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-06 16:53:42 |
| Report type | Batch inference summary |
| Project stage | Scorer deployment / data pool triage |
| Report status | Generated |

## Experiment Context

| Field | Value |
| --- | --- |
| Run name | `evergreen__v3_conservative` |
| Model | `Qwen/Qwen3-8B` |
| Adapter | `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3` |
| Output JSONL | `data\scored\evergreen_v3_conservative_predictions.jsonl` |
| Prompt only | False |

## Summary

| Metric | Value |
| --- | --- |
| Records | 600 |
| keep | 575 |
| not_keep | 25 |
| invalid | 0 |
| schema_valid_rate | 100.00% |

## Source Breakdown

| Source | Records | Keep | Not Keep | Invalid | Schema Valid |
| --- | --- | --- | --- | --- | --- |
| cot_zh | 340 | 323 | 17 | 0 | 100.00% |
| finetome | 185 | 177 | 8 | 0 | 100.00% |
| openmath_reasoning | 75 | 75 | 0 | 0 | 100.00% |

## Rule/Model Triage Buckets

| Source | Flagged But Predicted Keep | Clean But Predicted Not Keep |
| --- | --- | --- |
| cot_zh | 23 | 0 |
| finetome | 52 | 0 |

## Recommended Next Actions

- Inspect `flagged_keep` examples as likely rule/model disagreements.
- Inspect `clean_not_keep` examples as likely hard negatives or over-conservative predictions.
- Send disagreement and high-impact examples to the teacher model before adding irreversible drop rules.
