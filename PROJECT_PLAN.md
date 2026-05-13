# Project Plan

Last updated: 2026-05-13

This file is the working project memory for SFT-DataJudge. The README explains the project to readers; this plan tracks what has been done, what the current decision is, and what should happen next.

## Current Snapshot

We are building a binary scorer for SFT data quality:

```json
{"verdict": "keep|not_keep"}
```

Current model decision:

- **Primary candidate:** `v4_conservative`
- **Secondary companion:** `v4_confident`
- **Aggressive review reference:** `v3_conservative`

Reason:

`v4_conservative` gives the best current balance for automatic filtering. It has lower clean `not_keep` recall than `v3_conservative`, but much better `not_keep` precision and `keep` recall, which matters when the scorer is allowed to remove data from the downstream SFT pool.

## Selection Criteria

The main target is not simply "highest not_keep recall".

For automatic SFT filtering, the scorer should:

- catch clean-looking bad samples
- avoid throwing away too many good samples
- output valid JSON reliably
- remain stable when rule metadata is removed

Current operating criterion:

1. clean `not_keep` precision >= 75%
2. clean `keep` recall >= 95%
3. valid JSON rate = 100%
4. among models satisfying those constraints, prefer higher clean `not_keep` recall

## Completed Work

### Data Pipeline

Done:

- unified sample normalization
- rule-based quality flags
- teacher-labeling workflow
- binary scorer data builders
- LLaMA-Factory train/predict configs
- evaluation scripts for in-domain and evergreen tests
- cross-version evergreen reporting

### Repository Hygiene

Done on 2026-05-13:

- refreshed `scripts/README.md` through the Phase E pairwise judge scripts
- refreshed `reports/README.md` to separate current canonical reports from historical reports
- refreshed `PROJECT_FILE_INVENTORY.md` as the current GitHub handoff checklist
- updated `.gitignore` for archived generated data, dry-run eval JSONL files, and pre-replacement backups

### Scorer Versions

| Version | Summary | Status |
|---|---|---|
| v1 | first 4B/8B scorer baselines | historical baseline |
| v2 | stronger conservative/confident scorer data | comparison baseline |
| v3 | larger scorer run with conservative/confident variants | useful but too aggressive on evergreen_v2 |
| v4 | active learning plus targeted hard clean samples | current candidate family |

### V4 Data

v4 added three important sources:

| Source | Purpose |
|---|---|
| `v2active002` | active-learning continuation from model disagreement / uncertain regions |
| `v4_random_supplement` | random production-like clean samples |
| `v4_cot_zh_short_clean` | targeted hard clean `cot_zh` slice |

Approximate v4 binary datasets:

| Dataset | Total | Train | Valid | Test | Keep | Not keep |
|---|---:|---:|---:|---:|---:|---:|
| v4 conservative | 6,248 | 4,985 | 637 | 626 | 3,296 | 2,952 |
| v4 confident | 5,562 | 4,444 | 567 | 551 | 3,296 | 2,266 |

Label mapping:

- conservative: score 1-3 -> `not_keep`, score 4-5 -> `keep`
- confident: score 1-2 -> `not_keep`, score 4-5 -> `keep`, score 3 skipped

### Training

Done:

- `v4_conservative` trained
- `v4_confident` trained

Known output locations:

- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v4_conservative_qwen3_8b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v4_confident_qwen3_8b_lora_e3`

`v4_conservative` best checkpoint observed:

- checkpoint: 500
- eval loss: about 0.0509

## Evergreen V2

`evergreen_v2` is the current cross-version test set.

Composition:

- 900 total records
- 800 clean-looking records
- 100 flagged records
- sources: `cot_zh`, `finetome`, `openmath`

Purpose:

- compare model versions on the same fixed set
- stress-test clean-looking bad examples
- test whether prompt metadata such as `rule_flag` creates shortcut behavior

Important limitation:

`openmath` still has too few clean `not_keep` examples, so source-level openmath recall should not drive decisions yet.

## Evergreen V2 Results

All current evergreen_v2 predictions are complete:

- 8 models with normal prompt
- 8 models with no-flag prompt
- valid JSON rate is 100%

Reports:

- `reports/evergreen_v2_all_models_eval_report.md`
- `reports/evergreen_v2_noflag_all_models_eval_report.md`

Metrics:

- `data/eval/evergreen_v2_all_models_eval_metrics.json`
- `data/eval/evergreen_v2_noflag_all_models_eval_metrics.json`

### Normal Prompt, Conservative Ground Truth

| Model | Clean acc | Clean not_keep recall | Clean not_keep precision | Clean keep recall | Flagged not_keep recall |
|---|---:|---:|---:|---:|---:|
| `v1_4B_confident` | 72.38 | 43.09 | 56.68 | 85.38 | 42.86 |
| `v3_conservative` | 76.25 | 41.87 | 68.67 | 91.52 | 50.00 |
| `v4_conservative` | 77.75 | 36.18 | 80.91 | 96.21 | 32.14 |
| `v4_confident` | 76.50 | 28.46 | 85.37 | 97.83 | 32.14 |
| `v2_conservative` | 75.00 | 28.05 | 75.00 | 95.85 | 21.43 |
| `v1_8B_confident` | 74.12 | 26.42 | 71.43 | 95.31 | 39.29 |
| `v3_confident` | 74.62 | 25.20 | 76.54 | 96.57 | 17.86 |
| `v2_confident` | 74.25 | 23.17 | 77.03 | 96.93 | 17.86 |

### No-Flag Prompt, Conservative Ground Truth

| Model | Clean acc | Clean not_keep recall | Clean not_keep precision | Clean keep recall | Flagged not_keep recall |
|---|---:|---:|---:|---:|---:|
| `v1_4B_confident_noflag` | 72.50 | 47.56 | 56.25 | 83.57 | 46.43 |
| `v3_conservative_noflag` | 76.00 | 44.31 | 66.46 | 90.07 | 50.00 |
| `v4_conservative_noflag` | 77.75 | 36.18 | 80.91 | 96.21 | 39.29 |
| `v2_conservative_noflag` | 75.25 | 31.71 | 72.22 | 94.58 | 28.57 |
| `v1_8B_confident_noflag` | 74.50 | 28.86 | 71.00 | 94.77 | 35.71 |
| `v4_confident_noflag` | 76.50 | 28.86 | 84.52 | 97.65 | 32.14 |
| `v3_confident_noflag` | 74.75 | 26.42 | 75.58 | 96.21 | 28.57 |
| `v2_confident_noflag` | 74.25 | 23.98 | 75.64 | 96.57 | 21.43 |

## Current Interpretation

### V4 Conservative

Use as the current main auto-filter candidate.

Strengths:

- clean `not_keep` precision is high enough for automatic filtering
- clean `keep` recall is above 95%
- no-flag result is stable, so the model is not obviously relying on `rule_flag`
- improves over v2 conservative on clean `not_keep` recall

Weakness:

- still misses many clean-looking bad samples
- flagged-slice recall is not the best

### V4 Confident

Use as a stricter companion model.

Strengths:

- higher `not_keep` precision
- very high `keep` recall

Weakness:

- lower clean `not_keep` recall

Possible use:

- high-confidence rejection
- agreement/intersection logic with v4 conservative
- manual review prioritization

### V3 Conservative

Keep as an aggressive review reference, not the main auto-filter.

Strength:

- high clean `not_keep` recall

Weakness:

- lower precision and lower keep recall mean it throws away more good data

## Remaining Tests

No more evergreen_v2 prediction tests are required right now. The normal and no-flag runs are complete for all current models.

Still useful for a clean v4 release record:

```powershell
& $LF train configs/llamafactory/scorer_binary_v4_conservative_qwen3_8b_lora_predict_valid.yaml
& $LF train configs/llamafactory/scorer_binary_v4_conservative_qwen3_8b_lora_predict_test.yaml
& $LF train configs/llamafactory/scorer_binary_v4_confident_qwen3_8b_lora_predict_valid.yaml
& $LF train configs/llamafactory/scorer_binary_v4_confident_qwen3_8b_lora_predict_test.yaml
```

Also still useful:

- finish human audit in `data/eval/evergreen_human_verify/annotation.md`
- estimate teacher-label noise floor
- expand evergreen openmath bad-sample support

## Next Phase

### Phase E: Downstream SFT Validation

The scorer is only useful if it improves downstream SFT quality. Next step is to score a larger SFT pool and train/evaluate downstream SFT models under several filtering policies.

Current Phase E status:

- built exclusion-safe clean candidate pool: `data/splits/phase_e/phase_e_clean_candidate_15k.jsonl`
- completed v4 scoring on the same 15k pool:
  - `data/scored/phase_e_v4_conservative_clean_15k.jsonl`
  - `data/scored/phase_e_v4_confident_clean_15k.jsonl`
- built downstream SFT datasets in `data/labeled/phase_e_sft/`
- generated Phase E dataset report: `reports/phase_e_downstream_dataset_report.md`
- prepared five Qwen3-8B LoRA e1 training configs under `configs/llamafactory/`
- built small held-out downstream eval set:
  - samples: `data/eval/phase_e_downstream_eval/sample.jsonl`
  - LLaMA-Factory dataset: `data/labeled/phase_e_downstream_eval_lf/`
  - report: `reports/phase_e_downstream_eval_sampling_report.md`
- completed five Phase E downstream Qwen3-8B LoRA e1 training runs:
  - `phase_e_unfiltered_clean_15k`
  - `phase_e_v4_conservative_keep_clean_15k`
  - `phase_e_v4_confident_keep_clean_15k`
  - `phase_e_v4_both_keep_clean_15k`
  - `phase_e_v4_persource_keep_clean_15k`
- completed five Phase E eval generations on the fixed 200-prompt set
- generated Phase E prediction comparison artifacts:
  - script: `scripts/30_compare_phase_e_downstream_predictions.py`
  - report: `reports/phase_e_downstream_prediction_comparison_report.md`
  - metrics: `data/eval/phase_e_downstream_eval/phase_e_downstream_prediction_comparison_metrics.json`
  - side-by-side predictions: `data/eval/phase_e_downstream_eval/phase_e_downstream_prediction_comparison.jsonl`
  - review queue: `data/eval/phase_e_downstream_eval/phase_e_downstream_review_queue.jsonl`
- prepared five-model teacher pairwise judging:
  - dry-run output: `data/eval/phase_e_downstream_eval/phase_e_downstream_pairwise_labels_5model_dryrun.jsonl`
  - formal output target: `data/eval/phase_e_downstream_eval/phase_e_downstream_pairwise_labels_5model.jsonl`
  - status: waiting for `TEACHER_API_KEY` or `OPENAI_API_KEY`

Current automatic Phase E readout:

| Model | BLEU-4 | ROUGE-L | Token F1 | Len ratio | Repetition flags | Truncation flags |
|---|---:|---:|---:|---:|---:|---:|
| `unfiltered` | 48.06 | 48.61 | 0.629 | 1.20 | 29 | 1 |
| `v4_conservative_keep` | 47.26 | 48.15 | 0.618 | 1.26 | 29 | 2 |
| `v4_confident_keep` | 47.56 | 48.57 | 0.625 | 1.06 | 27 | 0 |
| `v4_both_keep` | 46.65 | 47.77 | 0.619 | 1.07 | 22 | 1 |
| `v4_persource_keep` | 46.39 | 47.55 | 0.616 | 1.23 | 28 | 2 |

Openmath `\boxed{}` exact-match readout:

| Model | Correct | Total | Accuracy |
|---|---:|---:|---:|
| `v4_both_keep` | **23** | 40 | **0.575** |
| `unfiltered` | 22 | 40 | 0.550 |
| `v4_persource_keep` | 20 | 40 | 0.500 |
| `v4_conservative_keep` | 19 | 40 | 0.475 |
| `v4_confident_keep` | 18 | 40 | 0.450 |

Interpretation:

- These are reference-overlap and surface-quality proxy metrics, not final quality judgments.
- The filtered downstream models do not show an obvious aggregate proxy-metric improvement over the unfiltered baseline on the current 200-prompt eval set.
- `v4_confident_keep` is closest to unfiltered by aggregate overlap and has fewer truncation issues.
- `v4_persource_keep` does not improve the proxy metrics and does not beat `v4_both_keep` on openmath exact-answer accuracy.
- `v4_both_keep` remains the current default unless the pending five-model teacher pairwise judge overturns the objective openmath signal.

Completed teacher pairwise judge over the 200-prompt eval set (DeepSeek-v4-pro, all four models judged together per prompt with randomized A/B/C/D order):

- prompt template: `prompts/teacher_judge_pairwise_prompt.md`
- runner: `scripts/31_teacher_judge_pairwise.py` (concurrent, with resume support)
- aggregator: `scripts/32_aggregate_pairwise_results.py` (also runs an objective `\boxed{}` answer match for the 40 openmath prompts)
- labels: `data/eval/phase_e_downstream_eval/phase_e_downstream_pairwise_labels.jsonl`
- metrics: `data/eval/phase_e_downstream_eval/phase_e_downstream_pairwise_metrics.json`
- report: `reports/phase_e_downstream_pairwise_report.md`

Pairwise readout (200 valid labels):

| Model | Avg rank ↓ | Correct rate | Win rate vs `unfiltered` | Math `\boxed{}` accuracy |
|---|---:|---:|---:|---:|
| `v4_both_keep` | **2.39** | **0.680** | 0.520 | **0.575 (23/40)** |
| `v4_conservative_keep` | 2.510 | 0.595 | 0.515 | 0.475 (19/40) |
| `v4_confident_keep` | 2.535 | 0.575 | 0.530 | 0.450 (18/40) |
| `unfiltered` | 2.565 | 0.600 | — | 0.550 (22/40) |

Conclusion: the BLEU/ROUGE proxy ranking is overturned. `v4_both_keep` wins on pairwise ranking and on the only objective signal (math `\boxed{}` match). All three filtered policies beat `unfiltered` head-to-head (51-53% win rate). Per-source breakdown: `v4_both_keep` is best on `finetome` and `openmath_reasoning`, but `v4_conservative_keep` is best on `cot_zh`; this motivated the per-source follow-up experiment.

Per-source follow-up (2026-05-13):

- policy: `cot_zh` uses `v4_conservative_keep`; `finetome` and `openmath_reasoning` use `v4_both_keep`
- dataset: `phase_e_v4_persource_keep_clean_15k` with 10,272 records
- training: completed one Qwen3-8B LoRA e1 epoch; final train loss about 0.486
- prediction: completed all 200 held-out eval prompts
- proxy comparison: no improvement over `v4_both_keep`
- openmath exact match: 20/40, below `v4_both_keep` at 23/40
- teacher pairwise: five-model prompt and scripts are ready; formal run is blocked until a teacher API key is available

Prepared downstream training datasets:

| Dataset | Records | Purpose |
|---|---:|---|
| `phase_e_unfiltered_clean_15k` | 15,000 | clean-pool baseline |
| `phase_e_v4_conservative_keep_clean_15k` | 10,301 | main scorer-filtered set |
| `phase_e_v4_confident_keep_clean_15k` | 11,111 | stricter companion-filtered set |
| `phase_e_v4_both_keep_clean_15k` | 10,206 | safest two-model keep intersection |
| `phase_e_v4_persource_keep_clean_15k` | 10,272 | source-aware follow-up policy |

V4 scorer agreement on the 15k pool:

| Bucket | Records |
|---|---:|
| both keep | 10,206 |
| conservative keep / confident not_keep | 95 |
| conservative not_keep / confident keep | 905 |
| both not_keep | 3,794 |

Prepared downstream eval set:

| Source | Records |
|---|---:|
| finetome | 80 |
| cot_zh | 80 |
| openmath_reasoning | 40 |
| **Total** | **200** |

Candidate groups:

| Group | Purpose |
|---|---|
| unfiltered | baseline |
| rule-clean only | rule baseline; omitted for the current 15k clean-pool run because it is identical to unfiltered |
| v4 conservative keep | main scorer-filtered set |
| v4 confident keep | stricter scorer-filtered set |
| v4 per-source keep | `cot_zh` conservative keep plus both-keep for English/math |
| v4 conservative keep plus manual/top-confidence review | quality-prioritized variant |
| intersection or agreement of v4 conservative/confident | safest high-precision variant |

Decision target:

- downstream model improves or at least does not regress
- data volume remains large enough
- filtered data has visibly fewer corrupted, wrong, irrelevant, or incomplete samples

### Phase F: Better Calibration

Current scorer output is binary JSON. For ranking and top-K filtering, it would be useful to produce or recover confidence.

Options:

- train JSON output with `decision` and `confidence`
- extract first-token softmax probabilities for `keep` vs `not_keep`
- calibrate scores against evergreen and human-audited subsets

## Open Questions

1. How much clean `not_keep` recall is enough before downstream SFT gains appear?
2. What is the real teacher-label noise floor on evergreen_v2?
3. Does v4 conservative improve downstream SFT quality more than a rule-clean baseline?
4. Is v4 confident useful as a high-precision reject model, or does it miss too much?
5. Should the next evergreen version include an OOD source such as alpaca, wizardlm, or ultrachat?

## Decision Log

- Do not select a model only by lowest eval loss.
- Do not select a model only by highest `not_keep` recall.
- Use clean `not_keep` recall as the main sensitivity metric, but constrain it with precision and keep recall.
- Treat flagged metrics as secondary because flagged samples are already easier to catch with rules.
- Treat evergreen_v2 as the main cross-version benchmark for now.
- Treat downstream SFT validation as the final go/no-go test.
