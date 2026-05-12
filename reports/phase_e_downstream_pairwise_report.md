# Phase E Downstream Pairwise Teacher Judge

Total labels: 200 (valid: 200)

## Per-Model Aggregate

| Model | N | Avg rank ↓ | 1st place | Last place | 1st rate | Correct rate | Wrong rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| unfiltered | 200 | 2.565 | 53 | 61 | 0.265 | 0.6 | 0.255 |
| v4_conservative_keep | 200 | 2.51 | 45 | 47 | 0.225 | 0.595 | 0.235 |
| v4_confident_keep | 200 | 2.535 | 48 | 49 | 0.24 | 0.575 | 0.245 |
| v4_both_keep | 200 | 2.39 | 54 | 43 | 0.27 | 0.68 | 0.16 |

Avg rank is lower-is-better (1 = best). 1st rate = fraction of prompts where this model placed first.

## Versus Unfiltered

| Model | Wins | Losses | Win rate vs unfiltered |
| --- | ---: | ---: | ---: |
| v4_conservative_keep | 103 | 97 | 0.515 |
| v4_confident_keep | 106 | 94 | 0.53 |
| v4_both_keep | 104 | 96 | 0.52 |

## Pairwise Win Rates (row beats column)

| | unfiltered | v4_conservative_keep | v4_confident_keep | v4_both_keep |
| --- | ---: | ---: | ---: | ---: |
| unfiltered | — | 0.485 (97/200) | 0.47 (94/200) | 0.48 (96/200) |
| v4_conservative_keep | 0.515 (103/200) | — | 0.53 (106/200) | 0.445 (89/200) |
| v4_confident_keep | 0.53 (106/200) | 0.47 (94/200) | — | 0.465 (93/200) |
| v4_both_keep | 0.52 (104/200) | 0.555 (111/200) | 0.535 (107/200) | — |

## By Source (Avg Rank)

### finetome

| Model | N | Avg rank |
| --- | ---: | ---: |
| unfiltered | 80 | 2.65 |
| v4_conservative_keep | 80 | 2.575 |
| v4_confident_keep | 80 | 2.562 |
| v4_both_keep | 80 | 2.212 |

### cot_zh

| Model | N | Avg rank |
| --- | ---: | ---: |
| unfiltered | 80 | 2.538 |
| v4_conservative_keep | 80 | 2.388 |
| v4_confident_keep | 80 | 2.475 |
| v4_both_keep | 80 | 2.6 |

### openmath_reasoning

| Model | N | Avg rank |
| --- | ---: | ---: |
| unfiltered | 40 | 2.45 |
| v4_conservative_keep | 40 | 2.625 |
| v4_confident_keep | 40 | 2.6 |
| v4_both_keep | 40 | 2.325 |

## Math Accuracy (openmath_reasoning, \boxed{} match)

Records with reference \boxed{}: 40

| Model | Correct | Extracted | Total | Accuracy | Extract rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| unfiltered | 22 | 35 | 40 | 0.55 | 0.875 |
| v4_conservative_keep | 19 | 32 | 40 | 0.475 | 0.8 |
| v4_confident_keep | 18 | 32 | 40 | 0.45 | 0.8 |
| v4_both_keep | 23 | 36 | 40 | 0.575 | 0.9 |

Math accuracy is an **objective** signal: did the model produce the same final \boxed{} answer as the reference?
