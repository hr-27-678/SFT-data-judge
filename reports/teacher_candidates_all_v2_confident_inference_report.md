# Binary Scorer Inference Report

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-03 16:17:46 |
| Report type | Batch inference summary |
| Project stage | Scorer deployment / data pool triage |
| Report status | Generated |

## Experiment Context

| Field | Value |
| --- | --- |
| Run name | `scorer_binary_v2_confident_qwen3_8b_lora_e3` |
| Model | `Qwen/Qwen3-8B` |
| Adapter | `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_confident_qwen3_8b_lora_e3` |
| Output JSONL | `data\scored\teacher_candidates_all_v2_confident_predictions.jsonl` |
| Prompt only | False |

## Summary

| Metric | Value |
| --- | --- |
| Records | 3600 |
| keep | 2953 |
| not_keep | 647 |
| invalid | 0 |
| schema_valid_rate | 100.00% |

## Source Breakdown

| Source | Records | Keep | Not Keep | Invalid | Schema Valid |
| --- | --- | --- | --- | --- | --- |
| cot_zh | 1200 | 880 | 320 | 0 | 100.00% |
| finetome | 1200 | 966 | 234 | 0 | 100.00% |
| openmath_reasoning | 1200 | 1107 | 93 | 0 | 100.00% |

## Rule/Model Triage Buckets

| Source | Flagged But Predicted Keep | Clean But Predicted Not Keep |
| --- | --- | --- |
| cot_zh | 150 | 263 |
| finetome | 203 | 197 |
| openmath_reasoning | 2 | 30 |

## Recommended Next Actions

- Inspect `flagged_keep` examples as likely rule/model disagreements.
- Inspect `clean_not_keep` examples as likely hard negatives or over-conservative predictions.
- Send disagreement and high-impact examples to the teacher model before adding irreversible drop rules.
