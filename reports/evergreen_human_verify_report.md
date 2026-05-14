# Evergreen Human Verification Report

This report compares the 50-record human audit against the DeepSeek teacher labels.

## Headline

- Completed human annotations: 50/50
- Exact 3-way verdict agreement: 43/50 (86.0%)
- Exact score agreement: 38/50 (76.0%)
- Within-one score agreement: 47/50 (94.0%)
- Conservative binary agreement (score 1-3 -> not_keep, 4-5 -> keep): 46/50 (92.0%)
- Average human-minus-teacher score: 0.08
- Average absolute score gap: 0.32

## Distributions

| Bucket           | Counts                                                                                   |
| ---------------- | ---------------------------------------------------------------------------------------- |
| Source           | {'cot_zh': 30, 'finetome': 15, 'openmath_reasoning': 5}                                  |
| Domain heuristic | {'code_or_programming': 5, 'cot_zh_reasoning': 30, 'general_instruction': 10, 'math': 5} |
| Clean status     | {'clean': 40, 'flagged': 10}                                                             |
| Teacher score    | {'1': 5, '2': 2, '3': 5, '4': 6, '5': 32}                                                |
| Human score      | {'1': 4, '2': 2, '3': 4, '4': 8, '5': 32}                                                |
| Teacher verdict  | {'keep': 38, 'maybe': 5, 'not_keep': 7}                                                  |
| Human verdict    | {'keep': 39, 'maybe': 5, 'not_keep': 6}                                                  |

## Per Source

| Source             | N  | Teacher scores                            | Human scores                              | Human verdicts                          | 3-way agree | Conservative binary agree |
| ------------------ | -- | ----------------------------------------- | ----------------------------------------- | --------------------------------------- | ----------- | ------------------------- |
| cot_zh             | 30 | {'1': 3, '2': 1, '3': 5, '4': 3, '5': 18} | {'1': 2, '2': 1, '3': 3, '4': 5, '5': 19} | {'keep': 23, 'maybe': 4, 'not_keep': 3} | 83.3%       | 90.0%                     |
| finetome           | 15 | {'1': 2, '2': 1, '4': 3, '5': 9}          | {'1': 2, '2': 1, '3': 1, '4': 3, '5': 8}  | {'keep': 11, 'maybe': 1, 'not_keep': 3} | 86.7%       | 93.3%                     |
| openmath_reasoning | 5  | {'5': 5}                                  | {'5': 5}                                  | {'keep': 5}                             | 100.0%      | 100.0%                    |

## Per Domain Heuristic

| Domain              | N  | Human scores                              | Human verdicts                          | Human score <=3 | Human not_keep |
| ------------------- | -- | ----------------------------------------- | --------------------------------------- | --------------- | -------------- |
| code_or_programming | 5  | {'3': 1, '5': 4}                          | {'keep': 4, 'maybe': 1}                 | 1               | 0              |
| cot_zh_reasoning    | 30 | {'1': 2, '2': 1, '3': 3, '4': 5, '5': 19} | {'keep': 23, 'maybe': 4, 'not_keep': 3} | 6               | 3              |
| general_instruction | 10 | {'1': 2, '2': 1, '4': 3, '5': 4}          | {'keep': 7, 'not_keep': 3}              | 3               | 3              |
| math                | 5  | {'5': 5}                                  | {'keep': 5}                             | 0               | 0              |

## Teacher x Human Verdict Confusion

Rows are teacher normalized verdicts; values are human normalized verdict counts.

```json
{
  "keep": {
    "keep": 36,
    "maybe": 1,
    "not_keep": 1
  },
  "maybe": {
    "keep": 3,
    "maybe": 2
  },
  "not_keep": {
    "maybe": 2,
    "not_keep": 5
  }
}
```

## High-Disagreement Records

| Rank | Source   | Clean | Teacher   | Human        | Score gap | Human notes                   |
| ---- | -------- | ----- | --------- | ------------ | --------- | ----------------------------- |
| #37  | finetome | clean | 5 / keep  | 2 / not_keep | -3        | 没有抓住题目关键逻辑                    |
| #06  | cot_zh   | clean | 3 / maybe | 5 / keep     | 2         | instruction略长，但是回答找到相关句子，逻辑清晰 |
| #27  | cot_zh   | clean | 3 / maybe | 5 / keep     | 2         | 推理完整正确                        |

## 3-Way Verdict Disagreements

| Rank | Source   | Teacher      | Human        | Human notes                      |
| ---- | -------- | ------------ | ------------ | -------------------------------- |
| #03  | cot_zh   | 3 / maybe    | 4 / keep     | 原文两句话可以联想到一起，但是没有直接语义关联，不能推断出结果。 |
| #06  | cot_zh   | 3 / maybe    | 5 / keep     | instruction略长，但是回答找到相关句子，逻辑清晰    |
| #09  | cot_zh   | 2 / not_keep | 3 / maybe    | 根据背景，回答没有太多问题，但是预训练知识没有被用到       |
| #17  | cot_zh   | 4 / keep     | 4 / maybe    | 有点怪，但推理正确                        |
| #27  | cot_zh   | 3 / maybe    | 5 / keep     | 推理完整正确                           |
| #37  | finetome | 5 / keep     | 2 / not_keep | 没有抓住题目关键逻辑                       |
| #38  | finetome | 2 / not_keep | 3 / maybe    | 可能教模型短输入该怎么回答，但是质量不高             |

## Human Label Consistency Notes

These records have a human score/verdict mismatch under the conservative score mapping (1-3 -> not_keep, 4-5 -> keep). They are worth normalizing before using the labels as training data.

| Rank | Source | Human score | Human verdict | Human notes |
| ---- | ------ | ----------- | ------------- | ----------- |
| #17  | cot_zh | 4           | maybe         | 有点怪，但推理正确   |

## Interpretation

- The human audit does not show a large teacher-label failure rate overall; most disagreements are boundary moves between `maybe`, `keep`, and `not_keep` rather than complete reversals.
- The audit sample is not adequate for estimating math/code false-negative rates: the math/code-heavy subset is overwhelmingly `keep`, and the openmath slice has no human `not_keep` examples.
- For v5, do not rely on another generic active-learning round alone. Build a targeted math/code hard-negative queue with real-answer checks where possible.

## Recommended Next Step

Create a targeted teacher-labeling batch for math/code hard negatives:

- openmath: mine expected-answer mismatches, missing final answers, invalid `\boxed{}` answers, and reasoning/final-answer contradictions.
- code: mine code-like prompts with syntax/runtime/test failures where lightweight checks are available, plus ambiguous API/spec mismatches for teacher review.
- keep a balancing slice of math/code `keep` examples so the next scorer does not learn `math/code -> not_keep`.
- keep this batch separate from evergreen test data; use it for v5 training, not for benchmark leakage.
