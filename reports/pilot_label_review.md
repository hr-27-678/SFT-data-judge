# Pilot Label Review

Reviewed file: `data/labeled/teacher_judge/pilot_teacher_labels.jsonl`

## Validation

| Check | Result |
| --- | --- |
| Records | 60 |
| Null labels | 0 |
| Rows with validation errors | 0 |
| Source balance | 20 CoT-ZH / 20 FineTome / 20 OpenMathReasoning |

## Score Distribution

| Score | Count |
| --- | ---: |
| 5 | 36 |
| 4 | 5 |
| 3 | 4 |
| 2 | 8 |
| 1 | 7 |

| Verdict | Count |
| --- | ---: |
| keep | 41 |
| maybe | 4 |
| drop | 15 |

## Source Notes

| Source | Observation |
| --- | --- |
| CoT-ZH | Teacher catches wrong commonsense answers, but can be slightly too harsh when a correct entailment answer is concise rather than detailed. |
| FineTome | Labels look mostly reasonable; several code/math responses are correctly marked wrong despite rule-clean status. |
| OpenMathReasoning | Corrupted exclamation-mark outputs are correctly dropped; duplicate but correct math samples can still score high, which is expected because duplication is a data selection issue rather than single-sample quality. |

## Prompt Adjustment Made

The prompt and rubric were updated after review:

- Multiple-choice commonsense cases should not be marked wrong only because another interpretation is possible.
- Concise but valid reasoning should not be penalized for lacking verbose chain-of-thought.
- Short outputs are acceptable when the instruction asks for an option, label, number, or concise answer.

## Recommendation

Run a second 10-20 sample pilot after the prompt adjustment if budget allows.
If the distribution remains stable, proceed to full 3,600-candidate labeling.
