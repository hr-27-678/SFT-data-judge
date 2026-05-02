# Scorer Error Analysis

Generated: 2026-05-01 17:13:37

## Summary

| Metric | Value |
| --- | --- |
| Records | 208 |
| Keep precision | 108/144 (75.00%) |
| Keep recall | 108/136 (79.41%) |
| Drop precision | 25/58 (43.10%) |
| Drop recall | 25/55 (45.45%) |
| Maybe recall | 0/17 (0.00%) |

## High-Risk Error Counts

| Category | Count | Why it matters |
| --- | ---: | --- |
| label drop -> predict keep | 25 | Bad samples would pass filtering. |
| label keep -> predict drop | 27 | Good samples would be thrown away. |
| label maybe missed | 17 | Boundary cases are not calibrated. |
| score error >= 2 | 67 | Model is not just off by one. |
| cot_zh score/verdict errors | 62 | Main weak source. |

## By Split

| Split | Records | Verdict acc | Score exact | Score +/-1 | drop->keep | keep->drop | maybe missed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| test | 104 | 59.62% | 43.27% | 63.46% | 14 | 16 | 8 |
| valid | 104 | 68.27% | 51.92% | 72.12% | 11 | 11 | 9 |

## By Source

| Source | Records | Verdict acc | Score exact | Score +/-1 | drop->keep | keep->drop | maybe missed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| cot_zh | 84 | 46.43% | 26.19% | 54.76% | 9 | 19 | 12 |
| finetome | 84 | 69.05% | 53.57% | 70.24% | 13 | 8 | 4 |
| openmath_reasoning | 40 | 90.00% | 80.00% | 90.00% | 3 | 0 | 1 |

## Diagnosis

- The model has learned the output schema, but it is not yet a reliable teacher replacement.
- The dominant failure is calibration, not JSON formatting.
- `cot_zh` is the main bottleneck. It mixes translated entailment/math-style prompts, option wording noise, and terse answers; the student often over-trusts or over-penalizes these examples.
- `maybe` is not learned as a real middle class. It is treated as either keep or drop, so a 3-way scorer is currently poorly calibrated.
- For filtering, `keep` precision is usable for a first-pass high-quality pool, but `drop` recall is too low to safely remove all bad data.

## Recommended Adjustments

1. Do not tune hyperparameters first. The bottleneck is data coverage and label boundary calibration.
2. Add targeted teacher labels: more `cot_zh`, more `maybe`, and more `drop` cases that look superficially fluent.
3. Consider a two-stage label: first `usable/not_usable`, then optional 1-5 score. This can improve filtering utility even if exact scores remain noisy.
4. Add eval during training for the next run, so we can stop by validation verdict accuracy instead of only train loss.
5. For immediate use, treat predictions conservatively: only auto-keep high-confidence keep-style outputs after spot checks; do not auto-drop based only on this model yet.

## Representative Errors

## Teacher drop, model keep

### Teacher drop, model keep #1

- Split/source/id: `valid` / `cot_zh` / `tj_cot_zh_00063`
- Label: score `1`, verdict `drop`
- Predict: score `5`, verdict `keep`
- Score error: `4`
- Label reason: The output gives an incorrect answer (no) without valid reasoning; the correct answer should be 'cannot determine'.
- Predict reason: Clear instruction, correct answer with concise reasoning, no issues.

**Instruction**

鉴于句子“一个男孩在水中齐膝”。我们可以得出“一个男孩在上学”的结论吗？\n选项：\n- 是\n- 无法判断\n- 否 让我们尽可能准确并首先考虑。

**Output**

如果男孩在水中，他就不能上学。最后回答：没有。

### Teacher drop, model keep #2

- Split/source/id: `valid` / `cot_zh` / `tj_cot_zh_00301`
- Label: score `1`, verdict `drop`
- Predict: score `5`, verdict `keep`
- Score error: `4`
- Label reason: The output gives a completely wrong answer (73) and the reasoning is nonsensical, indicating a broken or mismatched sample.
- Predict reason: Clear instruction, correct answer with reasonable reasoning, no data issues.

**Instruction**

提问：在x-y平面上，如果x和y都是整数，点(x,y)是一个格点。圆 C 的圆心在 (-2, -2)，直径为 8。一些点，例如圆心 (-2, -2)，在圆内，但有一个点，例如 (-2, 2)在圆上而不在圆内。圆C有多少格点？\n选项：\n(A) 40\n(B) 10\n(C) 73\n(D) 60\n(E) 63 一些意识流：

**Output**

圆内位于透视轴上的格点如下：由于直径为8，9个点位于横轴（8+圆心）上，但端点不在圆上，所以9- 2（纵轴同理，但不再计算中心），7 - 1. 圆内非横纵轴格点如下：格点在45, 45/轴的 2 度和 30 度（水平轴和垂直轴分别为 30 度和 45/2 度），因此数字与以前相同，但不再计算中心。所以， 13 + 5 * 12 = 73\n圆上共有73个格点。答案：（C）。

### Teacher drop, model keep #3

- Split/source/id: `valid` / `openmath_reasoning` / `tj_openmath_reasoning_00129`
- Label: score `1`, verdict `drop`
- Predict: score `5`, verdict `keep`
- Score error: `4`
- Label reason: The output derives a different integral than the target, missing the correct transformation to âˆ« 1/(âˆš3 sin z - cos z) dz.
- Predict reason: Clear instruction, correct and complete reasoning, no issues.

**Instruction**

How does one go from \[ I_{1}=\frac{1}{\sqrt{3}}\int\frac{1}{(t-1)\sqrt{\left(\frac{2t+1}{\sqrt{3}}\right)^{2}+1}}\ dt \] to \[ I_{1}=\int\frac{1}{\sqrt{3}\sin z-\cos z}\ dz =\frac{\sqrt{3}}{6}\ln\tan\left(\frac{z}{2}-\frac{\pi}{6}\right)+C \]?

**Output**

To solve the integral \( I_1 = \frac{1}{\sqrt{3}} \int \frac{1}{(t-1)\sqrt{\left( \frac{2t+1}{\sqrt{3}} \right)^2 + 1}} \, dt \) and transform it into the form \( I_1 = \int \frac{1}{\sqrt{3} \sin z - \cos z} \, dz \), we proceed as follows: 1. **Substitution \( u = \frac{2t + 1}{\sqrt{3}} \)**: \[ u = \frac{2t + 1}{\sqrt{3}} \implies t = \frac{u \sqrt{3} - 1}{2} \] Differentiating both sides with respect to \( t \): \[ du = \frac{2}{\sqrt{3}} \, dt \implies dt = \frac{\sqrt{3}}{2} \, du \] Substituting \( t \) and \( dt \) into the integral: \[ I_1 = \frac{1}{\sqrt{3}} \int \frac{1}{\left( \frac{u \sqrt{3} - 1}{2} - 1 \right) \sqrt{u^2 + 1}} \cdot \frac{\sqrt{3}}{2} \, du \] Simplifying ...

### Teacher drop, model keep #4

- Split/source/id: `test` / `cot_zh` / `tj_cot_zh_00220`
- Label: score `1`, verdict `drop`
- Predict: score `5`, verdict `keep`
- Score error: `4`
- Label reason: Output misinterprets 'ä¸ƒåˆ†ä¹‹ä¸ƒ' as 7/10 instead of 7/7, leading to an incorrect final answer.
- Predict reason: Clear instruction, correct and complete reasoning, final answer matches.

**Instruction**

给出一步一步的推理过程，然后给出最终答案。在一个有 800 名学生的学校里，5/8 的学生是女生。七分之七的女孩和五分之二的男孩是小学生，其余的是中学生。有多少中学生？

**Output**

有 800 x 5 / 8 = 500 个女孩。所以，有 800 - 500 = 300 个男孩。有 500 x 7 / 10 = 350 名小学女生。因此，500 - 350 = 150 名女孩是中学生。小学有 300 x 2 / 5 = 120 个男孩。因此，300 - 120 = 180 男学生是中学生。因此，一共150名女生+180名男生=330名中学生。 最终答案：330。

## Teacher keep, model drop

### Teacher keep, model drop #1

- Split/source/id: `valid` / `cot_zh` / `tj_cot_zh_00324`
- Label: score `5`, verdict `keep`
- Predict: score `1`, verdict `drop`
- Score error: `-4`
- Label reason: Clear instruction, correct answer with concise reasoning.
- Predict reason: The output contains an extraneous request to 'list solutions' that does not belong in the instruction or response, making it irrelevant and corrupted.

**Instruction**

以下哪个句子没有意义？\n选项：\n- 句子 A：“她吃了太多辣椒，得了蛀牙”\n- 句子 B：“她吃了太多糖果，得了蛀牙”\n 嗯，让我想想。我想详细列出解决方案。

**Output**

辣椒不含糖，不会导致蛀牙。答案是A句。

### Teacher keep, model drop #2

- Split/source/id: `valid` / `finetome` / `tj_finetome_00338`
- Label: score `5`, verdict `keep`
- Predict: score `1`, verdict `drop`
- Score error: `-4`
- Label reason: Instruction clear, response correct and complete for a simple word replacement task.
- Predict reason: The output only contains the corrected word without the full sentence, making it incomplete and thus not useful for instruction following.

**Instruction**

Replace the word in bold with a suitable word to make the sentence meaningful. The students were given a book each to read for the homwork.

**Output**

homework.

### Teacher keep, model drop #3

- Split/source/id: `test` / `finetome` / `tj_finetome_00071`
- Label: score `5`, verdict `keep`
- Predict: score `1`, verdict `drop`
- Score error: `-4`
- Label reason: Clear instruction, correct and complete answer, no issues.
- Predict reason: The response incorrectly treats B as a set of elements and applies union to mixed types, leading to a wrong answer; the instruction was clear but the response is factually wrong.

**Instruction**

Let A={1} and B={2}. Calculate the following: (AxB) U B =? A U (BxB) =?

**Output**

To solve these problems, we first need to find the Cartesian products AxB and BxB, and then find the union of the sets. 1. AxB: The Cartesian product of two sets A and B, denoted AxB, is the set of all ordered pairs (a, b) where a is in A and b is in B. In this case, A = {1} and B = {2}, so AxB = {(1, 2)}. 2. BxB: Similarly, BxB is the set of all ordered pairs (b1, b2) where b1 is in B and b2 is in B. Since B = {2}, BxB = {(2, 2)}. Now, we can find the unions: 1. (AxB) U B: The union of two sets A and B, denoted A U B, is the set of all elements that are in A, in B, or in both. In this case, (AxB) = {(1, 2)} and B = {2}, so (AxB) U B = {(1, 2), 2}. 2. A U (BxB): Using the same definition ...

### Teacher keep, model drop #4

- Split/source/id: `test` / `finetome` / `tj_finetome_00358`
- Label: score `5`, verdict `keep`
- Predict: score `1`, verdict `drop`
- Score error: `-4`
- Label reason: Correct solution with clear reasoning and complete steps.
- Predict reason: The output incorrectly treats the vowel group as [AAEI] and fails to account for the correct vowel count and arrangement, resulting in a wrong final answer.

**Instruction**

In how many ways can you arrange the letters of the word "MATHEMATICS" such that all vowels appear together?

**Output**

First, let's identify the vowels and consonants in the word "MATHEMATICS": Vowels: A, A, E, I Consonants: M, T, H, M, T, C, S Since all vowels must appear together, we can treat them as a single unit: [AAEI]. Now, we have 8 units to arrange: M, T, H, M, T, C, S, and [AAEI]. There are 8! (factorial) ways to arrange these 8 units: 8! = 8 × 7 × 6 × 5 × 4 × 3 × 2 × 1 = 40,320 However, we have two M's and two T's among the consonants, so we need to divide by 2! for each of these repetitions: Adjusted arrangements = 8! / (2! * 2!) = 40,320 / (2 * 2) = 10,080 Now, within the [AAEI] unit, there are 4 vowels. We must also account for their internal arrangements. There are 4! ways to arrange them: ...

## Teacher maybe, model missed

### Teacher maybe, model missed #1

- Split/source/id: `valid` / `cot_zh` / `tj_cot_zh_00046`
- Label: score `3`, verdict `maybe`
- Predict: score `5`, verdict `keep`
- Score error: `2`
- Label reason: Instruction contains leaked reasoning trace; answer is correct but explanation is minimal.
- Predict reason: Clear instruction, correct answer with concise reasoning, no issues.

**Instruction**

您会沿着什么特征找到玫瑰花丛？\n选项：\n- 公园\n- 在地下\n- 树篱\n- 温带气候\n- 植物园 嗯，让我想想。

**Output**

蔷薇发现于树篱中。树篱是一个特点。 所以，答案是树篱。

### Teacher maybe, model missed #2

- Split/source/id: `valid` / `cot_zh` / `tj_cot_zh_00191`
- Label: score `3`, verdict `maybe`
- Predict: score `5`, verdict `keep`
- Score error: `2`
- Label reason: Answer is plausible but reasoning is weak and does not properly justify the choice.
- Predict reason: Clear instruction, correct answer with valid reasoning, no data issues.

**Instruction**

使用推理得出以下问题的答案： 圆珠笔在哪里写支票有用？\n选项：\n- 银行\n- 背包\n- 办公桌\n- 家\n- 书桌抽屉 推理过程：

**Output**

银行是从中提取资金的机构。支票用于提款。所以，最后的答案是银行。

### Teacher maybe, model missed #3

- Split/source/id: `valid` / `cot_zh` / `tj_cot_zh_00230`
- Label: score `3`, verdict `maybe`
- Predict: score `5`, verdict `keep`
- Score error: `2`
- Label reason: The output provides a correct final answer but uses a factually incorrect reasoning about the play's characters.
- Predict reason: Clear instruction, correct answer with valid reasoning, no issues.

**Instruction**

以下句子是否正确？\n“罗密欧与朱丽叶在结婚前同居。”\n选项：\n- 是\n- 否 让我们先想想。逐步推理过程：

**Output**

罗密欧与朱丽叶其实是一部以16世纪为背景的爱情故事剧，没有固定的男女名字。所以，答案是否定的。

### Teacher maybe, model missed #4

- Split/source/id: `valid` / `cot_zh` / `tj_cot_zh_00304`
- Label: score `3`, verdict `maybe`
- Predict: score `5`, verdict `keep`
- Score error: `2`
- Label reason: The answer is plausible but debatable; the reasoning is acceptable but brief.
- Predict reason: Clear instruction, correct answer with valid reasoning, no data corruption.

**Instruction**

下一个问题：莉莉喜欢和平与安静，但她找不到任何她住的地方。她采取了严厉的措施，去了一个孤独的地方。她去哪儿了？\n选项：\n- 图书馆\n- 家\n- 山顶\n- 大海\n- 杂货店 推理：

**Output**

大海是一个宁静祥和的地方。一个人可以获得平静和完全的孤独。一个人可以在海上找到孤独。答案是大海。

## cot_zh mismatch

### cot_zh mismatch #1

- Split/source/id: `valid` / `cot_zh` / `tj_cot_zh_00063`
- Label: score `1`, verdict `drop`
- Predict: score `5`, verdict `keep`
- Score error: `4`
- Label reason: The output gives an incorrect answer (no) without valid reasoning; the correct answer should be 'cannot determine'.
- Predict reason: Clear instruction, correct answer with concise reasoning, no issues.

**Instruction**

鉴于句子“一个男孩在水中齐膝”。我们可以得出“一个男孩在上学”的结论吗？\n选项：\n- 是\n- 无法判断\n- 否 让我们尽可能准确并首先考虑。

**Output**

如果男孩在水中，他就不能上学。最后回答：没有。

### cot_zh mismatch #2

- Split/source/id: `valid` / `cot_zh` / `tj_cot_zh_00301`
- Label: score `1`, verdict `drop`
- Predict: score `5`, verdict `keep`
- Score error: `4`
- Label reason: The output gives a completely wrong answer (73) and the reasoning is nonsensical, indicating a broken or mismatched sample.
- Predict reason: Clear instruction, correct answer with reasonable reasoning, no data issues.

**Instruction**

提问：在x-y平面上，如果x和y都是整数，点(x,y)是一个格点。圆 C 的圆心在 (-2, -2)，直径为 8。一些点，例如圆心 (-2, -2)，在圆内，但有一个点，例如 (-2, 2)在圆上而不在圆内。圆C有多少格点？\n选项：\n(A) 40\n(B) 10\n(C) 73\n(D) 60\n(E) 63 一些意识流：

**Output**

圆内位于透视轴上的格点如下：由于直径为8，9个点位于横轴（8+圆心）上，但端点不在圆上，所以9- 2（纵轴同理，但不再计算中心），7 - 1. 圆内非横纵轴格点如下：格点在45, 45/轴的 2 度和 30 度（水平轴和垂直轴分别为 30 度和 45/2 度），因此数字与以前相同，但不再计算中心。所以， 13 + 5 * 12 = 73\n圆上共有73个格点。答案：（C）。

### cot_zh mismatch #3

- Split/source/id: `valid` / `cot_zh` / `tj_cot_zh_00324`
- Label: score `5`, verdict `keep`
- Predict: score `1`, verdict `drop`
- Score error: `-4`
- Label reason: Clear instruction, correct answer with concise reasoning.
- Predict reason: The output contains an extraneous request to 'list solutions' that does not belong in the instruction or response, making it irrelevant and corrupted.

**Instruction**

以下哪个句子没有意义？\n选项：\n- 句子 A：“她吃了太多辣椒，得了蛀牙”\n- 句子 B：“她吃了太多糖果，得了蛀牙”\n 嗯，让我想想。我想详细列出解决方案。

**Output**

辣椒不含糖，不会导致蛀牙。答案是A句。

### cot_zh mismatch #4

- Split/source/id: `test` / `cot_zh` / `tj_cot_zh_00220`
- Label: score `1`, verdict `drop`
- Predict: score `5`, verdict `keep`
- Score error: `4`
- Label reason: Output misinterprets 'ä¸ƒåˆ†ä¹‹ä¸ƒ' as 7/10 instead of 7/7, leading to an incorrect final answer.
- Predict reason: Clear instruction, correct and complete reasoning, final answer matches.

**Instruction**

给出一步一步的推理过程，然后给出最终答案。在一个有 800 名学生的学校里，5/8 的学生是女生。七分之七的女孩和五分之二的男孩是小学生，其余的是中学生。有多少中学生？

**Output**

有 800 x 5 / 8 = 500 个女孩。所以，有 800 - 500 = 300 个男孩。有 500 x 7 / 10 = 350 名小学女生。因此，500 - 350 = 150 名女孩是中学生。小学有 300 x 2 / 5 = 120 个男孩。因此，300 - 120 = 180 男学生是中学生。因此，一共150名女生+180名男生=330名中学生。 最终答案：330。
