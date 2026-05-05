# Qwen3-8B V3 Binary Scorer Experiment

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-05 |
| Report type | Experiment summary |
| Project stage | V3 binary scorer training/evaluation |
| Report status | Current canonical v3 scorer report |

## Experiment Context

| Field | Value |
| --- | --- |
| Base model | `Qwen/Qwen3-8B` |
| Fine-tuning | LoRA, rank 8, target all |
| Data version | `scorer_binary_sft_v3` |
| Training data | Starter + targeted 1200 + `v2active001` teacher labels |
| Conservative policy | score 4/5 -> `keep`; score 1/2/3 -> `not_keep` |
| Confident policy | score 4/5 -> `keep`; score 1/2 -> `not_keep`; score 3 skipped |
| Current use | Decide whether v3 replaces v2 as the main quality scorer |

## Training Summary

| Variant | Train records | Valid records | Test records | Best checkpoint | Best eval loss | Train runtime |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| v3 conservative | 2,057 | 267 | 264 | `checkpoint-250` | 0.057244 | 35m 59s |
| v3 confident | 1,855 | 234 | 237 | `checkpoint-100` | 0.053559 | 32m 24s |

Both runs completed normally with 100% valid JSON/schema generation in greedy
prediction.

## Evaluation Summary

| Variant | Split | Accuracy | Keep F1 | Not-keep F1 | Keep recall | Not-keep recall | Prediction mix |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| v3 conservative | valid | 74.16% | 0.756 | 0.725 | 75.35% | 72.80% | 141 keep / 126 not_keep |
| v3 conservative | test | 76.89% | 0.796 | 0.734 | 76.77% | 77.06% | 144 keep / 120 not_keep |
| v3 confident | valid | 72.65% | 0.794 | 0.595 | 86.62% | 51.09% | 168 keep / 66 not_keep |
| v3 confident | test | 78.90% | 0.851 | 0.638 | 92.26% | 53.66% | 181 keep / 56 not_keep |

## Source Breakdown

| Variant | Split | `cot_zh` accuracy | `finetome` accuracy | `openmath_reasoning` accuracy |
| --- | --- | ---: | ---: | ---: |
| v3 conservative | valid | 71.21% | 76.47% | 78.79% |
| v3 conservative | test | 71.32% | 77.67% | 96.88% |
| v3 confident | valid | 65.14% | 77.66% | 83.87% |
| v3 confident | test | 74.55% | 77.89% | 96.88% |

## Interpretation

V3 conservative is the new main quality-first candidate. On the current v3 test
split, it gives the healthiest reject behavior: `not_keep` F1 is 0.734 and
`not_keep` recall is 77.06%. Its prediction distribution is also balanced
against the v3 conservative label distribution, which is important for review
routing.

V3 confident remains a high-confidence keep companion rather than a reject
model. Its test keep recall is high at 92.26%, but `not_keep` recall is only
53.66%, and it predicts keep for 181 / 237 test records. This is useful for
prioritizing likely keep examples, but not for surfacing bad or ambiguous data.

The v3 test split is not identical to the v2 test split, so v2/v3 metrics should
not be treated as a strict apples-to-apples comparison. Still, the direction is
consistent with the project goal: adding teacher-confirmed active-learning
examples made the conservative scorer more useful for finding questionable
samples.

## Run Artifacts

Training adapters:

- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_confident_qwen3_8b_lora_e3`

Prediction outputs:

- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3_predict_valid_greedy\generated_predictions.jsonl`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3_predict_test_greedy\generated_predictions.jsonl`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_confident_qwen3_8b_lora_e3_predict_valid_greedy\generated_predictions.jsonl`
- `C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_confident_qwen3_8b_lora_e3_predict_test_greedy\generated_predictions.jsonl`

Evaluation reports:

- `reports/scorer_binary_v3_conservative_eval_valid_report.md`
- `reports/scorer_binary_v3_conservative_eval_test_report.md`
- `reports/scorer_binary_v3_confident_eval_valid_report.md`
- `reports/scorer_binary_v3_confident_eval_test_report.md`

Metric JSON:

- `data/eval/scorer_binary_v3_conservative_eval_valid_metrics.json`
- `data/eval/scorer_binary_v3_conservative_eval_test_metrics.json`
- `data/eval/scorer_binary_v3_confident_eval_valid_metrics.json`
- `data/eval/scorer_binary_v3_confident_eval_test_metrics.json`

## Recommended Next Actions

1. Treat v3 conservative as the current main scorer for review routing and hard
   negative mining.
2. Keep v3 confident as the companion high-confidence keep model.
3. Run both v3 scorers on a larger unlabeled pool, excluding all already
   teacher-labeled original sample `id`s.
4. Build the next active-learning teacher batch from:
   - v3 conservative/confident disagreements
   - v3 conservative predicted `not_keep`
   - rule-flagged examples predicted `keep`
   - `cot_zh` examples near the current weak boundary
5. Continue to avoid blind automatic deletion. V3 conservative is better for
   `not_keep` routing, but its false-positive/false-negative counts are still
   too high for irreversible filtering.
