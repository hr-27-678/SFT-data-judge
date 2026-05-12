# SFT-DataJudge

Last updated: 2026-05-11

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

The headline result is now on **downstream SFT quality**, not scorer-level classification metrics. The scorer is only useful if it improves the model trained on the data it keeps. Phase E tests that directly.

### Downstream filtering policy: `v4_both_keep` wins

Four Qwen3-8B LoRA models were trained on the same 15k clean candidate pool, filtered under four different policies, then evaluated on a fixed 200-prompt held-out set spanning `finetome`, `cot_zh`, and `openmath_reasoning`.

The 200 prediction sets were judged in two independent ways:

1. **Teacher pairwise ranking** (DeepSeek-v4-pro). For each prompt, all four model outputs are anonymized as A/B/C/D in a per-prompt randomized order and ranked together. Position bias is removed by hashing the prompt id to seed the shuffle.
2. **Math `\boxed{}` exact match** on the 40 `openmath_reasoning` prompts. Fully objective, does not depend on teacher judgment.

| Model | Avg rank ↓ | Teacher correct rate ↑ | Math `\boxed{}` accuracy ↑ | Win rate vs `unfiltered` |
|---|---:|---:|---:|---:|
| **`v4_both_keep`** | **2.39** | **0.680** | **0.575** | 0.520 |
| `v4_conservative_keep` | 2.510 | 0.595 | 0.475 | 0.515 |
| `v4_confident_keep` | 2.535 | 0.575 | 0.450 | 0.530 |
| `unfiltered` | 2.565 | 0.600 | 0.550 | — |

Two independent signals point the same way: `v4_both_keep` is the best downstream policy. It has the lowest average rank, the highest teacher-judged correctness rate, and the highest math exact-answer accuracy. `unfiltered` is fourth on the pairwise metric and second on math accuracy. All three filtered policies beat `unfiltered` head-to-head (51-53% win rate).

### Why the earlier proxy-metric report disagreed

An earlier BLEU/ROUGE/Token-F1 comparison showed `unfiltered` as the strongest model. That was an artifact of how those metrics work, not real quality:

- Reference answers in the eval set are drawn from the unfiltered training distribution. `unfiltered` learned to mimic their surface phrasing, which inflates reference-overlap scores even when the answer is wrong.
- `v4_both_keep` produces shorter, more direct answers (length ratio 1.07 vs `unfiltered`'s 1.20), which depresses ROUGE recall while improving actual answer quality.
- On the 40 math prompts where correctness can be checked objectively, the BLEU/ROUGE ranking is flipped: `v4_both_keep` is most correct, `unfiltered` is third, and the two single-policy filtered models trail.

Lesson: do not select a downstream filtering policy by automatic surface-overlap metrics on this kind of held-out eval. Use a stronger judge or task-specific objective correctness when available.

### Per-source detail

Average rank by source (lower is better, 1.0 = always first):

| Source | N | `unfiltered` | `v4_conservative_keep` | `v4_confident_keep` | `v4_both_keep` |
|---|---:|---:|---:|---:|---:|
| finetome (general English) | 80 | 2.65 | 2.575 | 2.562 | **2.212** |
| cot_zh (Chinese reasoning) | 80 | 2.538 | **2.388** | 2.475 | 2.60 |
| openmath_reasoning | 40 | 2.45 | 2.625 | 2.60 | **2.325** |

`v4_both_keep` dominates English and math but is weakest on Chinese reasoning. The likely cause is that requiring both scorers to agree on `keep` filters Chinese samples most aggressively, so the downstream model sees less Chinese training data. A follow-up experiment with a per-source filtering policy (use `v4_both_keep` for English/math, `v4_conservative_keep` for `cot_zh`) is the natural next step.

### Scorer-level metrics (still relevant for understanding the filter)

The scorer family that produced these downstream gains is `v4`, evaluated on the `evergreen_v2` cross-version test set. The two intersection signals used by `v4_both_keep` come from these two single-policy scorers:

| Model | Clean acc | Clean not_keep recall | Clean not_keep precision | Clean keep recall | Role |
|---|---:|---:|---:|---:|---|
| `v1_4B_confident` | 72.38 | 43.09 | 56.68 | 85.38 | early high-recall baseline |
| `v3_conservative` | 76.25 | 41.87 | 68.67 | 91.52 | aggressive review model |
| `v4_conservative` | 77.75 | 36.18 | 80.91 | 96.21 | precision-leaning filter |
| `v4_confident` | 76.50 | 28.46 | 85.37 | 97.83 | stricter companion filter |

Scorer selection rule (used inside Phase E to construct the four downstream training sets):

> Maximize clean `not_keep` recall, subject to clean `not_keep` precision >= 75%, clean `keep` recall >= 95%, valid JSON rate = 100%, and no obvious prompt shortcut dependence.

Single-scorer use favors `v4_conservative` (better precision/recall balance than `v3_conservative`). Intersection use (`v4_both_keep`) is what currently produces the best downstream model.

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

Three overlapping lessons from this project:

1. **In-domain test scores overstated progress.** v3 looked much stronger than v4 on in-domain tests but much weaker on `evergreen_v2`'s clean `not_keep` slice. v4's real value is a better operational tradeoff: useful detection of clean-looking bad samples, stable behavior when rule metadata is removed, and far better keep recall than the overly aggressive v3.
2. **Surface-overlap metrics mislead downstream eval.** BLEU/ROUGE/Token-F1 on the 200-prompt downstream eval ranked `unfiltered` first; teacher pairwise ranking and math exact-answer accuracy ranked `v4_both_keep` first. The proxy metrics rewarded the model that learned to mimic reference phrasing, not the model that produced correct answers.
3. **Two-scorer intersection beats either scorer alone, at the downstream level.** Neither `v4_conservative` nor `v4_confident` alone produces the best downstream model. Requiring both to agree on `keep` does, and it does so on the metrics that actually reflect answer quality.

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

- `reports/phase_e_downstream_pairwise_report.md` — teacher pairwise judge over the 4 downstream models, plus math accuracy
- `reports/phase_e_downstream_prediction_comparison_report.md` — earlier BLEU/ROUGE/Token-F1 comparison (kept as a cautionary example)
- `reports/phase_e_downstream_dataset_report.md` — how the four 15k filtered training sets were built
- `reports/evergreen_v2_all_models_eval_report.md` — scorer-level metrics with the normal prompt
- `reports/evergreen_v2_noflag_all_models_eval_report.md` — scorer-level metrics with `rule_*` fields removed
- `reports/training_lessons_and_notes.md`
- `reports/teacher_candidates_all_v2_model_agreement_report.md`

## Next Work

1. Per-source filtering policy: use `v4_both_keep` for English and math, `v4_conservative_keep` for `cot_zh`. Train one more downstream model and re-run pairwise judge to confirm.
2. Scale up: apply the winning policy to a larger SFT pool and verify that the downstream gain persists past 15k records.
3. Small human audit of evergreen labels to estimate the teacher-label noise floor (still outstanding from before Phase E).
4. Confidence calibration on the scorer (Phase F): probabilistic output instead of binary, to enable top-K filtering.

