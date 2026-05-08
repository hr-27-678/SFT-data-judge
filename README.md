# SFT-DataJudge

Last updated: 2026-05-08

SFT-DataJudge is a project for building a small, local binary scorer that filters supervised fine-tuning samples before they enter an SFT training run.

The scorer reads an instruction-output pair and predicts:

```json
{"verdict": "keep"}
```

or:

```json
{"verdict": "not_keep"}
```

The practical goal is not to classify every questionable sample perfectly. The goal is to remove clearly bad SFT data while preserving enough high-quality and diverse data for downstream model training.

## Why This Exists

SFT datasets often contain a mix of useful examples, malformed examples, wrong answers, incomplete outputs, irrelevant responses, and low-value reasoning traces. Rule-based filters can catch obvious corruption, but many quality problems require semantic judgment.

This project builds a learned quality filter using teacher-labeled data and tests whether the filter can generalize beyond the exact training distribution.

## What We Built

- A unified SFT sample schema for multiple sources.
- Rule-based prefilter signals such as `rule_clean` and `rule_flags`.
- Teacher-labeling scripts that turn raw samples into 1-5 quality scores.
- Binary scorer datasets under two label mappings:
  - **conservative**: score 1-3 -> `not_keep`, score 4-5 -> `keep`
  - **confident**: score 1-2 -> `not_keep`, score 4-5 -> `keep`, score 3 skipped
- LoRA fine-tuning configs for Qwen3-8B using LLaMA-Factory.
- Versioned scorer datasets from v1 to v4.
- An `evergreen_v2` evaluation set for cross-version comparison.
- Prompt ablation tests that remove `rule_clean` / `rule_flag` fields to check whether models rely on shortcut features.

## Current Result

The current production candidate is:

**`v4_conservative`**

It is not the model with the absolute highest `not_keep` recall. It is the best current balance for automatic filtering because it catches a meaningful share of bad clean-looking samples while keeping false rejects under better control.

Primary selection rule:

> Maximize clean `not_keep` recall, subject to clean `not_keep` precision >= 75%, clean `keep` recall >= 95%, valid JSON rate = 100%, and no obvious prompt shortcut dependence.

On `evergreen_v2` with the normal prompt and conservative ground truth:

| Model | Clean acc | Clean not_keep recall | Clean not_keep precision | Clean keep recall | Role |
|---|---:|---:|---:|---:|---|
| `v1_4B_confident` | 72.38 | 43.09 | 56.68 | 85.38 | high-recall but too many false rejects |
| `v3_conservative` | 76.25 | 41.87 | 68.67 | 91.52 | aggressive review model |
| `v4_conservative` | 77.75 | 36.18 | 80.91 | 96.21 | current auto-filter candidate |
| `v4_confident` | 76.50 | 28.46 | 85.37 | 97.83 | stricter companion model |

The key tradeoff is visible here:

- `v3_conservative` catches more bad clean samples, but rejects too many good ones.
- `v4_conservative` catches fewer bad clean samples, but has much better precision and keep recall.
- `v4_confident` is even safer against false rejects, but misses more bad samples.

## Prompt Shortcut Check

The no-flag prompt removes `rule_clean` and `rule_flags` from the input. This checks whether the model is actually judging sample content instead of relying on rule metadata.

On `evergreen_v2` with conservative ground truth:

| Model | Prompt | Clean not_keep recall | Clean not_keep precision | Clean keep recall |
|---|---|---:|---:|---:|
| `v4_conservative` | normal | 36.18 | 80.91 | 96.21 |
| `v4_conservative` | no-flag | 36.18 | 80.91 | 96.21 |
| `v4_confident` | normal | 28.46 | 85.37 | 97.83 |
| `v4_confident` | no-flag | 28.86 | 84.52 | 97.65 |

This suggests the v4 models are not mainly depending on the rule fields for clean-sample decisions.

## Evergreen V2 Evaluation

`evergreen_v2` is the current cross-version test set. It has 900 records:

- 800 clean-looking samples
- 100 flagged samples
- sources: `cot_zh`, `finetome`, `openmath`

Its main purpose is to test whether the scorer can identify bad examples that pass shallow rule checks. This matters because the final SFT pool is expected to contain many clean-looking but still low-quality samples.

Important caveat:

`openmath` still has too few true `not_keep` examples in evergreen_v2, so source-level openmath recall is not stable yet. The most reliable current comparison is the aggregate clean slice, especially `cot_zh` and `finetome`.

## Model Versions

| Version | Purpose | Status |
|---|---|---|
| v1 | first scorer baselines | kept as historical baseline |
| v2 | stronger binary scorer dataset | kept as comparison baseline |
| v3 | conservative/confident split and larger evaluation | revealed overfitting to in-domain test |
| v4 | active learning plus targeted hard clean samples | current best candidate family |

v4 training data combined:

- `v2active002`: active-learning batch
- `v4_random_supplement`: random production-like clean samples
- `v4_cot_zh_short_clean`: targeted hard clean `cot_zh` samples

## Main Lesson

The early in-domain test results overstated progress. On a harder evergreen set, v3 looked much weaker on clean `not_keep` recall than expected.

The biggest improvement in v4 is not a lower training loss by itself. The important improvement is a better operational tradeoff:

- more useful detection of clean-looking bad samples than v2
- much better precision and keep recall than the overly aggressive models
- stable behavior when rule metadata is removed

## Repository Layout

| Path | Contents |
|---|---|
| `data/raw/` | source data and imported pools |
| `data/processed/` | normalized intermediate data |
| `data/labeled/` | teacher-labeled scorer datasets |
| `data/eval/` | evergreen sets, metrics, and human-audit samples |
| `configs/llamafactory/` | train and predict configs |
| `scripts/` | data building, labeling, evaluation, and reporting scripts |
| `reports/` | experiment reports and analysis notes |

## Important Reports

- `reports/evergreen_v2_all_models_eval_report.md`
- `reports/evergreen_v2_noflag_all_models_eval_report.md`
- `reports/training_lessons_and_notes.md`
- `reports/teacher_candidates_all_v2_model_agreement_report.md`

## Next Work

1. Finish standard v4 valid/test prediction reports for the v4 release record.
2. Complete a small human audit of evergreen labels to estimate the teacher-label noise floor.
3. Use `v4_conservative` to score the larger SFT pool.
4. Build downstream SFT validation groups:
   - unfiltered baseline
   - rule-clean baseline
   - scorer-kept data
   - stricter high-confidence kept data
5. Train downstream SFT models and verify whether scorer filtering improves final model quality.

