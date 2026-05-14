# Phase E Downstream Pairwise Teacher Judge

Total labels: 264 (valid: 200)

## Per-Model Aggregate

| Model | N | Avg rank ↓ | 1st place | Last place | 1st rate | Correct rate | Wrong rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| unfiltered | 200 | 3.035 | 41 | 51 | 0.205 | 0.605 | 0.25 |
| v4_conservative_keep | 200 | 3.115 | 37 | 37 | 0.185 | 0.635 | 0.25 |
| v4_confident_keep | 200 | 3.045 | 39 | 38 | 0.195 | 0.625 | 0.25 |
| v4_both_keep | 200 | 2.855 | 48 | 37 | 0.24 | 0.695 | 0.185 |
| v4_persource_keep | 200 | 2.95 | 35 | 37 | 0.175 | 0.645 | 0.205 |

Avg rank is lower-is-better (1 = best). 1st rate = fraction of prompts where this model placed first.

## Versus Unfiltered

| Model | Wins | Losses | Win rate vs unfiltered |
| --- | ---: | ---: | ---: |
| v4_conservative_keep | 97 | 103 | 0.485 |
| v4_confident_keep | 105 | 95 | 0.525 |
| v4_both_keep | 105 | 95 | 0.525 |
| v4_persource_keep | 100 | 100 | 0.5 |

## Pairwise Win Rates (row beats column)

| | unfiltered | v4_conservative_keep | v4_confident_keep | v4_both_keep | v4_persource_keep |
| --- | ---: | ---: | ---: | ---: | ---: |
| unfiltered | — | 0.515 (103/200) | 0.475 (95/200) | 0.475 (95/200) | 0.5 (100/200) |
| v4_conservative_keep | 0.485 (97/200) | — | 0.49 (98/200) | 0.45 (90/200) | 0.46 (92/200) |
| v4_confident_keep | 0.525 (105/200) | 0.51 (102/200) | — | 0.45 (90/200) | 0.47 (94/200) |
| v4_both_keep | 0.525 (105/200) | 0.55 (110/200) | 0.55 (110/200) | — | 0.52 (104/200) |
| v4_persource_keep | 0.5 (100/200) | 0.54 (108/200) | 0.53 (106/200) | 0.48 (96/200) | — |

## By Source (Avg Rank)

### openmath_reasoning

| Model | N | Avg rank |
| --- | ---: | ---: |
| unfiltered | 40 | 3.075 |
| v4_conservative_keep | 40 | 3.025 |
| v4_confident_keep | 40 | 3.075 |
| v4_both_keep | 40 | 2.55 |
| v4_persource_keep | 40 | 3.275 |

### cot_zh

| Model | N | Avg rank |
| --- | ---: | ---: |
| unfiltered | 80 | 2.913 |
| v4_conservative_keep | 80 | 3.025 |
| v4_confident_keep | 80 | 2.975 |
| v4_both_keep | 80 | 3.2 |
| v4_persource_keep | 80 | 2.888 |

### finetome

| Model | N | Avg rank |
| --- | ---: | ---: |
| unfiltered | 80 | 3.138 |
| v4_conservative_keep | 80 | 3.25 |
| v4_confident_keep | 80 | 3.1 |
| v4_both_keep | 80 | 2.663 |
| v4_persource_keep | 80 | 2.85 |

## Math Accuracy (openmath_reasoning, \boxed{} match)

Records with reference \boxed{}: 40

| Model | Correct | Extracted | Total | Accuracy | Extract rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| unfiltered | 22 | 35 | 40 | 0.55 | 0.875 |
| v4_conservative_keep | 19 | 32 | 40 | 0.475 | 0.8 |
| v4_confident_keep | 18 | 32 | 40 | 0.45 | 0.8 |
| v4_both_keep | 23 | 36 | 40 | 0.575 | 0.9 |
| v4_persource_keep | 20 | 34 | 40 | 0.5 | 0.85 |

Math accuracy is an **objective** signal: did the model produce the same final \boxed{} answer as the reference?
