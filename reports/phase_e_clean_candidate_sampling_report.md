# Phase E Clean Candidate Sampling Report

## Purpose

Prepare an exclusion-safe clean candidate pool for local v4 scorer labeling.
Both v4 conservative and v4 confident should score this same file.

## Output

- Candidate JSONL: `data\splits\phase_e\phase_e_clean_candidate_15k.jsonl`
- Metrics JSON: `data\splits\phase_e\phase_e_clean_candidate_15k_metrics.json`
- Total: 15000
- Seed: 20260508

## Exclusion Policy

Excluded any source sample id found under:

- `data\labeled`: +7256 ids
- `data\splits\teacher_judge`: +4756 ids
- `data\eval`: +0 ids

Total unique excluded ids: 12012.
Selected/excluded overlap check: 0.
Duplicate selected ids: 0.

## Source Distribution

| Source | Selected | Eligible | Clean pool |
| --- | ---: | ---: | ---: |
| `cot_zh` | 5698 | 67532 | 72355 |
| `finetome` | 7863 | 93192 | 96561 |
| `openmath_reasoning` | 1439 | 17055 | 19187 |
| **Total** | **15000** | **177779** | **188103** |

## Next Commands

```powershell
$PY = "C:\Users\haoran27\miniconda3\envs\llamafactory\python.exe"

& $PY scripts/12_infer_binary_scorer.py `
  --input data\splits\phase_e\phase_e_clean_candidate_15k.jsonl `
  --output data/scored/phase_e_v4_conservative_clean_15k.jsonl `
  --report-md reports/phase_e_v4_conservative_clean_15k_inference_report.md `
  --metrics-json data/scored/phase_e_v4_conservative_clean_15k_metrics.json `
  --run-name phase_e_v4_conservative_clean_15k `
  --adapter-name-or-path "C:\Users\haoran27\llamafactory_outputs\scorer_binary_v4_conservative_qwen3_8b_lora_e3" `
  --batch-size 1 `
  --torch-dtype bfloat16

& $PY scripts/12_infer_binary_scorer.py `
  --input data\splits\phase_e\phase_e_clean_candidate_15k.jsonl `
  --output data/scored/phase_e_v4_confident_clean_15k.jsonl `
  --report-md reports/phase_e_v4_confident_clean_15k_inference_report.md `
  --metrics-json data/scored/phase_e_v4_confident_clean_15k_metrics.json `
  --run-name phase_e_v4_confident_clean_15k `
  --adapter-name-or-path "C:\Users\haoran27\llamafactory_outputs\scorer_binary_v4_confident_qwen3_8b_lora_e3" `
  --batch-size 1 `
  --torch-dtype bfloat16
```
