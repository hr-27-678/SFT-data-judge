# Binary Scorer Inference Report

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-10 16:42:00 |
| Report type | Batch inference summary |
| Project stage | Scorer deployment / data pool triage |
| Report status | Generated |

## Experiment Context

| Field | Value |
| --- | --- |
| Run name | `phase_e_v4_confident_clean_15k` |
| Model | `Qwen/Qwen3-8B` |
| Adapter | `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v4_confident_qwen3_8b_lora_e3` |
| Output JSONL | `data\scored\phase_e_v4_confident_clean_15k.jsonl` |
| Prompt only | False |

## Summary

| Metric | Value |
| --- | --- |
| Records | 15000 |
| keep | 11111 |
| not_keep | 3889 |
| invalid | 0 |
| schema_valid_rate | 100.00% |

## Source Breakdown

| Source | Records | Keep | Not Keep | Invalid | Schema Valid |
| --- | --- | --- | --- | --- | --- |
| cot_zh | 5698 | 3861 | 1837 | 0 | 100.00% |
| finetome | 7863 | 5836 | 2027 | 0 | 100.00% |
| openmath_reasoning | 1439 | 1414 | 25 | 0 | 100.00% |

## Rule/Model Triage Buckets

| Source | Flagged But Predicted Keep | Clean But Predicted Not Keep |
| --- | --- | --- |
| cot_zh | 0 | 1837 |
| finetome | 0 | 2027 |
| openmath_reasoning | 0 | 25 |

## Recommended Next Actions

- Inspect `flagged_keep` examples as likely rule/model disagreements.
- Inspect `clean_not_keep` examples as likely hard negatives or over-conservative predictions.
- Send disagreement and high-impact examples to the teacher model before adding irreversible drop rules.
