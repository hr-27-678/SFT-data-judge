# Original 1-5 Scorer Error Analysis Report (Greedy)

## Report Metadata

| Field | Value |
| --- | --- |
| Generated | 2026-05-01 17:32:43 |
| Report type | Error analysis |
| Project stage | Original 1-5 scorer |
| Report status | Canonical diagnostic for the 1-5 scorer |
| Evaluation mode | Greedy deterministic prediction |
| Current use | Diagnose why the project moved to binary scoring |

## Experiment Context

| Field | Value |
| --- | --- |
| Model family | Qwen3-4B LoRA scorer |
| Run name | `scorer_sft_1000_qwen3_4b_lora_e3` |
| Data version | `scorer_sft_1000` |
| Label space | score 1-5 plus verdict `keep` / `maybe` / `drop` |
| Splits analyzed | `valid_greedy` + `test_greedy` |
| Records | 208 |
| Related reports | `scorer_eval_valid_greedy_report.md`, `scorer_eval_test_greedy_report.md` |

## Metrics Summary

| Metric | Value |
| --- | --- |
| Records | 208 |
| Keep precision | 117/150 (78.00%) |
| Keep recall | 117/136 (86.03%) |
| Drop precision | 32/58 (55.17%) |
| Drop recall | 32/55 (58.18%) |
| Maybe recall | 0/17 (0.00%) |

## High-Risk Error Counts

| Category | Count | Why it matters |
| --- | ---: | --- |
| label drop -> predict keep | 23 | Bad samples would pass filtering. |
| label keep -> predict drop | 19 | Good samples would be thrown away. |
| label maybe missed | 17 | Boundary cases are not calibrated. |
| score error >= 2 | 57 | Model is not just off by one. |
| cot_zh score/verdict errors | 49 | Main weak source. |

## Split Breakdown

| Split | Records | Verdict acc | Score exact | Score +/-1 | drop->keep | keep->drop | maybe missed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| test_greedy | 104 | 69.23% | 56.73% | 70.19% | 14 | 10 | 8 |
| valid_greedy | 104 | 74.04% | 55.77% | 75.00% | 9 | 9 | 9 |

## Source Breakdown

| Source | Records | Verdict acc | Score exact | Score +/-1 | drop->keep | keep->drop | maybe missed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| cot_zh | 84 | 64.29% | 41.67% | 66.67% | 6 | 12 | 12 |
| finetome | 84 | 70.24% | 57.14% | 70.24% | 14 | 7 | 4 |
| openmath_reasoning | 40 | 90.00% | 85.00% | 90.00% | 3 | 0 | 1 |

## Key Findings

- The model has learned the output schema, but it is not yet a reliable teacher replacement.
- The dominant failure is calibration, not JSON formatting.
- `cot_zh` is the main bottleneck. It mixes translated entailment/math-style prompts, option wording noise, and terse answers; the student often over-trusts or over-penalizes these examples.
- `maybe` is not learned as a real middle class. It is treated as either keep or drop, so a 3-way scorer is currently poorly calibrated.
- For filtering, `keep` precision is usable for a first-pass high-quality pool, but `drop` recall is too low to safely remove all bad data.

## Recommended Next Actions

1. Do not tune hyperparameters first. The bottleneck is data coverage and label boundary calibration.
2. Add targeted teacher labels: more `cot_zh`, more `maybe`, and more `drop` cases that look superficially fluent.
3. Consider a two-stage label: first `usable/not_usable`, then optional 1-5 score. This can improve filtering utility even if exact scores remain noisy.
4. Add eval during training for the next run, so we can stop by validation verdict accuracy instead of only train loss.
5. For immediate use, treat predictions conservatively: only auto-keep high-confidence keep-style outputs after spot checks; do not auto-drop based only on this model yet.

## Representative Errors

## Teacher drop, model keep

### Teacher drop, model keep #1

- Split/source/id: `valid_greedy` / `openmath_reasoning` / `tj_openmath_reasoning_00107`
- Label: score `1`, verdict `drop`
- Predict: score `5`, verdict `keep`
- Score error: `4`
- Label reason: Output is truncated mid-sentence, missing the final answer and part of the solution, making it incomplete and unusable for training.
- Predict reason: Clear instruction, correct and complete solution with proper reasoning, matches expected answer.

**Instruction**

Evaluate the integral $$ \int_0^1 \frac{1+x^2}{1+x^2+x^4} \, dx. $$

**Output**

To evaluate the integral \[ \int_0^1 \frac{1+x^2}{1+x^2+x^4} \, dx, \] we start by factoring the denominator. Notice that \[ 1 + x^2 + x^4 = (x^2 - x + 1)(x^2 + x + 1). \] Thus, the integrand can be written as \[ \frac{1 + x^2}{(x^2 - x + 1)(x^2 + x + 1)}. \] We use partial fractions to decompose the integrand. Assume \[ \frac{1 + x^2}{(x^2 - x + 1)(x^2 + x + 1)} = \frac{Ax + B}{x^2 - x + 1} + \frac{Cx + D}{x^2 + x + 1}. \] Multiplying both sides by the denominator \((x^2 - x + 1)(x^2 + x + 1)\), we get \[ 1 + x^2 = (Ax + B)(x^2 + x + 1) + (Cx + D)(x^2 - x + 1). \] Expanding and combining like terms, we have \[ 1 + x^2 = (Ax^3 + Ax^2 + Ax + Bx^2 + Bx + B) + (Cx^3 - Cx^2 + Cx + Dx^2 - Dx +...

### Teacher drop, model keep #2

- Split/source/id: `valid_greedy` / `openmath_reasoning` / `tj_openmath_reasoning_00129`
- Label: score `1`, verdict `drop`
- Predict: score `5`, verdict `keep`
- Score error: `4`
- Label reason: The output derives a different integral than the target, missing the correct transformation to âˆ« 1/(âˆš3 sin z - cos z) dz.
- Predict reason: Clear instruction, correct and complete step-by-step reasoning, matches expected answer.

**Instruction**

How does one go from \[ I_{1}=\frac{1}{\sqrt{3}}\int\frac{1}{(t-1)\sqrt{\left(\frac{2t+1}{\sqrt{3}}\right)^{2}+1}}\ dt \] to \[ I_{1}=\int\frac{1}{\sqrt{3}\sin z-\cos z}\ dz =\frac{\sqrt{3}}{6}\ln\tan\left(\frac{z}{2}-\frac{\pi}{6}\right)+C \]?

**Output**

To solve the integral \( I_1 = \frac{1}{\sqrt{3}} \int \frac{1}{(t-1)\sqrt{\left( \frac{2t+1}{\sqrt{3}} \right)^2 + 1}} \, dt \) and transform it into the form \( I_1 = \int \frac{1}{\sqrt{3} \sin z - \cos z} \, dz \), we proceed as follows: 1. **Substitution \( u = \frac{2t + 1}{\sqrt{3}} \)**: \[ u = \frac{2t + 1}{\sqrt{3}} \implies t = \frac{u \sqrt{3} - 1}{2} \] Differentiating both sides with respect to \( t \): \[ du = \frac{2}{\sqrt{3}} \, dt \implies dt = \frac{\sqrt{3}}{2} \, du \] Substituting \( t \) and \( dt \) into the integral: \[ I_1 = \frac{1}{\sqrt{3}} \int \frac{1}{\left( \frac{u \sqrt{3} - 1}{2} - 1 \right) \sqrt{u^2 + 1}} \cdot \frac{\sqrt{3}}{2} \, du \] Simplifying ...

### Teacher drop, model keep #3

- Split/source/id: `test_greedy` / `cot_zh` / `tj_cot_zh_00220`
- Label: score `1`, verdict `drop`
- Predict: score `5`, verdict `keep`
- Score error: `4`
- Label reason: Output misinterprets 'ä¸ƒåˆ†ä¹‹ä¸ƒ' as 7/10 instead of 7/7, leading to an incorrect final answer.
- Predict reason: Clear instruction, correct answer with step-by-step reasoning, no issues.

**Instruction**

给出一步一步的推理过程，然后给出最终答案。在一个有 800 名学生的学校里，5/8 的学生是女生。七分之七的女孩和五分之二的男孩是小学生，其余的是中学生。有多少中学生？

**Output**

有 800 x 5 / 8 = 500 个女孩。所以，有 800 - 500 = 300 个男孩。有 500 x 7 / 10 = 350 名小学女生。因此，500 - 350 = 150 名女孩是中学生。小学有 300 x 2 / 5 = 120 个男孩。因此，300 - 120 = 180 男学生是中学生。因此，一共150名女生+180名男生=330名中学生。 最终答案：330。

### Teacher drop, model keep #4

- Split/source/id: `test_greedy` / `finetome` / `tj_finetome_00001`
- Label: score `1`, verdict `drop`
- Predict: score `5`, verdict `keep`
- Score error: `4`
- Label reason: Response is an incomplete Stata log snippet, missing requested analyses for multiple sample sizes, histogram, and pattern discussion; fails to address the extra part and lacks explanatory content.
- Predict reason: Clear instruction, correct and complete Stata code, no issues.

**Instruction**

Create a solution in Stata to the following: Statistics is all about large groups of numbers. When talking about a set of sampled data, most frequently used is their mean value and standard deviation (stddev). If you have set of data x i {\displaystyle x_{i}} where i = 1 , 2 , … , n {\displaystyle i=1,2,\ldots ,n\,\!} , the mean is x ¯ ≡ 1 n ∑ i x i {\displaystyle {\bar {x}}\equiv {1 \over n}\sum _{i}x_{i}} , while the stddev is σ ≡ 1 n ∑ i ( x i − x ¯ ) 2 {\displaystyle \sigma \equiv {\sqrt {{1 \over n}\sum _{i}\left(x_{i}-{\bar {x}}\right)^{2}}}} . When examining a large quantity of data, one often uses a histogram, which shows the counts of data samples falling into a prechosen set of ...

**Output**

. clear all . set obs 100000 number of observations (_N) was 0, now 100,000 . gen x=runiform() . summarize x Variable | Obs Mean Std. Dev. Min Max -------------+--------------------------------------------------------- x | 100,000 .4991874 .2885253 1.18e-06 .9999939 . hist x

## Teacher keep, model drop

### Teacher keep, model drop #1

- Split/source/id: `valid_greedy` / `cot_zh` / `tj_cot_zh_00255`
- Label: score `5`, verdict `keep`
- Predict: score `1`, verdict `drop`
- Score error: `-4`
- Label reason: Clear instruction, correct answer, and reasonable reasoning.
- Predict reason: Instruction contains a typo (学童 instead of 学生) and is irrelevant to the math reasoning task.

**Instruction**

下一个问题：如果政府发现你没有报税，他们会怎么做？\n选项：\n- 拿钱\n- 学童\n- 为公众服务\n- 原谅你\n- 拿钱 推理：

**Output**

税收是一个国家人民的法律义务。法律义务意味着必须遵守它。如果一个人不遵守法律义务，政府无论如何都会强加它。征税就是拿钱。答案是拿钱。

### Teacher keep, model drop #2

- Split/source/id: `valid_greedy` / `finetome` / `tj_finetome_00249`
- Label: score `5`, verdict `keep`
- Predict: score `1`, verdict `drop`
- Score error: `-4`
- Label reason: Clear instruction, correct and well-explained response, no issues.
- Predict reason: The output provides a plausible but incorrect explanation, failing to address the actual use of positional words in algebra and vector spaces.

**Instruction**

Why do we use positional words like "on," "under," and "over" to describe relationships in algebra and other mathematical concepts, such as vector spaces and operations?

**Output**

In algebra and mathematics, the use of positional words like "on," "under," and "over" to describe relationships is largely idiomatic, meaning it has evolved through common usage and tradition. These prepositions often serve to convey a sense of the relationship between mathematical objects or operations, but their choice is not based on strict logic or a single, precise meaning. For example, saying "V is a vector space over F" suggests that the vector space (V) is built using the field (F), with the field providing a basis for the operations. Similarly, "a group under multiplication" implies that the operation of multiplication is defined for the elements of the group. However, these int...

### Teacher keep, model drop #3

- Split/source/id: `valid_greedy` / `finetome` / `tj_finetome_00314`
- Label: score `5`, verdict `keep`
- Predict: score `1`, verdict `drop`
- Score error: `-4`
- Label reason: Clear instruction, relevant response, correct code solution, complete with reasoning, no corruption.
- Predict reason: The output contains a syntax error (missing closing parenthesis) and does not correctly solve the problem, making it unsuitable for training.

**Instruction**

Write Python code to solve the task: Fangy the little walrus, as all the modern walruses, loves to communicate via text messaging. One day he faced the following problem: When he sends large texts, they are split into parts each containing n characters (which is the size of one text message). Thus, whole sentences and words get split! Fangy did not like it, so he faced the task of breaking the text into minimal messages on his own so that no sentence were broken into pieces when it is sent and the number of text messages to be sent would be minimal. If two consecutive sentences are in different messages, the space between them can be ignored (Fangy does not write this space). The little w...

**Output**

Step 1: To solve this problem, we need to understand the concept of splitting a large text into minimal messages and the rules to follow when splitting the text. Step 2: We also need to consider the constraints such as the size of one message and the rules for splitting, such as not splitting a sentence into multiple messages. Step 3: The given solution takes the size of one message and the text as input and splits the text into minimal messages based on the rules. Step 4: We will implement the splitting process based on the rules and constraints, and handle the cases where splitting is impossible. ```python # Step 5: Import the re module for regular expression matching. import re # Step ...

### Teacher keep, model drop #4

- Split/source/id: `valid_greedy` / `finetome` / `tj_finetome_00397`
- Label: score `5`, verdict `keep`
- Predict: score `1`, verdict `drop`
- Score error: `-4`
- Label reason: The instruction is clear, the response is comprehensive, factually correct, well-structured, and contains no corruption or errors.
- Predict reason: The output contains a factual error: hot air balloons are not inflated with cold air using a fan; they are filled with cold air from the atmosphere, and the burner heats the air inside the envelope to create lift. This is a critical error in the explanation.

**Instruction**

Describe the basic principles of hot air ballooning, including how balloons are inflated, controlled, and navigated during flight.

**Output**

Hot air ballooning is a form of recreational aviation that involves flying large, lightweight balloons filled with hot air. The basic principles of hot air ballooning are based on the scientific concept that warm air rises in cooler air. Here are some key aspects of how balloons are inflated, controlled, and navigated during flight: 1. Inflation: Before takeoff, the balloon envelope (the fabric part of the balloon) is spread out on the ground and attached to the basket, which holds the passengers and pilot. A powerful fan is used to fill the envelope with cold air, causing it to inflate partially. Once the envelope has enough air inside, the burner, which is mounted above the basket, is i...

## Teacher maybe, model missed

### Teacher maybe, model missed #1

- Split/source/id: `valid_greedy` / `cot_zh` / `tj_cot_zh_00046`
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

- Split/source/id: `valid_greedy` / `cot_zh` / `tj_cot_zh_00191`
- Label: score `3`, verdict `maybe`
- Predict: score `5`, verdict `keep`
- Score error: `2`
- Label reason: Answer is plausible but reasoning is weak and does not properly justify the choice.
- Predict reason: Clear instruction, correct answer with valid reasoning, no issues.

**Instruction**

使用推理得出以下问题的答案： 圆珠笔在哪里写支票有用？\n选项：\n- 银行\n- 背包\n- 办公桌\n- 家\n- 书桌抽屉 推理过程：

**Output**

银行是从中提取资金的机构。支票用于提款。所以，最后的答案是银行。

### Teacher maybe, model missed #3

- Split/source/id: `valid_greedy` / `cot_zh` / `tj_cot_zh_00230`
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

- Split/source/id: `valid_greedy` / `cot_zh` / `tj_cot_zh_00304`
- Label: score `3`, verdict `maybe`
- Predict: score `5`, verdict `keep`
- Score error: `2`
- Label reason: The answer is plausible but debatable; the reasoning is acceptable but brief.
- Predict reason: Clear instruction, correct answer with reasonable reasoning, no issues.

**Instruction**

下一个问题：莉莉喜欢和平与安静，但她找不到任何她住的地方。她采取了严厉的措施，去了一个孤独的地方。她去哪儿了？\n选项：\n- 图书馆\n- 家\n- 山顶\n- 大海\n- 杂货店 推理：

**Output**

大海是一个宁静祥和的地方。一个人可以获得平静和完全的孤独。一个人可以在海上找到孤独。答案是大海。

## cot_zh mismatch

### cot_zh mismatch #1

- Split/source/id: `valid_greedy` / `cot_zh` / `tj_cot_zh_00255`
- Label: score `5`, verdict `keep`
- Predict: score `1`, verdict `drop`
- Score error: `-4`
- Label reason: Clear instruction, correct answer, and reasonable reasoning.
- Predict reason: Instruction contains a typo (学童 instead of 学生) and is irrelevant to the math reasoning task.

**Instruction**

下一个问题：如果政府发现你没有报税，他们会怎么做？\n选项：\n- 拿钱\n- 学童\n- 为公众服务\n- 原谅你\n- 拿钱 推理：

**Output**

税收是一个国家人民的法律义务。法律义务意味着必须遵守它。如果一个人不遵守法律义务，政府无论如何都会强加它。征税就是拿钱。答案是拿钱。

### cot_zh mismatch #2

- Split/source/id: `test_greedy` / `cot_zh` / `tj_cot_zh_00220`
- Label: score `1`, verdict `drop`
- Predict: score `5`, verdict `keep`
- Score error: `4`
- Label reason: Output misinterprets 'ä¸ƒåˆ†ä¹‹ä¸ƒ' as 7/10 instead of 7/7, leading to an incorrect final answer.
- Predict reason: Clear instruction, correct answer with step-by-step reasoning, no issues.

**Instruction**

给出一步一步的推理过程，然后给出最终答案。在一个有 800 名学生的学校里，5/8 的学生是女生。七分之七的女孩和五分之二的男孩是小学生，其余的是中学生。有多少中学生？

**Output**

有 800 x 5 / 8 = 500 个女孩。所以，有 800 - 500 = 300 个男孩。有 500 x 7 / 10 = 350 名小学女生。因此，500 - 350 = 150 名女孩是中学生。小学有 300 x 2 / 5 = 120 个男孩。因此，300 - 120 = 180 男学生是中学生。因此，一共150名女生+180名男生=330名中学生。 最终答案：330。

### cot_zh mismatch #3

- Split/source/id: `test_greedy` / `cot_zh` / `tj_cot_zh_00365`
- Label: score `5`, verdict `keep`
- Predict: score `1`, verdict `drop`
- Score error: `-4`
- Label reason: Clear instruction with correct answer and adequate reasoning.
- Predict reason: Instruction is a corrupted mix of news and movie plot; output incorrectly answers with a real-world president instead of a fictional one.

**Instruction**

白宫进行了报复，邮报和时报很快一起出现在最高法院，为他们关于发布该材料的权利的第一修正案辩护。与此同时，全国各地的报纸都与《华盛顿邮报》和《纽约时报》联手报道了这个故事。法院裁定 6 - 3 对报纸有利，证明了格雷厄姆的决定。尼克松要求禁止邮报进入白宫。一年后，在水门酒店的一位客人打电话抱怨有人使用手电筒后，保安弗兰克威尔斯发现水门大楼有人闯入。\n\n根据这段话，谁是电影中的总统？先给出意识流：

**Output**

文章中的相关句子是：尼克松要求禁止邮报进入白宫。 所以，最后的答案是尼克松。

### cot_zh mismatch #4

- Split/source/id: `valid_greedy` / `cot_zh` / `tj_cot_zh_00061`
- Label: score `4`, verdict `keep`
- Predict: score `1`, verdict `drop`
- Score error: `-3`
- Label reason: Correct answer with minor reasoning imprecision.
- Predict reason: The output is a generic statement and does not provide a valid reasoning or answer to the question, making it unsuitable for training.

**Instruction**

丹尼问： 前提：“一个穿绿色衬衫的人在他朋友的帮助下尝试后空翻。”\n假设：“一个穿绿色衬衫的人正在尝试做一个后空翻。”\n前提是否包含假设？ \n选项：\n- 是\n- 无法分辨\n- 否。 乐：好的，那我怎么解释一下才能回答呢？

**Output**

这个人要么得到朋友的帮助，要么独自尝试。 答案是：是的。
