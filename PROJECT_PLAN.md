# Project Plan

Last updated: 2026-05-06

## Resume Here

This is the first file a future Codex session should read.

Current repository:

- Local path: `\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge`
- GitHub: `https://github.com/hr-27-678/SFT-data-judge.git`
- Branch: `main`
- Initial pushed commit: `7b701c6 Initial project cleanup and scorer reports`

Recommended reading order for a fresh session:

1. `PROJECT_PLAN.md`
2. `PROJECT_FILE_INVENTORY.md`
3. `reports/README.md`
4. `scripts/README.md`
5. `reports/scorer_binary_experiment_report.md`
6. `reports/scorer_binary_v2_conservative_qwen3_8b_experiment_report.md`
7. `reports/scorer_binary_v2_confident_qwen3_8b_experiment_report.md`
8. `reports/teacher_candidates_all_v2_model_agreement_report.md`
9. `reports/training_lessons_and_notes.md`
10. `reports/scorer_binary_v3_qwen3_8b_experiment_report.md`
11. `reports/scorer_binary_v3_conservative_eval_test_report.md`
12. `reports/scorer_binary_v3_confident_eval_test_report.md`
13. `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_conservative_report.md`
14. `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_confident_report.md`
15. `reports/teacher_candidates_all_v2_priority_teacher_analysis_report.md`
16. `reports/teacher_sampling_v2_active_pilot_001_report.md`
17. `reports/teacher_sampling_targeted_1200_report.md`
18. `reports/v3_unlabeled_pool_5000_model_agreement_report.md`
19. `reports/teacher_sampling_v2_active_pilot_002_report.md`

The school computer does not preserve conversation progress, so this file should
be treated as the project memory.

## Current State Snapshot

The project has completed one full starter loop:

1. sampled 1,000 teacher-label candidates
2. labeled them with the teacher model
3. built original 1-5 scorer SFT data
4. trained a Qwen3-4B LoRA scorer
5. evaluated valid/test behavior
6. found that the 1-5 score task was too fuzzy around score 3 / `maybe`
7. rebuilt a binary confident dataset
8. trained and evaluated the binary confident scorer
9. organized project files and pushed the current repo to GitHub
10. trained and evaluated a Qwen3-8B v1 capacity-check scorer on the same
    binary confident dataset
11. labeled the targeted 1,200-example teacher batch
12. merged starter + targeted labels into v2 binary scorer datasets
13. trained and evaluated the Qwen3-8B v2 conservative scorer
14. standardized all markdown reports under `reports/` with consistent
    metadata/context headers and common section names
15. implemented `scripts/12_infer_binary_scorer.py` for batch scorer inference
    on unlabeled JSONL pools with resume support and summary reporting
16. trained and evaluated the Qwen3-8B v2 confident ablation
17. ran both Qwen3-8B v2 scorers on the 3,600-row teacher-candidate pool and
    built a conservative/confident agreement report plus a teacher-review
    priority queue
18. implemented `scripts/13_build_teacher_review_batch.py` and built the first
    deduplicated active-learning teacher batch, `v2active001`
19. analyzed `v2active001` labels and joined all available teacher labels back
    to the 1,215-record priority queue with
    `scripts/14_analyze_teacher_review_priority.py`
20. built v3 binary scorer datasets from starter + targeted + `v2active001`
    teacher labels
21. prepared Qwen3-8B v3 conservative/confident LLaMA-Factory training configs
    and matching greedy valid/test prediction configs
22. trained and evaluated both Qwen3-8B v3 scorer variants
23. ran both v3 scorers over a fresh 5,000-record unlabeled pool (excluded
    already-teacher-labeled ids at sampling time, zero overlap with locked
    test) and produced an agreement / priority queue report
24. built the next active-learning teacher batch `v2active002` (2,365 records:
    2,277 priority + 88 random calibration from `conf_keep__cons_keep`) and
    started DeepSeek labeling on 2026-05-06
25. built the 600-record evergreen baseline test set (500 clean + 100 flagged,
    `duplicate_pair` excluded), labeled with DeepSeek, locked at
    `data/eval/evergreen_test_ids.json`
26. evaluated all six existing scorer adapters (v1 4B, v1 8B, v2 conservative,
    v2 confident, v3 conservative, v3 confident) on the evergreen baseline
    using LLaMA-Factory `qwen3_nothink` predict (the same pipeline used during
    training); report at `reports/evergreen_cross_version_eval_report.md`

The current best direction is the binary scorer family, not the original 1-5
scorer.

On 2026-05-02, the targeted teacher-labeling batch was completed with DeepSeek.
Four initial API/parse failures were retried, then merged into the canonical
`data/labeled/teacher_judge/targeted_1200_teacher_labels.jsonl`, giving
1,200/1,200 valid teacher labels.

On 2026-05-03, the Qwen3-8B v2 confident ablation was restarted from scratch
with `overwrite_output_dir: true`, trained successfully, and evaluated on
valid/test with greedy decoding. Treat the current local adapter as complete.

On 2026-05-03, both Qwen3-8B v2 scorers were run on
`data/splits/teacher_judge/teacher_candidates_all.jsonl` (3,600 records).
They agreed on 3,327 / 3,600 records (92.42%) and disagreed on 273 records.
The strongest teacher-labeling queue is the 273 disagreements plus the 646
both-not-keep records, before expanding to the full 188,103-row processed pool.

On 2026-05-04, the 1,215-record pilot priority queue was deduplicated against
existing teacher labels using the original sample `id` only. Do not deduplicate
across batches by `teacher_sample_id`; those ids can be reused by different
sampling runs. The result:

- 827 priority records already have teacher labels from the starter/targeted
  batches.
- 388 priority records were unlabeled at selection time and were written as
  batch `v2active001`.
- Dry-run teacher prompts were rendered to
  `data/labeled/teacher_judge/v2active001/v2active001_teacher_prompts.jsonl`.

After teacher labeling and retry, `v2active001` has 388 deduplicated valid
labels. The raw output file has 390 rows because the two failed rows were
retried with `--resume` and appended; downstream analysis keeps the last record
per original sample `id`. The 1,215-record priority queue now has 1,215 valid
teacher labels joined from starter, targeted, and `v2active001`; the current
analysis report is
`reports/teacher_candidates_all_v2_priority_teacher_analysis_report.md`.

On 2026-05-04, v3 binary scorer datasets were generated in
`data/labeled/scorer_binary_sft_v3/` from the starter, targeted, and
`v2active001` teacher labels:

- `scorer_binary_v3_conservative`: 2,588 total records, with score 3 mapped to
  `not_keep` (train 2,057 / valid 267 / test 264).
- `scorer_binary_v3_confident`: 2,326 total records, with score 3 skipped
  (train 1,855 / valid 234 / test 237).
- Both variants use the same binary prompt/schema as v2 and have
  `dataset_info.json` entries ready for LLaMA-Factory.

On 2026-05-05, both v3 Qwen3-8B LoRA variants were trained and evaluated with
greedy valid/test prediction:

- v3 conservative best checkpoint: `checkpoint-250`, best valid eval loss
  `0.05724373087286949`.
- v3 confident best checkpoint: `checkpoint-100`, best valid eval loss
  `0.053558845072984695`.
- v3 conservative test: accuracy 76.89%, keep F1 0.796, not_keep F1 0.734,
  not_keep recall 77.06%.
- v3 confident test: accuracy 78.90%, keep F1 0.851, not_keep F1 0.638,
  not_keep recall 53.66%.
- Current report:
  `reports/scorer_binary_v3_qwen3_8b_experiment_report.md`.

On 2026-05-06, both v3 scorers were run on a fresh 5,000-record unlabeled pool
at `data/splits/teacher_judge/v3_unlabeled_pool_5000/teacher_candidates_all.jsonl`.
The pool was sampled with `--exclude-label-files` covering all prior teacher
labels (~2,588 ids) and verified to have zero overlap with the 264-id
`data/eval/locked_test_ids.json`. Result: 4,352 / 5,000 (87.04%) agreement,
648 disagreements. The agreement analysis script
`scripts/15_analyze_v3_pool_agreement.py` produced the priority queue
`data/scored/v3_unlabeled_pool_5000_teacher_review_priority.jsonl` (2,277
priority records + 88 calibration random from `conf_keep__cons_keep`). Script
13 then built `v2active002` (2,365 unique unlabeled candidates, 0 prior labels
matched, 0 in-pool duplicates). DeepSeek labeling is in progress.

## Test Set Comparability

This is a known data-integrity caveat that affects all cross-version metric
comparisons.

| Variant | Test records | Source population | Locked? |
| --- | ---: | --- | --- |
| v1 4B confident | 96 | starter_1000 only | no |
| v1 8B confident | 96 | starter_1000 only | no |
| v2 conservative | 224 | starter + targeted | no |
| v2 confident | 199 | starter + targeted (score 3 skipped) | no |
| v3 conservative | 264 | starter + targeted + v2active001 | YES |
| v3 confident | 237 | locked 264 minus 27 score-3 records | inherits subset of locked |

Implications:

- The 264-id locked test set was created on 2026-05-05 from
  `scorer_binary_sft_v3/scorer_binary_v3_conservative_test.jsonl`. Forward of
  v3, `scripts/09_build_binary_scorer_sft.py` enforces these ids stay in the
  test split.
- Pre-v3 metrics are on entirely different test populations than v3. Some
  ids that were in the v1 or v2 test split may now be in v3 training data
  because the lock only protects v3 forward.
- v3 confident is evaluated on a subset of the locked 264 (the 27 score-3
  records are skipped). When comparing v3 conservative to v3 confident,
  remember that conservative's 264-record test includes 27 records that
  confident never sees.
- Important: simply rerunning v1/v2 adapters on `locked_test_ids.json`
  produces biased numbers, because parts of the locked 264 ids were in v1
  and/or v2 training data (forward locking does not fix backward leakage).
  Direct cross-version comparison on the locked set is honest only for v3
  forward (v3 vs v4 vs v5 ...).
- Evergreen baseline test set (built 2026-05-06): 600 fresh records reserved
  permanently for cross-version comparison. Lock file:
  `data/eval/evergreen_test_ids.json`.
  - Stratum 1 (clean v1, 200 records): `data/splits/teacher_judge/evergreen_test/`,
    sampled from the 5,000 v3 unlabeled pool with source quotas
    120/50/30 cot_zh/finetome/openmath, all `is_clean=True`.
  - Stratum 2 (clean supplement, 300 records): merged into
    `data/splits/teacher_judge/evergreen_test_extension/`, source quotas
    180/75/45 to bring clean total to 500 (60/25/15 ratio).
  - Stratum 3 (flagged, 100 records): merged into the same extension file,
    sampled from the 188K processed pool minus all reservations, source
    quotas 40/60 cot_zh/finetome (openmath has only 65 flagged total in
    188K; not enough to stratify meaningfully).
  - Lock enforced at three layers: (1) labels never passed to
    `scripts/09_build_binary_scorer_sft.py` `--label-prefix`; (2) candidate
    files added to `DEFAULT_EXCLUDE_LABEL_FILES` in
    `scripts/02_sample_for_teacher.py`; (3) candidate files added to
    `DEFAULT_KNOWN_LABEL_FILES` in `scripts/13_build_teacher_review_batch.py`.
  - Resolved risk: `duplicate_pair` records have a content twin elsewhere
    in their source dataset; if a twin is in training, the evergreen score
    is contaminated. Fix applied 2026-05-06: the flagged stratum was
    resampled with `--exclude-flag duplicate_pair`. Final flag distribution
    on the 100 flagged records is 98 short_output + 1 short_instruction +
    1 possible_mojibake. Contamination risk is now negligible.
  - Known caveat (accepted, not fixed): clean stratum was sampled from the
    5,000 active-learning pool (which itself was source x length stratified
    from the 188K processed pool), while the flagged stratum was sampled
    directly from the 188K pool without length stratification. The 5,000
    pool is itself a stratified snapshot of 188K, so this asymmetry is
    second-order and does not affect cross-version comparison validity.
    Report the clean 500 and flagged 100 as two separate tables (not a
    weighted mean), and the asymmetry is irrelevant.

## Evergreen Cross-Version Evaluation (2026-05-06)

All six existing scorer adapters were evaluated on the 600-record evergreen
test set using the same LLaMA-Factory `qwen3_nothink` predict pipeline that
was used during training. (An earlier attempt to use
`scripts/12_infer_binary_scorer.py` produced wrong numbers because it used
the HuggingFace tokenizer's default chat template instead of the
`qwen3_nothink` template the scorers were trained on. That attempt was
discarded; do not reproduce it.)

Predict configs (one per adapter):
`configs/llamafactory/evergreen_predict_*.yaml`. Each config copies the
canonical LLaMA-Factory predict template and overrides only `dataset_dir`,
`eval_dataset`, `output_dir`. Aggregated by `scripts/17_evaluate_on_evergreen.py`,
which joins LF `generated_predictions.jsonl` to the evergreen LF source by
order, with first/middle/last record signature verification to catch any
order shuffling.

Headline result (Conservative GT, score 1-2-3 -> not_keep):

| Model | Clean accuracy | Clean not-keep recall | Flagged accuracy | Flagged not-keep recall |
| --- | ---: | ---: | ---: | ---: |
| v3 conservative | 77.00% | **10.08%** | 79.00% | **50.00%** |
| v3 confident | 76.20% | 0.00% | 76.00% | 17.86% |
| v2 conservative | 76.20% | 0.00% | 75.00% | 21.43% |
| v2 confident | 76.20% | 0.00% | 76.00% | 17.86% |
| v1 8B confident | 76.00% | 0.00% | 76.00% | 39.29% |
| v1 4B confident | 72.60% | **20.17%** | 74.00% | 42.86% |

(Full report including Confident GT and per-source breakdowns:
`reports/evergreen_cross_version_eval_report.md`. Metrics JSON:
`data/eval/evergreen_cross_version_eval_metrics.json`.)

Findings:

1. In-domain test severely overstated reject ability. v3 conservative's 77%
   not-keep recall on its own 264-record test drops to 10.08% on the
   evergreen clean stratum.
2. Four of six scorers predict `not_keep` zero times on the clean stratum
   (v3 confident, v2 conservative, v2 confident, v1 8B confident). They
   collapsed to an "all keep" output on rule_clean records.
3. Flagged stratum discrimination is acceptable across the board (17-50%
   not-keep recall). Scorers learned to lean on the rule_flag signal as the
   primary discriminator and to skip discrimination on rule_clean records.
4. v1 4B is the only baseline that meaningfully discriminates inside the
   clean stratum (20.17% not-keep recall). Hypothesis: smaller capacity
   blocked the rule-flag shortcut from fully forming during fine-tuning.
5. v3 conservative is still the best balanced scorer overall: highest reject
   on flagged (50%), second-highest reject on clean (10%), and the only 8B
   adapter doing any reject on clean.
6. openmath_reasoning is a near-zero-reject case for every scorer. True
   not_keep rate is ~12% on clean openmath, so the cost of all-keep is
   small, but no scorer rejects any openmath sample.

## Data Versions

The scorer training set is built incrementally. Each version adds a new
batch of teacher labels to the previous version's data.

| Version trained | Batch added | Records | Sampling method | Notes |
| --- | --- | ---: | --- | --- |
| v1 | starter (`teacher_labels_1000`) | 1,000 | Source-stratified random from 188K (cot_zh / finetome / openmath_reasoning), 80% clean / 20% flagged, length-bucketed (short / medium / long). Seed 42. | Foundation. Used by every later version. |
| v2 | targeted (`targeted_1200_teacher_labels`) | 1,200 | Hand-curated targeted batch focused on v1 weak/boundary areas (sources, lengths, and rule flags where v1 was unreliable). Built by `scripts/11_build_targeted_teacher_batch.py`. | First non-active-learning expansion. Helped v2 reject boundary not move much beyond v1's compact baseline. |
| v3 | `v2active001` | 388 | First active-learning batch. Built by running v2 conservative + v2 confident on a 3,600-record candidate pool, computing a priority queue (model disagreements + both_not_keep + flagged_but_keep), then deduplicating against existing teacher labels. The pool was not pre-filtered for already-labeled ids, so the priority queue lost 827 of 1,215 records to dedup. | Small batch but high signal: each record was a confirmed boundary case the v2 scorers wanted teacher review on. |
| v4 (in progress) | `v2active002` | 2,365 | Second active-learning batch. Same priority logic as v2active001 but on a fresh 5,000-record pool that was pre-filtered to exclude all teacher-labeled ids at sampling time, so 0 records lost to dedup. Includes 88 random calibration samples drawn from `conf_keep__cons_keep` (records both v3 scorers say keep) to detect silent agreement errors that the priority logic would miss. | Roughly 6x the size of v2active001 because the input pool was larger (5K vs 3.6K) and properly deduplicated. DeepSeek labeling 2026-05-06+. |

Naming note: the legacy prefix `v2active` was chosen when v2 was the latest
scorer family. It has stuck even though v2active002 was built using v3
scorers and feeds v4 training. Treat the prefix as an opaque batch label
unrelated to the scorer it was selected with. A planned rename to
`v1_data` / `v2_data` / `v3_data` / `v4_data` is queued for after
v2active002 finishes labeling, to avoid disrupting the active write.

Each version's binary scorer dataset is built by
`scripts/09_build_binary_scorer_sft.py` from these batches plus the
locked test ids reservation:

- v1 binary confident: starter only.
- v2 binary conservative / confident: starter + targeted.
- v3 binary conservative / confident: starter + targeted + v2active001.
- v4 binary conservative / confident: starter + targeted + v2active001 +
  v2active002 (planned).

Evergreen test ids and locked test ids are excluded from every training set
by enforcement in `scripts/02_sample_for_teacher.py` (default exclude list)
and `scripts/13_build_teacher_review_batch.py` (default known label files).

## Status Board

Completed and usable:

- Qwen3-4B v1 binary confident baseline.
- Qwen3-8B v1 binary confident capacity check.
- Targeted 1,200 DeepSeek teacher labels.
- V2 binary scorer datasets:
  - `scorer_binary_v2_confident`
  - `scorer_binary_v2_conservative`
- Qwen3-8B v2 conservative training, valid/test prediction, evaluation, and
  experiment report.
- Qwen3-8B v2 confident training, valid/test prediction, evaluation, and
  experiment report.
- Batch inference script:
  `scripts/12_infer_binary_scorer.py`
- Active-learning teacher batch script:
  `scripts/13_build_teacher_review_batch.py`
- Priority teacher analysis script:
  `scripts/14_analyze_teacher_review_priority.py`
- 3,600-row teacher-candidate pilot inference with both Qwen3-8B v2 adapters:
  - `reports/teacher_candidates_all_v2_conservative_inference_report.md`
  - `reports/teacher_candidates_all_v2_confident_inference_report.md`
  - `reports/teacher_candidates_all_v2_model_agreement_report.md`
  - `data/scored/teacher_candidates_all_v2_teacher_review_priority.jsonl`
  - `data/scored/teacher_candidates_all_v2_teacher_review_top919.jsonl`
  - `data/labeled/teacher_judge/v2_pilot_top919/v2_pilot_top919_teacher_prompts.jsonl`
- Deduplicated first active-learning teacher batch:
  - `reports/teacher_sampling_v2_active_pilot_001_report.md`
  - `reports/teacher_label_report_v2active001.md`
  - `reports/teacher_candidates_all_v2_priority_teacher_analysis_report.md`
  - `data/splits/teacher_judge/v2_active_pilot_001/v2active001_teacher_candidates_all.jsonl`
  - `data/labeled/teacher_judge/v2active001/v2active001_teacher_prompts.jsonl`
- V3 binary scorer datasets:
  - `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_conservative_report.md`
  - `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_confident_report.md`
  - `data/labeled/scorer_binary_sft_v3/dataset_info.json`
- V3 Qwen3-8B LLaMA-Factory configs:
  - `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_e3.yaml`
  - `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_predict_valid.yaml`
  - `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_predict_test.yaml`
  - `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_e3.yaml`
  - `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_predict_valid.yaml`
  - `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_predict_test.yaml`
- Qwen3-8B v3 conservative/confident training, valid/test prediction,
  evaluation, and experiment report:
  - `reports/scorer_binary_v3_qwen3_8b_experiment_report.md`
  - `reports/scorer_binary_v3_conservative_eval_valid_report.md`
  - `reports/scorer_binary_v3_conservative_eval_test_report.md`
  - `reports/scorer_binary_v3_confident_eval_valid_report.md`
  - `reports/scorer_binary_v3_confident_eval_test_report.md`
  - `data/eval/scorer_binary_v3_conservative_eval_valid_metrics.json`
  - `data/eval/scorer_binary_v3_conservative_eval_test_metrics.json`
  - `data/eval/scorer_binary_v3_confident_eval_valid_metrics.json`
  - `data/eval/scorer_binary_v3_confident_eval_test_metrics.json`
- Training lessons note:
  `reports/training_lessons_and_notes.md`

Current main candidate:

- `Qwen/Qwen3-8B` LoRA on `scorer_binary_v3_conservative`
- Local adapter:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3`
- Use it for prioritization, review routing, and selecting teacher relabeling
  candidates. Do not use it for blind automatic deletion.

Current companion candidate:

- `Qwen/Qwen3-8B` LoRA on `scorer_binary_v3_confident`
- Local adapter:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_confident_qwen3_8b_lora_e3`
- Use it as a high-confidence keep filter and as a contrast model against v3
  conservative. Disagreements between the two v3 8B models are useful
  teacher-relabeling candidates.

Best next action (2026-05-06):

Evergreen evaluation is now complete and exposed a structural weakness in
the active-learning loop: scorers learned a "rule_clean=True -> keep"
shortcut and barely discriminate inside the clean stratum (0-10% not_keep
recall on clean 500, vs 50% on flagged 100). The v4 plan needs an
intervention to fix this; see "v4 strategy decision" below before training.

Mechanical work, in order:

1. Wait for `v2active002` DeepSeek labeling to finish (2,365 records). After
   the rename pause, resume with `--resume`.
2. Run `scripts/05_analyze_teacher_labels.py` on the resulting label file
   and inspect the 88 calibration_random records specifically: count how
   many teacher-labeled them `drop` or `maybe`. That count is the v3 scorer's
   silent false-positive rate on rule_clean records.
3. Decide the v4 sampling strategy (see "v4 strategy decision" below).
4. Once v4 dataset composition is locked, build v4 binary scorer datasets
   from the chosen batches using `scripts/09_build_binary_scorer_sft.py`.
5. Train Qwen3-8B v4 conservative and confident variants under the existing
   v3 LoRA configs (only swap dataset names and output dirs).
6. Evaluate v4 on BOTH locked test (264) AND evergreen (600). The headline
   metric is v4's clean stratum not_keep recall on evergreen; that is the
   number that needs to move materially upward.

## v4 Strategy Decision

The current `v2active002` batch (2,365 records) was selected on the same
priority criteria as `v2active001`: model disagreements, both_not_keep, and
flagged_but_model_keep. Plus 88 random calibration records from
`conf_keep__cons_keep`.

Evergreen evaluation showed the priority signals are over-indexed on rule-
flagged boundary cases. Inside the clean stratum (where production-time
filtering matters most), the scorer needs more "clean records that look
keep but are actually drop" to break the rule_clean shortcut. The 88
calibration records partly address this, but at ~24% expected drop rate
they only contribute ~21 hard negatives — small relative to the rest of
v4 (2,277 priority records skewed toward flagged content).

Three options for v4 (see end of `evergreen_cross_version_eval_report.md`
discussion in the README for the diagnostic context):

- **A. Train v4 on `v2active002` as-is.** No additional sampling. Fastest
  path. Risk: v4's clean-stratum reject ability may not improve materially
  over v3.
- **B. Add a random clean supplement to v4 before training.** Sample 500
  fresh clean records from the 188K pool (excluding labeled + evergreen +
  locked), label with DeepSeek (~30 min, <$3), add to v4 training set. At
  ~24% drop rate this contributes ~120 hard negatives directly aimed at
  the rule_clean shortcut. Recommended.
- **C. Restructure `v2active002` itself.** Drop the priority-skewed records
  in favor of more random clean. Wasteful given labeling is ~half done.
  Not recommended.

The recommended default is B. Decision is open until v2active002 labeling
finishes and the calibration_random subset gives a concrete estimate of
the silent error rate. If the calibration confirms >15% silent drop rate
on rule_clean, B becomes a strong default.

## Goal

Build a small local data-quality scorer for supervised fine-tuning samples. The
scorer should imitate a stronger teacher model well enough to filter or
prioritize future SFT data at lower cost.

## Current Pipeline

1. Normalize source datasets into a shared schema.
2. Apply light rule-based quality checks.
3. Sample a 1,000-example starter set with source-aware allocation.
4. Label the starter set with a teacher model.
5. Convert teacher labels into LLaMA-Factory SFT format.
6. Train a Qwen3-4B LoRA scorer.
7. Evaluate on held-out valid/test splits.
8. Simplify the target into a binary confident scorer because the original
   1-5 score task had ambiguous middle labels.
9. Add targeted teacher labels for known weak/boundary areas.
10. Build v2 binary datasets with both confident and conservative score-3
    policies.
11. Train and evaluate Qwen3-8B v2 conservative as the current quality-first
    candidate.
12. Train and evaluate Qwen3-8B v2 confident as the high-confidence keep
    ablation.
13. Run both Qwen3-8B v2 scorers on the 3,600-row teacher-candidate pilot pool.
14. Build and label the deduplicated active-learning batch `v2active001`.
15. Build v3 binary datasets from starter + targeted + `v2active001`.
16. Train and evaluate Qwen3-8B v3 conservative/confident variants.
17. Run both v3 scorers on a 5,000-record unlabeled pool, build the
    agreement / priority queue, and produce the `v2active002` teacher batch.
18. (in progress) DeepSeek-label `v2active002` (2,365 records).
19. Next: build v4 binary datasets from starter + targeted + v2active001 +
    v2active002 and train Qwen3-8B v4 conservative/confident.

## Data Sources

- `cot_zh`: Chinese chain-of-thought style reasoning data.
- `finetome`: broad instruction-following data.
- `openmath_reasoning`: math reasoning data.

The starter split is intentionally not equal-weighted. It keeps the source mix
closer to the project goal and gives enough examples to compare behavior by
source.

## Completed Artifacts

Teacher-label artifacts:

- `reports/teacher_sampling_starter_1000_report.md`
- `reports/teacher_label_report_1000.md`
- `data/labeled/teacher_judge/pilot_teacher_labels.jsonl`
- `data/labeled/teacher_judge/starter_1000_teacher_labels.jsonl`

Original 1-5 scorer artifacts:

- `data/labeled/scorer_sft/scorer_sft_report.md`
- `reports/scorer_eval_valid_greedy_report.md`
- `reports/scorer_eval_test_greedy_report.md`
- `reports/scorer_error_analysis_greedy_report.md`

Binary confident scorer artifacts:

- `data/labeled/scorer_binary_sft/scorer_binary_confident_1000_report.md`
- `reports/scorer_binary_eval_valid_report.md`
- `reports/scorer_binary_eval_test_report.md`
- `reports/scorer_binary_experiment_report.md`

Qwen3-8B v1 capacity-check artifacts:

- `configs/llamafactory/scorer_binary_confident_1000_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_confident_1000_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_confident_1000_qwen3_8b_lora_predict_test.yaml`
- `reports/scorer_binary_qwen3_8b_v1_experiment_report.md`
- `reports/scorer_binary_eval_valid_qwen3_8b_v1_report.md`
- `reports/scorer_binary_eval_test_qwen3_8b_v1_report.md`

Next teacher-labeling batch artifacts:

- `scripts/11_build_targeted_teacher_batch.py`
- `reports/teacher_sampling_targeted_1200_report.md`
- `reports/teacher_label_report_targeted_1200.md`
- `data/splits/teacher_judge/targeted_1200/targeted_teacher_candidates_all.jsonl`
- `data/labeled/teacher_judge/targeted_1200_teacher_prompts.jsonl`
- `data/labeled/teacher_judge/targeted_1200_teacher_labels.jsonl`

V2 binary scorer dataset artifacts:

- `data/labeled/scorer_binary_sft_v2/scorer_binary_v2_confident_report.md`
- `data/labeled/scorer_binary_sft_v2/scorer_binary_v2_conservative_report.md`
- `data/labeled/scorer_binary_sft_v2/dataset_info.json`

V3 binary scorer dataset artifacts:

- `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_confident_report.md`
- `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_conservative_report.md`
- `data/labeled/scorer_binary_sft_v3/dataset_info.json`

Qwen3-8B v3 training/evaluation configs:

- `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_v3_conservative_qwen3_8b_lora_predict_test.yaml`
- `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_v3_confident_qwen3_8b_lora_predict_test.yaml`

Qwen3-8B v2 conservative artifacts:

- `configs/llamafactory/scorer_binary_v2_conservative_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_v2_conservative_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_v2_conservative_qwen3_8b_lora_predict_test.yaml`
- `reports/scorer_binary_v2_conservative_qwen3_8b_experiment_report.md`
- `reports/scorer_binary_v2_conservative_eval_valid_report.md`
- `reports/scorer_binary_v2_conservative_eval_test_report.md`
- `data/eval/scorer_binary_v2_conservative_eval_valid_metrics.json`
- `data/eval/scorer_binary_v2_conservative_eval_test_metrics.json`

Qwen3-8B v2 confident artifacts:

- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_e3.yaml`
- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_valid.yaml`
- `configs/llamafactory/scorer_binary_v2_confident_qwen3_8b_lora_predict_test.yaml`
- `reports/scorer_binary_v2_confident_qwen3_8b_experiment_report.md`
- `reports/scorer_binary_v2_confident_eval_valid_report.md`
- `reports/scorer_binary_v2_confident_eval_test_report.md`
- `data/eval/scorer_binary_v2_confident_eval_valid_metrics.json`
- `data/eval/scorer_binary_v2_confident_eval_test_metrics.json`

Teacher-candidate v2 inference artifacts:

- `reports/teacher_candidates_all_v2_conservative_inference_report.md`
- `reports/teacher_candidates_all_v2_confident_inference_report.md`
- `reports/teacher_candidates_all_v2_model_agreement_report.md`
- `data/scored/teacher_candidates_all_v2_conservative_predictions.jsonl`
- `data/scored/teacher_candidates_all_v2_confident_predictions.jsonl`
- `data/scored/teacher_candidates_all_v2_model_agreement_metrics.json`
- `data/scored/teacher_candidates_all_v2_model_disagreements.jsonl`
- `data/scored/teacher_candidates_all_v2_teacher_review_priority.jsonl`
- `data/scored/teacher_candidates_all_v2_teacher_review_top919.jsonl`
- `data/labeled/teacher_judge/v2_pilot_top919/v2_pilot_top919_teacher_prompts.jsonl`

Learning and handoff notes:

- `reports/training_lessons_and_notes.md`
- All `reports/*.md` files now use a common report header:
  `Report Metadata` followed by `Experiment Context`.

## Current Best Result

The Qwen3-8B v3 conservative scorer is the current main quality-first candidate.
The Qwen3-8B v3 confident scorer is the companion high-confidence keep filter.
The Qwen3-4B v1 binary confident scorer remains the compact baseline.

Qwen3-8B v3 conservative (current main candidate, `scorer_binary_v3_conservative`):

| Split | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | ---: | ---: | ---: | ---: | ---: |
| Valid | 74.16% | 0.756 | 0.725 | 72.80% | 100% |
| Test | 76.89% | 0.796 | 0.734 | 77.06% | 100% |

Interpretation:

- Best reject-boundary metrics to date: test not_keep F1 0.734 and not_keep
  recall 77.06%.
- Prediction distribution is balanced: 144 keep / 120 not_keep on test split.
- Per-source test accuracy: cot_zh 71.32%, finetome 77.67%, openmath 96.88%.
  cot_zh remains the weakest source.
- Use for review routing, hard-negative mining, and teacher-relabeling
  prioritization. Do not use for blind automatic deletion.

Qwen3-8B v3 confident (companion high-confidence keep filter, `scorer_binary_v3_confident`):

| Split | Accuracy | Keep F1 | Not-keep F1 | Not-keep recall | JSON valid |
| --- | ---: | ---: | ---: | ---: | ---: |
| Valid | 72.65% | 0.794 | 0.595 | 51.09% | 100% |
| Test | 78.90% | 0.851 | 0.638 | 53.66% | 100% |

Interpretation:

- Keep recall 92.26% on test; useful for prioritizing likely keep examples.
- Not-keep recall only 53.66%; do not use as a reject model.
- Disagreements between v3 conservative and v3 confident are the highest-value
  teacher-relabeling candidates.

Historical results for reference:

Qwen3-4B v1 binary confident (compact baseline):

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 82.11% | 0.872 | 0.702 | 100% |
| Test | 76.04% | 0.824 | 0.623 | 100% |

Qwen3-8B v1 binary confident capacity check (same 1,000-example dataset):

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 77.89% | 0.851 | 0.571 | 100% |
| Test | 84.38% | 0.899 | 0.651 | 100% |

- Test not_keep recall was only 51.85%; too keep-biased for reject routing.

Qwen3-8B v2 conservative:

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 74.55% | 0.799 | 0.655 | 100% |
| Test | 79.91% | 0.844 | 0.717 | 100% |

- Test not_keep recall 64.04%. Superseded by v3 conservative.

Qwen3-8B v2 confident:

| Split | Accuracy | Keep F1 | Not-keep F1 | JSON valid |
| --- | ---: | ---: | ---: | ---: |
| Valid | 76.14% | 0.832 | 0.591 | 100% |
| Test | 82.41% | 0.879 | 0.679 | 100% |

- Test not_keep recall 57.81%. Superseded by v3 confident.

Training notes:

- `reports/training_lessons_and_notes.md` summarizes the practical training
  settings, observed model behavior, Windows/LLaMA-Factory pitfalls, metric
  interpretation, and recommended next learning experiments.

V2 binary scorer datasets are now ready:

| Dataset | Records | Train | Valid | Test | Keep | Not-keep | Score 3 Policy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `scorer_binary_v2_confident` | 1,968 | 1,572 | 197 | 199 | 1,283 | 685 | skipped |
| `scorer_binary_v2_conservative` | 2,200 | 1,752 | 224 | 224 | 1,283 | 917 | mapped to `not_keep` |

`scorer_binary_v2_conservative` was used as the first v2 training target
because the project policy is quality-first and score 3 should not be
auto-kept.

V3 binary scorer datasets (trained and evaluated on 2026-05-05):

| Dataset | Records | Train | Valid | Test | Keep | Not-keep | Score 3 Policy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `scorer_binary_v3_confident` | 2,326 | 1,855 | 234 | 237 | 1,438 | 888 | skipped |
| `scorer_binary_v3_conservative` | 2,588 | 2,057 | 267 | 264 | 1,438 | 1,150 | mapped to `not_keep` |

Compared with v2, v3 adds the 388 teacher-confirmed active-learning examples
from `v2active001`. V3 conservative has now been trained and is the current
main quality-first scorer; v3 confident is the companion high-confidence keep
ablation.

Local model artifacts are not committed to GitHub. The important local adapter
paths are:

- Original 1-5 scorer:
  `C:\Users\haoran27\llamafactory_outputs\scorer_sft_1000_qwen3_4b_lora_e3`
- Binary confident scorer:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_4b_lora_e3`
- Qwen3-8B binary confident v1 capacity check:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_confident_1000_qwen3_8b_lora_e3`
- Qwen3-8B binary conservative v2:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_conservative_qwen3_8b_lora_e3`
- Qwen3-8B binary confident v2:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v2_confident_qwen3_8b_lora_e3`
- Qwen3-8B binary conservative v3:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3`
- Qwen3-8B binary confident v3:
  `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_confident_qwen3_8b_lora_e3`

Use the binary setup for future scorer experiments. The 4B adapter is the
compact baseline, while the v3 conservative 8B adapter is the current main
quality-first candidate and the v3 confident 8B adapter is the companion
high-confidence keep candidate.

3,600-row teacher-candidate pilot result:

| Bucket | Count |
| --- | ---: |
| confident keep + conservative keep | 2,681 |
| confident keep + conservative not_keep | 272 |
| confident not_keep + conservative keep | 1 |
| confident not_keep + conservative not_keep | 646 |

Interpretation:

- The two Qwen3-8B v2 scorers agree on 92.42% of the teacher-candidate pilot.
- The 273 disagreements are compact boundary cases for teacher relabeling.
- The 646 both-not-keep examples are the strongest hard-negative candidates.
- The priority review queue has 1,215 records after adding clean-not_keep and
  flagged-but-kept cases.
- The original top919 file
  `data/scored/teacher_candidates_all_v2_teacher_review_top919.jsonl` contains
  all 273 model disagreements plus all 646 both-not-keep records, but it is not
  fully unlabeled. Some records were already labeled in the starter/targeted
  teacher batches.
- The deduplicated first teacher-labeling batch is
  `data/splits/teacher_judge/v2_active_pilot_001/v2active001_teacher_candidates_all.jsonl`
  with 388 priority records that were unlabeled at selection time, and prompts
  are in
  `data/labeled/teacher_judge/v2active001/v2active001_teacher_prompts.jsonl`.

## Why the Binary Task Exists

The original 1-5 score task worked technically, but the middle class was noisy:

- `maybe` had near-zero recall.
- Many mistakes were off-by-one score disagreements.
- The teacher rubric itself has fuzzy boundaries around score 3.

The binary confident dataset removes score-3 examples and asks a cleaner
question: "Is this clearly useful training data or clearly not?"

## Next Steps

Recommended next work:

1. Treat v3 training/evaluation as complete and use
   `reports/scorer_binary_v3_qwen3_8b_experiment_report.md` as the current
   scorer report.
2. Use v3 conservative as the main quality-first scorer for review routing and
   hard-negative mining.
3. Use v3 confident as the high-confidence keep companion.
4. Run both v3 scorers on a larger unlabeled pool, excluding all already
   teacher-labeled original sample `id`s.
5. Keep a small calibration sample from three buckets:
   - high-confidence keep
   - high-confidence not_keep
   - conservative/confident disagreement examples
6. Use the teacher model only on uncertain or high-impact examples.
7. Add more negative examples, especially from `cot_zh` and `finetome`.
8. Keep Qwen3-4B as the compact comparison baseline, but do not prioritize
   v2 4B training until the 8B models have been used to mine hard cases.
9. Only after the binary scorer is stable, consider adding a second-stage
   severity score or a calibrated confidence score.

Concrete next implementation plan:

1. Run v3 conservative and v3 confident inference on the next candidate pool
   with `scripts/12_infer_binary_scorer.py`.
2. Build a v3 agreement/disagreement report similar to the v2 3,600-row pilot
   report.
3. Use `scripts/13_build_teacher_review_batch.py` again with a new batch prefix
   such as `v2active002`, excluding all prior teacher-label files by original
   sample `id`.
4. Prioritize teacher review from:
   - v3 conservative/confident disagreements
   - v3 conservative predicted `not_keep`
   - rule-flagged examples predicted `keep`
   - `cot_zh` examples near the current weak boundary
5. After the next teacher batch is labeled, rebuild the binary scorer dataset
   as the next data version and compare against v3 conservative/confident.

Avoid spending much more effort on the 1-5 score setup until the binary filter
is more stable. The 1-5 scorer is useful as an error-analysis reference, but it
is not the best current training target.

## Downstream SFT Validation Plan (Phase E)

This is the project's final validation: prove that the scorer actually improves
a downstream supervised fine-tuning run, not just that it imitates teacher
labels. As of 2026-05-05 this is design only; do not start until the gates
below are satisfied.

### Goal

Show that filtering an SFT dataset with the v4 (or later) binary scorer
produces a measurably better fine-tuned model than the same SFT pipeline run
on (a) random data and (b) rule-clean data, on a fixed evaluation suite.

### Pre-flight gates

Do not start Phase E until:

- The binary scorer has not_keep recall >= 85% on the locked test set
  (`data/eval/locked_test_ids.json`). v3 conservative is at 77.06%; one or two
  more active-learning rounds (`v2active002`, `v2active003`) should be the
  natural lift.
- Inference cost for filtering the SFT pool is understood. Running v4
  conservative + confident over 188,103 records at `batch_size=1` is on the
  order of 16-30 hours; budget GPU time or batch the pool down.
- Disk has room for 4-5 LoRA adapters and their training/eval logs (~5-10 GB
  per LoRA on a 7B target model).

### Open decisions

Each item below is a launch-blocking choice. The recommendation is the
current default unless the user changes it.

1. **Target base model.** Recommendation: `Qwen2.5-7B` base. Reasons: similar
   capacity to the scorer, different generation than Qwen3 (so the base does
   not have memorized scorer training data), well-studied. Alternatives:
   `Qwen2.5-3B` for faster iteration, `Llama-3-8B` for cross-family check.
2. **SFT data pool.** Recommendation: keep using `unified_sft_clean.jsonl`
   (188K). Same three sources the scorer was trained on, so the scorer is in
   distribution. Do not pull in unrelated sources for the first comparison.
3. **Evaluation suite.** Recommendation:
   - GSM8K (math reasoning, covers `cot_zh` and `openmath_reasoning`)
   - IFEval (instruction following, covers `finetome`)
   - MMLU (general knowledge baseline)
   Skip code benchmarks (e.g. HumanEval) since the SFT pool is not code. Skip
   preference evals (MT-Bench, AlpacaEval) for the first run because they
   require an LLM judge and add noise.
4. **Sample size N.** Recommendation: 20K per group. 5K is too small for MMLU
   sensitivity, 50K doubles training time without clear benefit for a first
   pass. Use the same N across groups so data quality is the only variable.
5. **Comparison groups.**
   - **G0 base.** Untrained `Qwen2.5-7B` base, zero-shot.
   - **G1 random.** N drawn uniformly from the 188K pool.
   - **G2 rule-clean.** N drawn uniformly from `is_clean == true` records.
   - **G3 scorer-keep.** N drawn from records the v4 conservative scorer
     predicts `keep`.
   - **G4 scorer-strict.** N drawn from records where both v4 conservative
     and v4 confident predict `keep` (intersection).
   - **G5 anti-baseline (optional).** N drawn from records the scorer
     predicts `not_keep`. If G5 underperforms G1, the scorer is doing
     something useful even when G3/G4 do not beat G1 by much.
   For all groups, match source distribution to G1 so the only difference
   across runs is the keep/not_keep filter, not the source mix.
6. **SFT training setup.** Recommendation: LoRA, rank 16, lr 1e-4, 3 epochs,
   identical config across groups. Fixed seed. Save the final checkpoint of
   each run; do not best-checkpoint-select per group, otherwise different
   groups get different effective training durations.
7. **What counts as "improvement."** Report the delta on each benchmark
   relative to G0 (base) and compare deltas across G1-G4. A scorer is
   interesting if G3 or G4 beats G1 by more than the run-to-run noise floor.
   Rerun G1 with two seeds to estimate that noise floor.

### Pipeline steps once decisions are locked

1. Run v4 scorer (conservative + confident) on the full SFT pool. Save
   keep/not_keep predictions per id.
2. Sample G1-G4 (and optionally G5) so that source distribution matches G1
   and N is identical.
3. Convert each group to LLaMA-Factory SFT format and write
   `dataset_info.json` entries.
4. Train each group with the same LLaMA-Factory config, changing only
   `dataset` and `output_dir`.
5. Run the evaluation suite on G0 (base) and on each trained adapter.
6. Aggregate results into a single comparison report and decide whether the
   scorer is production ready or needs another scorer iteration.

### New artifacts the project will need

- `scripts/15_score_full_sft_pool.py`: large-scale scorer inference on
  `unified_sft_clean.jsonl` with both v4 adapters; outputs joined per-id
  predictions and source breakdowns.
- `scripts/16_build_sft_comparison_groups.py`: samples G1-G4 from the scored
  pool with matched source distribution and identical N.
- `scripts/17_export_sft_dataset.py`: converts a sampled group into
  LLaMA-Factory dataset format and writes a `dataset_info.json` entry.
- `configs/llamafactory/sft_eval_*_qwen25_7b_lora.yaml`: training configs
  for each comparison group.
- `scripts/18_run_eval_suite.py`: wraps GSM8K / IFEval / MMLU evaluation
  for base model and each LoRA adapter; writes per-run metrics JSON.
- `scripts/19_compare_sft_results.py`: aggregates eval outputs into a
  single markdown comparison table.

### Risks to watch

- **Source bias.** The scorer treats `cot_zh`, `finetome`, and
  `openmath_reasoning` differently. If G3/G4 has a skewed source mix relative
  to G1, the comparison is unfair. Match source distribution across groups.
- **Insufficient keep pool.** If v4's overall keep rate on the 188K pool is
  below ~30%, G3/G4 may exhaust before reaching N=20K. Verify keep rate
  before committing to N.
- **Run-to-run noise.** A 0.5% delta on MMLU is within noise for small N.
  Rerun G1 with at least two seeds to set a noise floor before reading any
  improvement claim.
- **Evaluation leakage.** Confirm that the SFT pool does not contain GSM8K
  or MMLU training items. If it does, the comparison measures contamination,
  not data quality.

## GitHub Notes

Commit:

- scripts
- prompts
- configs
- markdown reports
- small metadata files

Use `PROJECT_FILE_INVENTORY.md` as the pre-GitHub checklist.

Do not commit:

- raw datasets
- generated JSONL data
- API keys
- Hugging Face cache files
- LLaMA-Factory model outputs
- local checkpoint directories

Current `.gitignore` is set up to ignore generated JSONL files, processed data,
splits, Python caches, local checkpoints, model weights, and environment files.
If future work creates new generated directories, update `.gitignore` before
committing.
