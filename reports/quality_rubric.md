# Phase 2 Quality Rubric

This rubric defines the teacher-label target for SFT data quality scoring.
The scorer should judge the quality of an `instruction` and `output` pair as
training data for supervised fine-tuning.

## Label Format

Teacher labels should be JSON with the following fields:

```json
{
  "overall_score": 4,
  "dimension_scores": {
    "instruction_clarity": 4,
    "response_relevance": 5,
    "factual_or_answer_correctness": 4,
    "reasoning_quality": 4,
    "completeness": 4,
    "data_integrity": 5
  },
  "verdict": "keep",
  "reason": "The answer is relevant and mostly correct with clear reasoning.",
  "major_issues": []
}
```

## Overall Score

| Score | Meaning | Recommended Action |
| --- | --- | --- |
| 5 | Excellent SFT sample. Clear instruction, correct and complete answer, intact data. | Keep |
| 4 | Good sample with minor issues that should not hurt training. | Keep |
| 3 | Usable but imperfect. Some missing steps, weak explanation, or minor uncertainty. | Maybe |
| 2 | Low-quality sample. Noticeable correctness, relevance, or formatting problems. | Drop or review |
| 1 | Harmful or unusable. Empty, wrong, incoherent, corrupted, or mismatched pair. | Drop |

## Dimensions

Each dimension uses a 1-5 score.

| Dimension | What To Judge |
| --- | --- |
| instruction_clarity | Whether the instruction/question is understandable and specific enough. |
| response_relevance | Whether the output directly answers the instruction. |
| factual_or_answer_correctness | Whether the final answer is correct. For math, use the provided expected answer if available. |
| reasoning_quality | Whether reasoning is coherent, non-contradictory, and useful for SFT. |
| completeness | Whether the answer fully solves the task rather than stopping early. |
| data_integrity | Whether the pair is intact and usable: no mojibake, severe repetition, truncation, broken extraction, or unreadable formatting. Natural user noise is allowed. |

## Robustness vs. Corruption

Do not penalize a sample just because the instruction is not perfectly clean.
Real SFT data should include some natural user noise so the downstream model
becomes robust.

Allowed noise:

- Typos or informal wording.
- Mixed Chinese/English terms.
- Extra spaces, mild punctuation issues, or casual phrasing.
- Slightly messy but understandable user questions.

Quality problems:

- Mojibake or unreadable encoding artifacts.
- Truncated instruction or output.
- Repeated punctuation/tokens that dominate the sample.
- Dataset extraction artifacts where instruction and output are mismatched.
- Output format so broken that the model would learn the wrong behavior.

In short: natural noisy input can still be high quality; corrupted training
pairs should score low.

Also, do not penalize a short output if the instruction explicitly asks for a
letter, label, option, number, or otherwise concise answer. Penalize short
outputs only when the task asks for explanation/reasoning and the answer is
clearly incomplete.

For reasoning prompts, do not require verbose hidden chain-of-thought. A concise
but valid explanation is acceptable. Penalize reasoning only when it is absent,
contradictory, mathematically invalid, or too shallow to support the answer.

## Source-Specific Notes

### CoT-ZH

- Prefer samples with correct final answers and concise, readable Chinese reasoning.
- Penalize examples where the instruction accidentally contains answer-like reasoning text.
- Penalize random "stream of consciousness" filler if it does not support the solution.
- Do not penalize short answers if the problem is simple and the final answer is clear.
- For multiple-choice commonsense or "which sentence is less sensible" tasks, judge the likely intended option. If there is no gold answer and the case is debatable, prefer score 3 over score 1.

### FineTome

- Treat the original `score` as metadata only; do not blindly copy it.
- Good samples should have instruction-following behavior and coherent responses.
- Penalize long outputs that are verbose but do not answer the prompt.
- Penalize multi-turn extraction artifacts if first-turn instruction/output is incomplete.

### OpenMathReasoning

- The hidden `<think>...</think>` block should not be used as the SFT target.
- Judge the retained user-visible solution, not the removed internal trace.
- User-visible reasoning can be long; length alone is not a quality problem.
- Use `expected_answer` when available to judge correctness.
- Use `pass_rate_72b_tir` as metadata about difficulty/reliability, not a direct quality label.
- Penalize correct final answers with severely flawed or contradictory reasoning.

## Verdict Mapping

| overall_score | verdict |
| --- | --- |
| 5 | keep |
| 4 | keep |
| 3 | maybe |
| 2 | drop |
| 1 | drop |

## Major Issue Tags

Use zero or more of these tags:

| Tag | Meaning |
| --- | --- |
| unclear_instruction | The instruction is confusing or underspecified. |
| irrelevant_response | The output does not answer the instruction. |
| wrong_answer | The answer appears incorrect. |
| weak_reasoning | Reasoning is missing, shallow, contradictory, or mathematically invalid. |
| incomplete_response | The answer is cut off or does not finish the task. |
| format_corruption | Mojibake, severe repetition, broken text, or unreadable formatting. |
| unsafe_or_sensitive | The sample contains content that should not be used for this training task. |
| extraction_artifact | The pair appears damaged by dataset conversion or first-turn extraction. |

## Important Rule

The teacher should judge whether the pair is useful as SFT training data, not
whether the answer style is personally preferred. A concise correct answer can
score high; a long polished answer can score low if it is wrong or irrelevant.
