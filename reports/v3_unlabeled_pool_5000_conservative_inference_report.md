# Binary Scorer Inference Report

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-06 12:37:51 |
| Report type | Batch inference summary |
| Project stage | Scorer deployment / data pool triage |
| Report status | Generated |

## Experiment Context

| Field | Value |
| --- | --- |
| Run name | `scorer_binary_v3_conservative_qwen3_8b_lora_e3` |
| Model | `Qwen/Qwen3-8B` |
| Adapter | `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3` |
| Output JSONL | `data\scored\v3_unlabeled_pool_5000_conservative_predictions.jsonl` |
| Prompt only | False |

## Summary

| Metric | Value |
| --- | --- |
| Records | 5000 |
| keep | 3119 |
| not_keep | 1881 |
| invalid | 0 |
| schema_valid_rate | 100.00% |

## Source Breakdown

| Source | Records | Keep | Not Keep | Invalid | Schema Valid |
| --- | --- | --- | --- | --- | --- |
| cot_zh | 3000 | 1512 | 1488 | 0 | 100.00% |
| finetome | 1250 | 882 | 368 | 0 | 100.00% |
| openmath_reasoning | 750 | 725 | 25 | 0 | 100.00% |

## Rule/Model Triage Buckets

| Source | Flagged But Predicted Keep | Clean But Predicted Not Keep |
| --- | --- | --- |
| cot_zh | 199 | 1280 |
| finetome | 194 | 312 |
| openmath_reasoning | 0 | 25 |

## Recommended Next Actions

- Inspect `flagged_keep` examples as likely rule/model disagreements.
- Inspect `clean_not_keep` examples as likely hard negatives or over-conservative predictions.
- Send disagreement and high-impact examples to the teacher model before adding irreversible drop rules.
