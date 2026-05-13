# Report Index

Last updated: 2026-05-13

This folder keeps experiment reports for traceability. The current project
decision is no longer based only on scorer validation metrics; Phase E
downstream SFT validation is the main evidence.

Start with:

1. `../PROJECT_PLAN.md`
2. `../README.md`
3. `phase_e_downstream_pairwise_report.md`
4. `phase_e_downstream_dataset_report.md`
5. `evergreen_v2_all_models_eval_report.md`
6. `evergreen_v2_noflag_all_models_eval_report.md`

## Current Canonical Reports

### Phase E Downstream Validation

- `phase_e_downstream_pairwise_report.md`
  - Current strongest evidence. Teacher pairwise judge over the four downstream
    Qwen3-8B LoRA models plus openmath `\boxed{}` exact-match accuracy.
  - Current winner: `v4_both_keep`.
- `phase_e_downstream_prediction_comparison_report.md`
  - BLEU/ROUGE/token-F1 comparison. Kept as a cautionary proxy-metric report:
    it ranks `unfiltered` first, but pairwise judging and math accuracy overturn
    that result.
- `phase_e_downstream_dataset_report.md`
  - Describes the four 15k downstream training datasets and v4 scorer agreement
    buckets.
- `phase_e_downstream_eval_sampling_report.md`
  - Documents the fixed 200-prompt downstream eval set.
- `phase_e_clean_candidate_sampling_report.md`
  - Documents the exclusion-safe 15k candidate pool.
- `phase_e_v4_conservative_clean_15k_inference_report.md`
  - v4 conservative scorer inference over the 15k Phase E pool.
- `phase_e_v4_confident_clean_15k_inference_report.md`
  - v4 confident scorer inference over the same 15k Phase E pool.

### Evergreen V2 Scorer Evaluation

- `evergreen_v2_all_models_eval_report.md`
  - Current cross-version scorer benchmark with the normal prompt.
- `evergreen_v2_noflag_all_models_eval_report.md`
  - Shortcut-ablation benchmark with rule fields removed.
- `evergreen_v2_v4_conservative_eval_report.md`
- `evergreen_v2_v4_confident_eval_report.md`
- `evergreen_v2_noflag_v4_conservative_eval_report.md`
- `evergreen_v2_noflag_v4_confident_eval_report.md`
  - Per-model v4 reports retained for detail.

### V4 Data Construction

- `teacher_sampling_v2_active_pilot_002_report.md`
  - Active-learning continuation used in v4.
- `v4_random_supplement_sampling_report.md`
  - Random production-like clean supplement.
- `v4_cot_zh_short_clean_sampling_report.md`
  - Targeted hard clean `cot_zh` supplement.
- `teacher_sampling_v3_unlabeled_pool_5000_report.md`
- `v3_unlabeled_pool_5000_model_agreement_report.md`
- `v3_unlabeled_pool_5000_conservative_inference_report.md`
- `v3_unlabeled_pool_5000_confident_inference_report.md`
  - Pool analysis that led into later active-learning and v4 data.

### Scorer Training Baselines

- `scorer_binary_v3_qwen3_8b_experiment_report.md`
  - Main v3 scorer experiment record. Useful historical comparison: v3 was
    more aggressive but less suitable as the main auto-filter.
- `scorer_binary_v3_conservative_eval_valid_report.md`
- `scorer_binary_v3_conservative_eval_test_report.md`
- `scorer_binary_v3_confident_eval_valid_report.md`
- `scorer_binary_v3_confident_eval_test_report.md`
- `scorer_binary_v2_conservative_qwen3_8b_experiment_report.md`
- `scorer_binary_v2_confident_qwen3_8b_experiment_report.md`
- `scorer_binary_qwen3_8b_v1_experiment_report.md`
- `scorer_binary_experiment_report.md`
  - Earlier binary-scorer baselines retained for comparison.

### Reference Notes

- `training_lessons_and_notes.md`
  - Living notes on task framing, training settings, evaluation pitfalls, and
    Windows/LLaMA-Factory operational details.
- `quality_rubric.md`
  - Teacher-label rubric.
- `data_report.md`
  - Source data summary.
- `llamafactory_startup.md`
  - Local LLaMA-Factory WebUI startup notes.

## Historical Reports

These are retained for reproducibility and should not drive new decisions unless
the current plan explicitly references them.

- Original 1-5 scorer reports:
  - `scorer_eval_valid_greedy_report.md`
  - `scorer_eval_test_greedy_report.md`
  - `scorer_eval_valid_report.md`
  - `scorer_eval_test_report.md`
  - `scorer_error_analysis_greedy_report.md`
  - `scorer_error_analysis_report.md`
- Early teacher sampling and labeling:
  - `teacher_sampling_report.md`
  - `teacher_sampling_starter_1000_report.md`
  - `teacher_label_report_1000.md`
  - `teacher_sampling_targeted_1200_report.md`
  - `teacher_label_report_targeted_1200.md`
  - `teacher_sampling_v2_active_pilot_001_report.md`
  - `teacher_label_report_v2active001.md`
  - `teacher_candidates_all_v2_*`
- Earlier evergreen v0/v1/v3 transition reports:
  - `evergreen_cross_version_eval_report.md`
  - `evergreen_noflag_cross_version_eval_report.md`
  - `evergreen_v1_*`
  - `evergreen_v2_conservative_inference_report.md`
  - `evergreen_v2_confident_inference_report.md`
  - `evergreen_v3_*`
  - `evergreen_test_*`
  - `evergreen_clean_expansion_sampling_report.md`
- Pilot reports:
  - `pilot_sampling_report.md`
  - `pilot_label_review.md`

## Reports Outside This Directory

Some generated dataset reports live beside their dataset metadata:

- `data/labeled/scorer_sft/scorer_sft_report.md`
- `data/labeled/scorer_binary_sft/scorer_binary_confident_1000_report.md`
- `data/labeled/scorer_binary_sft_v2/scorer_binary_v2_confident_report.md`
- `data/labeled/scorer_binary_sft_v2/scorer_binary_v2_conservative_report.md`
- `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_confident_report.md`
- `data/labeled/scorer_binary_sft_v3/scorer_binary_v3_conservative_report.md`
- `data/labeled/scorer_binary_sft_v3_noflag/scorer_binary_v3_conservative_noflag_report.md`
- `data/labeled/scorer_binary_sft_v4/scorer_binary_v4_confident_report.md`
- `data/labeled/scorer_binary_sft_v4/scorer_binary_v4_conservative_report.md`

## Cleanup Notes

- Do not commit large JSONL data, model outputs, or LLaMA-Factory checkpoints.
- Keep old markdown reports unless there is a clear duplicate; they are cheap
  and useful for reconstructing the experiment path.
- Prefer updating this index over deleting reports that encode a real completed
  run.
