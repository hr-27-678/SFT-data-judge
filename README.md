# SFT-DataJudge

SFT-DataJudge is a data-centric pipeline for judging whether supervised fine-tuning
samples are useful training data. The project builds a small local scorer by
distilling labels from a stronger teacher model.

## Current Status

Last updated: 2026-05-09

### Headline findings

**1. In-domain test severely overstated reject ability.** On the 600-record
evergreen v1 baseline (2026-05-06), v3 conservative dropped from 77%
not-keep recall on its in-domain test to **10% not-keep recall on clean
records**. Four of six existing scorers collapsed to predicting `keep`
for every clean sample.

**2. The "rule_clean shortcut" hypothesis was tested and rejected.** A
no-flag-prompt ablation (2026-05-07) ran the same 6 adapters on a
prompt-stripped variant of evergreen. If the adapters truly relied on
rule_clean, recall should have crashed; instead it moved within ±5pp
and slightly *up* in 4 of 6 cases. The actual root cause is **training-
data composition**: the active-learning loop produced very few
"clean + drop" examples, so models never learned that class exists.
Removing rule_flag from the prompt cannot fix what training never
contained.

**3. The v4 intervention is data-driven.** v4 adds three new batches:
v2active002 (2,361, active learning), v4_random_supplement (999, random
clean from production distribution), v4_cot_zh_short_clean (300,
worst sub-slice). The v4 conservative training set has keep:not_keep =
1.12:1 (vs v3's ~1.7:1) and ~2,950 not_keep records (vs v3's ~1,150).

**4. Evergreen v2 (2026-05-08).** The 600-record evergreen v1 was
extended with 300 fresh cot_zh + finetome clean records, raising
per-source not_keep support to cot_zh 184, finetome 53, openmath 9.
Cross-version evaluation against v2 is the new standard.

**5. v4 conservative validated on evergreen v2 (2026-05-09).** Clean
not_keep recall jumped from v3's 10.08% to **36.18%** (3.6x), with
clean cot_zh from 12.79% to **38.59%** (3x). Precision on clean
rejects rose from ~0.60 to **0.81** — v4's reject decisions are
production-quality. Production-weighted recall: **v3 ~12% -> v4
~36%**, a 3x improvement on representative data. v4 lands in the
lower half of the "expected target" tier (35-55%) defined ahead of
training, validating the data-composition intervention.

### Current best candidate

The Qwen3-8B **v4 conservative** scorer (LoRA, 3 epochs, LLaMA-Factory,
trained on v4 binary scorer dataset) is the current production
candidate as of 2026-05-09. The v3 scorers remain documented as the
prior generation for cross-version comparison.

v4 conservative metrics on evergreen v2 (the cross-version standard
test set):

| Stratum / source | N | Accuracy | Not-keep precision | Not-keep recall |
| --- | ---: | ---: | ---: | ---: |
| Clean (Conservative GT) | 800 | 77.75% | **0.81** | **36.18%** |
| Clean (Confident GT) | 736 | 83.15% | 0.79 | 43.41% |
| Flagged (Conservative GT) | 100 | 80.00% | **0.90** | 32.14% |
| Flagged (Confident GT) | 92 | 86.96% | 0.75 | 45.00% |
| Clean cot_zh (Conservative GT) | 500 | 74.40% | 0.83 | **38.59%** |
| Clean finetome (Conservative GT) | 225 | 81.78% | 0.78 | 33.96% |
| Clean openmath (Conservative GT) | 75 | 88.00% | n/a | 0.00% (only 9 negs, unevaluable) |

No-flag prompt produces nearly identical numbers (within 1pp on every
metric), reconfirming that data composition — not the rule_flag
fields in the prompt — drove the improvement. Full report:
`reports/evergreen_v2_v4_conservative_eval_report.md`.

**Comparison vs v3 conservative on evergreen v1** (rough — different
test sizes; full apples-to-apples aggregation pending):

| Metric | v3 cons (v1, 600) | v4 cons (v2, 900) | Δ |
| --- | ---: | ---: | ---: |
| Clean not_keep recall | 10.08% | 36.18% | **3.6x** |
| Clean cot_zh recall | 12.79% | 38.59% | **3.0x** |
| Clean precision | ~0.60 | 0.81 | +21pp |
| Production-weighted recall (95/5 clean/flagged) | 12.1% | 36.0% | **3.0x** |

### Prior-generation candidate (v3)

The Qwen3-8B v3 scorers were the production candidates from 2026-05-05
to 2026-05-08; results are kept here for cross-version reference. Both
are LoRA, 3 epochs, LLaMA-Factory, on the v3 binary scorer datasets.

V3 metrics on the locked 264-record in-domain test set (legacy reference):

| Model | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | ---: | ---: | ---: | ---: | ---: |
| v3 conservative Qwen3-8B | 76.89% | 0.796 | 0.734 | 77.06% | 100% |
| v3 confident Qwen3-8B (subset 237) | 78.90% | 0.851 | 0.638 | 53.66% | 100% |

V3 metrics on the evergreen baseline (the honest cross-version comparison):

| Model | Stratum | N | Accuracy | Not-keep F1 | **Not-keep recall** |
| --- | --- | ---: | ---: | ---: | ---: |
| v3 conservative | clean | 500 | 77.00% | 0.173 | **10.08%** |
| v3 conservative | flagged | 100 | 79.00% | 0.571 | **50.00%** |
| v3 confident | clean | 500 | 76.20% | 0.000 | 0.00% |
| v3 confident | flagged | 100 | 76.00% | 0.294 | 17.86% |

(Conservative GT, score 3 -> not_keep. Full table in
`reports/evergreen_cross_version_eval_report.md`.)

Recommended use (unchanged but with the new caveat above):

- v3 conservative: review routing, hard-negative mining on rule-flagged
  records, teacher-relabeling prioritization. Do not use for blind automatic
  deletion. Inside the clean stratum, treat its `keep` verdicts with skepticism
  until v4.
- v3 confident: high-confidence keep filter; do not use as a reject model.
- Disagreements between v3 conservative and v3 confident are the highest-value
  teacher-relabeling candidates.

V3 dataset shape:

| Dataset | Records | Train | Valid | Test | Keep | Not-keep | Score 3 Policy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `scorer_binary_v3_conservative` | 2,588 | 2,057 | 267 | 264 | 1,438 | 1,150 | mapped to `not_keep` |
| `scorer_binary_v3_confident` | 2,326 | 1,855 | 234 | 237 | 1,438 | 888 | skipped |

Local adapters (not in git):

- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_confident_qwen3_8b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v4_conservative_qwen3_8b_lora_e3` (trained 2026-05-08)

### Active-learning loop status (2026-05-08)

- Both v3 scorers were run on a fresh 5,000-record unlabeled pool;
  agreement 4,352 / 5,000 (87.04%), 648 disagreements.
- `v2active002` (2,365 records, active-learning priority + 88
  calibration) — **labeled** with DeepSeek. 2,361 valid labels after
  dedup and JSON-parse failures.
- `v4_random_supplement` (1,000, random clean from 188K, production
  source ratio) — **labeled**. 999 valid labels. ~24% drop rate as
  expected.
- `v4_cot_zh_short_clean` (300, cot_zh-only short bucket) — **labeled**.
  300 valid labels. ~49% drop rate (much higher than the 24% baseline,
  confirming this sub-slice is the hardest).
- `evergreen_clean_expansion` (300, cot_zh + finetome clean fresh) —
  **labeled** and merged into evergreen v2.
- Cumulative teacher-labeled records for v4 training: 4,985 train +
  637 valid + 626 test = 6,248 (conservative variant).
- Pool report: `reports/v3_unlabeled_pool_5000_model_agreement_report.md`.

### Test set comparability — resolved with evergreen baseline

Pre-v3 metrics on each version's own in-domain test split are NOT directly
comparable, because the test populations are different and pre-v3 splits were
never locked:

| Variant | In-domain test records | Source | Locked? |
| --- | ---: | --- | --- |
| v1 4B confident | 96 | starter_1000 | no |
| v1 8B confident | 96 | starter_1000 | no |
| v2 conservative | 224 | starter + targeted | no |
| v2 confident | 199 | starter + targeted (score-3 skipped) | no |
| v3 conservative | 264 | starter + targeted + v2active001 | YES (`data/eval/locked_test_ids.json`) |
| v3 confident | 237 | locked 264 minus 27 score-3 records | inherits subset of locked |

To enable an honest cross-version comparison, a 600-record evergreen test
set was built on 2026-05-06 and locked. All 6 adapters were evaluated on
that single test set with the same LLaMA-Factory pipeline used during
training. See "Evergreen cross-version comparison" below.

### Evergreen cross-version comparison

The evergreen test set is 600 fresh records that no scorer (past or future)
will ever train on. Source: 5,000 v3 unlabeled pool minus already-labeled and
locked-test ids, plus 100 flagged records from the 188K pool with
`duplicate_pair` excluded. Lock: `data/eval/evergreen_test_ids.json`.
Stratified into 500 clean (60/25/15 cot_zh/finetome/openmath) + 100 flagged
(40/60 cot_zh/finetome).

Two ground-truth mappings: Conservative GT maps teacher score 1-2-3 to
not_keep; Confident GT skips score 3 (44 records). Predictions produced by
LLaMA-Factory `qwen3_nothink` predict, identical pipeline to training.

Conservative GT, clean stratum (500 records, true not_keep rate 23.8%):

| Model | Accuracy | Not-keep F1 | Not-keep recall |
| --- | ---: | ---: | ---: |
| v3 conservative | 77.00% | 0.173 | **10.08%** |
| v3 confident | 76.20% | 0.000 | 0.00% |
| v2 conservative | 76.20% | 0.000 | 0.00% |
| v2 confident | 76.20% | 0.000 | 0.00% |
| v1 8B confident | 76.00% | 0.000 | 0.00% |
| v1 4B confident | 72.60% | 0.259 | **20.17%** |

Conservative GT, flagged stratum (100 records, true not_keep rate 28%):

| Model | Accuracy | Not-keep F1 | Not-keep recall |
| --- | ---: | ---: | ---: |
| v3 conservative | 79.00% | 0.571 | **50.00%** |
| v3 confident | 76.00% | 0.294 | 17.86% |
| v2 conservative | 75.00% | 0.324 | 21.43% |
| v2 confident | 76.00% | 0.294 | 17.86% |
| v1 8B confident | 76.00% | 0.478 | 39.29% |
| v1 4B confident | 74.00% | 0.480 | 42.86% |

Confident GT, flagged stratum (92 records):

| Model | Accuracy | Not-keep F1 | Not-keep recall |
| --- | ---: | ---: | ---: |
| v3 conservative | 81.52% | 0.541 | **50.00%** |
| v1 4B confident | 78.26% | 0.500 | 50.00% |
| v1 8B confident | 79.35% | 0.457 | 40.00% |
| v2 conservative | 81.52% | 0.414 | 30.00% |
| v3 confident | 82.61% | 0.385 | 25.00% |
| v2 confident | 82.61% | 0.385 | 25.00% |

Full report including Confident GT clean tables and per-source breakdowns:
`reports/evergreen_cross_version_eval_report.md`.

Key takeaways:

- **In-domain test severely overstated reject ability.** v3 conservative
  77% not-keep recall on its own test collapses to 10% on evergreen clean.
  The in-domain test was drawn from the same active-learning-enriched pool
  the scorer trained on, so it inherited the boundary-case bias.
- **Scorers learned a "rule_clean=True -> keep" shortcut.** 4 of 6 scorers
  predict not_keep zero times on clean records. Only v3 conservative and
  v1 4B do any reject inside clean, both at low rates.
- **Discrimination on flagged records is acceptable.** v3 conservative
  reaches 50% not-keep recall on flagged. Rule-flag signal is the scorer's
  main discriminator.
- **v1 4B is the only baseline that meaningfully discriminates inside
  clean.** Hypothesis: smaller capacity blocked the rule-flag shortcut from
  fully forming. v3 conservative is the most balanced overall (best on
  flagged, second-best on clean).
- **openmath_reasoning is a near-zero-reject case for every scorer.** True
  not_keep rate is ~12% on clean openmath, so the cost of all-keep is small,
  but no scorer corrects any openmath sample.

### Historical results (different test sets — see caveat above)

Qwen3-4B v1 binary confident (compact baseline, test=96):

| Split | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | ---: | ---: | ---: | ---: | ---: |
| Valid | 82.11% | 0.872 | 0.702 | 71.43% | 100% |
| Test | 76.04% | 0.824 | 0.623 | 70.37% | 100% |

Qwen3-8B v1 capacity check on the same 1,000-example dataset (test=96):

| Split | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | ---: | ---: | ---: | ---: | ---: |
| Valid | 77.89% | 0.851 | 0.571 | 50.00% | 100% |
| Test | 84.38% | 0.899 | 0.651 | 51.85% | 100% |

Note: v1 8B looked stronger on accuracy, but its not_keep recall is only
51.85%, so it was too keep-biased to use as a reject filter.

Qwen3-8B v2 conservative (test=224):

| Split | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | ---: | ---: | ---: | ---: | ---: |
| Valid | 74.55% | 0.799 | 0.655 | 57.45% | 100% |
| Test | 79.91% | 0.844 | 0.717 | 64.04% | 100% |

Qwen3-8B v2 confident (test=199):

| Split | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | ---: | ---: | ---: | ---: | ---: |
| Valid | 76.14% | 0.832 | 0.591 | 50.75% | 100% |
| Test | 82.41% | 0.879 | 0.679 | 57.81% | 100% |

## Data Versions

The scorer training set grows incrementally. Each version adds a new
teacher-label batch on top of the previous version's data. Full descriptions
in `PROJECT_PLAN.md` under "Data Versions".

| Version trained | Batches added | Records | How it was built |
| --- | --- | ---: | --- |
| v1 | starter (`teacher_labels_1000`) | 1,000 | Source-stratified random sample, 80/20 clean/flagged, length-bucketed. Foundation. |
| v2 | + targeted (`targeted_1200_teacher_labels`) | 1,200 | Hand-curated targeted batch focused on v1 weak/boundary areas. |
| v3 | + `v2active001` | 388 | First active-learning batch. Model disagreements + both_not_keep + flagged_but_keep on a 3,600 pool, deduped against existing labels. |
| v4 (cons trained 2026-05-08) | + `v2active002` + `v4_random_supplement` + `v4_cot_zh_short_clean` | 2,365 + 1,000 + 300 | Second active-learning batch (priority + 88 calibration); plus random clean from production distribution to break the "clean+drop" gap; plus targeted cot_zh short bucket (the worst sub-slice on evergreen v1). |

Naming note: `v2active001` / `v2active002` are legacy prefixes from when v2
was the latest scorer; they are batch labels, not scorer versions.

Each version's binary scorer dataset is built by
`scripts/09_build_binary_scorer_sft.py` from the cumulative batches:

- v1 binary confident: starter only.
- v2 binary conservative / confident: starter + targeted.
- v3 binary conservative / confident: starter + targeted + v2active001.
- v4 binary conservative / confident: starter + targeted + v2active001 +
  v2active002 + v4_random_supplement + v4_cot_zh_short_clean.

v4 dataset shape:

| Dataset | Records | Train | Valid | Test | Keep | Not-keep | Score 3 Policy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `scorer_binary_v4_conservative` | 6,248 | 4,985 | 637 | 626 | 3,296 | 2,952 | mapped to `not_keep` |
| `scorer_binary_v4_confident` | 5,562 | 4,444 | 567 | 551 | 3,296 | 2,266 | skipped |

## Repository Layout

```text
SFT-DataJudge/
  configs/                 Dataset and run configuration files
  prompts/                 Teacher and scorer prompt templates
  reports/                 Human-readable experiment reports
  scripts/                 Pipeline scripts, ordered by stage
  data/                    Local/generated data artifacts
```

Most JSONL data and model outputs are generated artifacts and are ignored by
`.gitignore`. The reports and scripts are the main files to commit.

## Main Workflow

1. Prepare unified source data.
2. Sample teacher candidates with source-aware allocation.
3. Label candidates with the teacher model.
4. Analyze teacher labels.
5. Convert teacher labels into SFT data for a scorer model.
6. Train and evaluate the original 1-5 scorer.
7. Convert confident labels into a binary scorer dataset.
8. Train and evaluate the binary confident scorer.
9. Add targeted teacher labels for weak and boundary cases.
10. Build v2 binary scorer datasets with confident and conservative score-3
    policies.
11. Train and evaluate the Qwen3-8B v2 conservative scorer.
12. Train and evaluate the Qwen3-8B v2 confident ablation.
13. Run both Qwen3-8B v2 scorers over the 3,600-row teacher-candidate pilot.
14. Analyze the teacher-labeled priority review queue and retrain from
    teacher-confirmed hard cases.
15. Build v3 binary scorer datasets from starter + targeted + `v2active001`.
16. Train/evaluate Qwen3-8B v3 conservative and confident variants.
17. Run both v3 scorers on a 5,000-record unlabeled pool, build the
    agreement report, and produce the `v2active002` teacher batch.
18. Build the 600-record evergreen v1 baseline (locked); evaluate all 6
    historical adapters on it. Headline finding: in-domain test
    overstated reject ability; clean-stratum recall collapsed to 0-10%.
19. Run prompt-ablation evaluation (no-flag prompt) to test the
    rule_clean shortcut hypothesis. Result: rejected. Data composition,
    not prompt form, is the gap.
20. Sample and label `v4_random_supplement` (1,000 random clean from
    188K) and `v4_cot_zh_short_clean` (300 worst-slice supplement).
21. Build evergreen v2 (900 records = v1 600 + 300 fresh clean
    expansion) and 12 v2 predict configs.
22. Build v4 binary datasets and train Qwen3-8B v4 conservative
    (2026-05-08).
23. Evaluate v4 conservative on evergreen v2 (2026-05-09). Clean
    not_keep recall 36.18% (vs v3 10.08%), clean precision 0.81.
    No-flag prompt gives near-identical results, reconfirming data
    composition is the lever. v4 confident training and full
    cross-version aggregation pending.

## Key Reports

Start here:

- `PROJECT_PLAN.md` - current project plan and next steps.
- `PROJECT_FILE_INVENTORY.md` - GitHub handoff checklist.
- `reports/README.md` - report index and which reports are canonical.
- `scripts/README.md` - script index and pipeline order.

Most useful current reports:

- `reports/scorer_binary_experiment_report.md`
- `reports/scorer_binary_qwen3_8b_v1_experiment_report.md`
- `reports/scorer_binary_v2_conservative_qwen3_8b_experiment_report.md`
- `reports/scorer_binary_v2_confident_qwen3_8b_experiment_report.md`
- `reports/scorer_binary_v3_qwen3_8b_experiment_report.md`
- `reports/scorer_binary_v3_conservative_eval_valid_report.md`
- `reports/scorer_binary_v3_conservative_eval_test_report.md`
- `reports/scorer_binary_v3_confident_eval_valid_report.md`
- `reports/scorer_binary_v3_confident_eval_test_report.md`
- `reports/scorer_binary_eval_valid_report.md`
- `reports/scorer_binary_eval_test_report.md`
- `reports/scorer_binary_v2_conservative_eval_valid_report.md`
- `reports/scorer_binary_v2_conservative_eval_test_report.md`
- `reports/scorer_binary_v2_confident_eval_valid_report.md`
- `reports/scorer_binary_v2_confident_eval_test_report.md`
- `reports/teacher_candidates_all_v2_model_agreement_report.md`
- `reports/v3_unlabeled_pool_5000_model_agreement_report.md`
- `reports/teacher_sampling_v2_active_pilot_002_report.md`
- `reports/teacher_candidates_all_v2_conservative_inference_report.md`
- `reports/teacher_candidates_all_v2_confident_inference_report.md`
- `reports/teacher_candidates_all_v2_priority_teacher_analysis_report.md`
- `reports/training_lessons_and_notes.md`
- `reports/teacher_label_report_targeted_1200.md`
- `reports/teacher_label_report_v2active001.md`
- `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_conservative_report.md`
- `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_confident_report.md`
- `reports/scorer_error_analysis_greedy_report.md`
- `reports/teacher_label_report_1000.md`
- `reports/teacher_sampling_starter_1000_report.md`
- `data/labeled/scorer_binary_sft/scorer_binary_confident_1000_report.md`

## Reproduction Notes

Run scripts from the repository root.

`scripts/09_build_binary_scorer_sft.py` defaults to the v1 starter_1000 dataset.
To rebuild the current v3 datasets, pass all candidate files and all label
prefixes explicitly. Example:

```powershell
python scripts/09_build_binary_scorer_sft.py `
  --candidates `
    data/splits/teacher_judge/starter_1000/teacher_candidates_all.jsonl `
    data/splits/teacher_judge/targeted_1200/targeted_teacher_candidates_all.jsonl `
    data/splits/teacher_judge/v2_active_pilot_001/v2active001_teacher_candidates_all.jsonl `
  --labels-dir data/labeled/teacher_judge `
  --label-prefix teacher_labels_1000 `
  --label-prefix targeted_1200_teacher_labels `
  --label-prefix v2active001/v2active001_teacher_labels `
  --output-dir data/labeled/scorer_binary_sft_v3 `
  --dataset-prefix scorer_binary_v3_conservative `
  --mode all
python scripts/10_evaluate_binary_scorer_predictions.py --help
```

The locked evaluation set at `data/eval/locked_test_ids.json` is applied
automatically when present, so any sample id listed there is forced into the
test split regardless of the candidate file's original split assignment.

LLaMA-Factory WebUI startup is documented in:

```text
reports/llamafactory_startup.md
```

Do not commit API keys, raw datasets, generated JSONL label files, Hugging Face
caches, or LLaMA-Factory model outputs.
