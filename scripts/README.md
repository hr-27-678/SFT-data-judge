# Script Index

Last updated: 2026-05-13

Run scripts from the repository root unless a script says otherwise. On the
school Windows machine, prefer the UNC project path if `U:` is not visible in a
non-interactive shell:

```powershell
Set-Location -LiteralPath "\\ad.uillinois.edu\engr-ews\haoran27\微调\SFT-DataJudge"
```

Keep `PYTHONIOENCODING=utf-8` / `PYTHONUTF8=1` set when running long jobs that
print Chinese examples.

## Current Phase E Pipeline

- `27_sample_phase_e_candidates.py`
  - Samples the fixed exclusion-safe 15k clean downstream candidate pool.
- `28_build_phase_e_downstream_datasets.py`
  - Joins v4 scorer outputs with the 15k pool and builds four LLaMA-Factory
    downstream SFT datasets: unfiltered, v4 conservative keep, v4 confident
    keep, and v4 both-keep intersection.
- `run_phase_e_downstream_train.ps1`
  - Runs the four Phase E downstream train configs.
- Phase E prediction configs live in `configs/llamafactory/` and are named
  `phase_e_*_predict_eval_200.yaml`.
- `29_sample_phase_e_downstream_eval.py`
  - Builds the fixed 200-prompt held-out eval set and its LLaMA-Factory
    dataset.
- `30_compare_phase_e_downstream_predictions.py`
  - Compares the four generated prediction files with BLEU/ROUGE/token-F1 and
    writes the side-by-side review queue.
- `31_teacher_judge_pairwise.py`
  - Runs the teacher pairwise judge over the four downstream models. It supports
    dry-run rendering, concurrency, response-format JSON mode, and resume.
- `32_aggregate_pairwise_results.py`
  - Aggregates pairwise labels into model rankings, win rates, per-source
    metrics, and openmath `\boxed{}` exact-match accuracy.

Current readout: `v4_both_keep` is the best downstream policy overall, but
`v4_conservative_keep` is best on `cot_zh`. The next natural experiment is a
per-source policy.

## Evergreen Evaluation

- `16_sample_evergreen_test.py`
  - Historical first evergreen sampler.
- `16_resample_evergreen_test.py`
  - Resamples the fixed evergreen test set.
- `16b_extend_evergreen_test.py`
  - Extends the evergreen clean slice.
- `16c_extend_evergreen_flagged.py`
  - Extends the evergreen flagged slice.
- `17_evaluate_on_evergreen.py`
  - Evaluates scorer predictions on evergreen sets and writes reports.
- `18_build_evergreen_lf_dataset.py`
  - Builds LLaMA-Factory datasets for evergreen scorer prediction.
- `21_sample_evergreen_clean_expansion.py`
  - Samples additional clean-looking evergreen candidates.
- `22_build_evergreen_noflag_lf_dataset.py`
  - Builds no-flag prompt datasets for shortcut-ablation runs.
- `23_sample_evergreen_human_verify.py`
  - Samples the 50-record evergreen human-audit set.
- `24_merge_evergreen_v2.py`
  - Merges evergreen pieces into `evergreen_v2`.
- `25_generate_evergreen_v2_predict_configs.py`
  - Generates normal/no-flag evergreen_v2 LLaMA-Factory predict configs.
- `run_all_evergreen_inferences.ps1`
  - Historical evergreen inference runner.
- `run_all_evergreen_noflag_inferences.ps1`
  - Historical no-flag evergreen inference runner.
- `run_all_evergreen_v2_inferences.ps1`
  - Current evergreen_v2 inference runner.
- `verify_evergreen_labels.py`
  - Checks evergreen label consistency.

## Teacher Labeling And Active Learning

- `01_prepare_data.py`
  - Normalizes source datasets and writes processed JSONL files.
- `02_sample_for_teacher.py`
  - Builds teacher-candidate splits with source-aware sampling.
- `03_build_pilot.py`
  - Builds a small pilot set for teacher-label sanity checks.
- `04_teacher_judge.py`
  - Calls the teacher model and writes labels incrementally; supports resume by
    skipping examples already written.
- `05_analyze_teacher_labels.py`
  - Summarizes teacher labels and writes label reports. Use `--dedupe-by-id`
    when retry outputs were appended to the same JSONL.
- `11_build_targeted_teacher_batch.py`
  - Builds the targeted 1,200-example teacher-labeling batch.
- `13_build_teacher_review_batch.py`
  - Builds deduplicated active-learning teacher batches from scorer priority
    queues.
- `14_analyze_teacher_review_priority.py`
  - Joins scorer priority queues with teacher labels by original sample `id`.
- `15_analyze_v3_pool_agreement.py`
  - Analyzes v3 pool model agreement and disagreement buckets.
- `19_sample_v4_random_supplement.py`
  - Samples the random production-like clean supplement for v4.
- `20_sample_cot_zh_short_clean.py`
  - Samples targeted hard clean `cot_zh` records for v4.
- `26_prepare_v4_label_splits.py`
  - Prepares the v4 merged label splits after active-learning additions.

## Scorer Dataset, Inference, And Eval

- `06_build_scorer_sft.py`
  - Converts teacher labels into the original 1-5 scorer SFT dataset.
- `07_evaluate_scorer_predictions.py`
  - Evaluates original 1-5 scorer predictions.
- `08_analyze_scorer_errors.py`
  - Produces error-analysis reports for the original 1-5 scorer.
- `09_build_binary_scorer_sft.py`
  - Converts teacher labels into binary scorer datasets. `confident` skips
    score 3; `all` maps score 3 to `not_keep`.
- `10_evaluate_binary_scorer_predictions.py`
  - Evaluates binary scorer predictions and writes markdown reports.
- `12_infer_binary_scorer.py`
  - Runs a trained binary scorer adapter on unlabeled candidate pools. Supports
    resume-by-id, deterministic greedy generation, prompt-only dry runs, scored
    JSONL output, and source/rule-disagreement summaries.

## Local Utilities

- `start_llamafactory_webui.ps1`
  - Starts the LLaMA-Factory WebUI on the school Windows machine.
  - If PowerShell blocks scripts, run with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_llamafactory_webui.ps1
```
