"""Analyze the evergreen human-audit annotations.

Inputs:
- data/eval/evergreen_human_verify/sample.jsonl
- data/eval/evergreen_human_verify/annotation.md

Outputs:
- data/eval/evergreen_human_verify/human_labels.jsonl
- data/eval/evergreen_human_verify/human_audit_metrics.json
- reports/evergreen_human_verify_report.md
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SAMPLE = PROJECT_ROOT / "data" / "eval" / "evergreen_human_verify" / "sample.jsonl"
DEFAULT_ANNOTATION = PROJECT_ROOT / "data" / "eval" / "evergreen_human_verify" / "annotation.md"
DEFAULT_CANDIDATES = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test_merged_candidates.jsonl"
DEFAULT_LABELS_OUT = PROJECT_ROOT / "data" / "eval" / "evergreen_human_verify" / "human_labels.jsonl"
DEFAULT_METRICS_OUT = PROJECT_ROOT / "data" / "eval" / "evergreen_human_verify" / "human_audit_metrics.json"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "evergreen_human_verify_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze evergreen human verification annotations.")
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--annotation", type=Path, default=DEFAULT_ANNOTATION)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--labels-out", type=Path, default=DEFAULT_LABELS_OUT)
    parser.add_argument("--metrics-out", type=Path, default=DEFAULT_METRICS_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8-sig") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def normalize_verdict(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    text = text.replace("-", "_").replace(" ", "_")
    text = re.sub(r"[^a-z_]", "", text)
    if text in {"keep", "k"}:
        return "keep"
    if text in {"drop", "not_keep", "notkeep", "reject", "remove"}:
        return "not_keep"
    if text in {"maybe", "unsure", "uncertain"}:
        return "maybe"
    return text or None


def score_to_conservative_binary(score: Any) -> str | None:
    if score is None:
        return None
    try:
        s = int(str(score).strip())
    except ValueError:
        return None
    if s <= 3:
        return "not_keep"
    return "keep"


def score_to_confident_binary(score: Any) -> str | None:
    if score is None:
        return None
    try:
        s = int(str(score).strip())
    except ValueError:
        return None
    if s <= 2:
        return "not_keep"
    if s >= 4:
        return "keep"
    return "skip"


def parse_annotation_md(path: Path) -> dict[int, dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig")
    pattern = re.compile(
        r"## #(?P<rank>\d+).*?### YOUR ANNOTATION(?P<body>.*?)(?=\n---\n)",
        re.DOTALL,
    )
    out: dict[int, dict[str, Any]] = {}
    for match in pattern.finditer(text):
        rank = int(match.group("rank"))
        body = match.group("body")
        score_match = re.search(r"^\s*-\s*human_score:\s*(.*?)\s*$", body, re.MULTILINE)
        verdict_match = re.search(r"^\s*-\s*human_verdict:\s*(.*?)\s*$", body, re.MULTILINE)
        notes_match = re.search(r"^\s*-\s*human_notes:\s*(.*?)\s*$", body, re.MULTILINE)

        score: int | None = None
        if score_match:
            raw_score = score_match.group(1).strip()
            if raw_score:
                try:
                    score = int(raw_score)
                except ValueError:
                    score = None

        out[rank] = {
            "human_score": score,
            "human_verdict_raw": verdict_match.group(1).strip() if verdict_match else "",
            "human_verdict": normalize_verdict(verdict_match.group(1) if verdict_match else None),
            "human_notes": notes_match.group(1).strip() if notes_match else "",
        }
    return out


def infer_domain(record: dict[str, Any], candidate: dict[str, Any] | None) -> str:
    source = record.get("source")
    task_type = (candidate or {}).get("task_type")
    instruction = str(record.get("instruction") or "")
    output = str(record.get("output") or "")
    both = f"{instruction}\n{output}".lower()

    if source == "openmath_reasoning":
        return "math"

    code_markers = [
        "```python",
        "def ",
        "write a function",
        "python function",
        "python",
        "javascript",
        "java ",
        "c++",
        "programming",
        "opengl",
    ]
    if any(marker in both for marker in code_markers):
        return "code_or_programming"
    if source == "cot_zh":
        return "cot_zh_reasoning"
    if task_type == "math_reasoning":
        return "math_or_reasoning"
    return str(task_type or "general")


def pct(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(k): int(v) for k, v in sorted(counter.items(), key=lambda kv: str(kv[0]))}


def confusion(records: list[dict[str, Any]], teacher_key: str, human_key: str) -> dict[str, dict[str, int]]:
    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        teacher = record.get(teacher_key)
        human = record.get(human_key)
        if teacher is not None and human is not None:
            matrix[str(teacher)][str(human)] += 1
    return {k: counter_dict(v) for k, v in sorted(matrix.items())}


def table(rows: list[list[Any]]) -> list[str]:
    if not rows:
        return []
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    out = []
    for i, row in enumerate(rows):
        out.append("| " + " | ".join(str(cell).ljust(widths[j]) for j, cell in enumerate(row)) + " |")
        if i == 0:
            out.append("| " + " | ".join("-" * widths[j] for j in range(len(row))) + " |")
    return out


def main() -> None:
    args = parse_args()

    samples = read_jsonl(args.sample)
    candidates = {record["id"]: record for record in read_jsonl(args.candidates)}
    annotations = parse_annotation_md(args.annotation)

    merged: list[dict[str, Any]] = []
    parse_warnings: list[str] = []
    for sample in samples:
        rank = int(sample["rank"])
        ann = annotations.get(rank)
        if ann is None:
            parse_warnings.append(f"missing annotation block for rank {rank}")
            continue

        candidate = candidates.get(sample["id"])
        teacher_score = sample.get("teacher_score")
        human_score = ann.get("human_score")
        teacher_verdict = normalize_verdict(sample.get("teacher_verdict"))
        human_verdict = ann.get("human_verdict")

        row = {
            **sample,
            "task_type": (candidate or {}).get("task_type"),
            "domain": infer_domain(sample, candidate),
            "teacher_verdict_normalized": teacher_verdict,
            "human_score": human_score,
            "human_verdict": human_verdict,
            "human_verdict_raw": ann.get("human_verdict_raw"),
            "human_notes": ann.get("human_notes"),
            "teacher_binary_conservative": score_to_conservative_binary(teacher_score),
            "human_binary_conservative": score_to_conservative_binary(human_score),
            "teacher_binary_confident": score_to_confident_binary(teacher_score),
            "human_binary_confident": score_to_confident_binary(human_score),
        }
        if teacher_score is not None and human_score is not None:
            row["score_diff_human_minus_teacher"] = int(human_score) - int(teacher_score)
            row["score_abs_diff"] = abs(int(human_score) - int(teacher_score))
        else:
            row["score_diff_human_minus_teacher"] = None
            row["score_abs_diff"] = None

        merged.append(row)

    total = len(merged)
    completed = sum(1 for r in merged if r.get("human_score") is not None and r.get("human_verdict") is not None)

    exact_verdict_agree = sum(
        1
        for r in merged
        if r.get("teacher_verdict_normalized") is not None
        and r.get("human_verdict") is not None
        and r["teacher_verdict_normalized"] == r["human_verdict"]
    )
    exact_score_agree = sum(
        1
        for r in merged
        if r.get("teacher_score") is not None and r.get("human_score") is not None and int(r["teacher_score"]) == int(r["human_score"])
    )
    within_one_score = sum(
        1
        for r in merged
        if r.get("score_abs_diff") is not None and int(r["score_abs_diff"]) <= 1
    )
    cons_agree = sum(
        1
        for r in merged
        if r.get("teacher_binary_conservative") is not None
        and r.get("human_binary_conservative") is not None
        and r["teacher_binary_conservative"] == r["human_binary_conservative"]
    )
    conf_agree = sum(
        1
        for r in merged
        if r.get("teacher_binary_confident") is not None
        and r.get("human_binary_confident") is not None
        and r["teacher_binary_confident"] == r["human_binary_confident"]
    )

    diffs = [int(r["score_diff_human_minus_teacher"]) for r in merged if r.get("score_diff_human_minus_teacher") is not None]
    abs_diffs = [int(r["score_abs_diff"]) for r in merged if r.get("score_abs_diff") is not None]
    avg_diff = round(sum(diffs) / len(diffs), 3) if diffs else None
    avg_abs_diff = round(sum(abs_diffs) / len(abs_diffs), 3) if abs_diffs else None

    metrics = {
        "total_records": total,
        "completed_records": completed,
        "parse_warnings": parse_warnings,
        "source_counts": counter_dict(Counter(r.get("source") for r in merged)),
        "domain_counts": counter_dict(Counter(r.get("domain") for r in merged)),
        "clean_counts": counter_dict(Counter("clean" if r.get("is_clean") else "flagged" for r in merged)),
        "teacher_score_counts": counter_dict(Counter(r.get("teacher_score") for r in merged)),
        "human_score_counts": counter_dict(Counter(r.get("human_score") for r in merged)),
        "teacher_verdict_counts": counter_dict(Counter(r.get("teacher_verdict_normalized") for r in merged)),
        "human_verdict_counts": counter_dict(Counter(r.get("human_verdict") for r in merged)),
        "exact_verdict_agreement": {
            "count": exact_verdict_agree,
            "rate": pct(exact_verdict_agree, completed),
        },
        "exact_score_agreement": {
            "count": exact_score_agree,
            "rate": pct(exact_score_agree, completed),
        },
        "within_one_score_agreement": {
            "count": within_one_score,
            "rate": pct(within_one_score, completed),
        },
        "conservative_binary_agreement": {
            "count": cons_agree,
            "rate": pct(cons_agree, completed),
        },
        "confident_binary_agreement": {
            "count": conf_agree,
            "rate": pct(conf_agree, completed),
        },
        "score_diff_human_minus_teacher_avg": avg_diff,
        "score_abs_diff_avg": avg_abs_diff,
        "score_diff_counts": counter_dict(Counter(diffs)),
        "verdict_confusion_teacher_x_human": confusion(merged, "teacher_verdict_normalized", "human_verdict"),
        "conservative_binary_confusion_teacher_x_human": confusion(
            merged,
            "teacher_binary_conservative",
            "human_binary_conservative",
        ),
    }

    per_source: dict[str, Any] = {}
    for source, rows in defaultdict(list, {s: [r for r in merged if r.get("source") == s] for s in sorted({r.get("source") for r in merged})}).items():
        n = len(rows)
        per_source[str(source)] = {
            "n": n,
            "teacher_scores": counter_dict(Counter(r.get("teacher_score") for r in rows)),
            "human_scores": counter_dict(Counter(r.get("human_score") for r in rows)),
            "teacher_verdicts": counter_dict(Counter(r.get("teacher_verdict_normalized") for r in rows)),
            "human_verdicts": counter_dict(Counter(r.get("human_verdict") for r in rows)),
            "exact_verdict_agreement_rate": pct(
                sum(1 for r in rows if r.get("teacher_verdict_normalized") == r.get("human_verdict")),
                n,
            ),
            "conservative_binary_agreement_rate": pct(
                sum(1 for r in rows if r.get("teacher_binary_conservative") == r.get("human_binary_conservative")),
                n,
            ),
        }
    metrics["per_source"] = per_source

    per_domain: dict[str, Any] = {}
    for domain in sorted({str(r.get("domain")) for r in merged}):
        rows = [r for r in merged if str(r.get("domain")) == domain]
        n = len(rows)
        per_domain[domain] = {
            "n": n,
            "teacher_scores": counter_dict(Counter(r.get("teacher_score") for r in rows)),
            "human_scores": counter_dict(Counter(r.get("human_score") for r in rows)),
            "human_verdicts": counter_dict(Counter(r.get("human_verdict") for r in rows)),
            "human_not_keep": sum(1 for r in rows if r.get("human_verdict") == "not_keep"),
            "human_score_le_3": sum(1 for r in rows if r.get("human_score") is not None and int(r["human_score"]) <= 3),
        }
    metrics["per_domain"] = per_domain

    disagreements = [
        r
        for r in merged
        if r.get("teacher_verdict_normalized") is not None
        and r.get("human_verdict") is not None
        and r["teacher_verdict_normalized"] != r["human_verdict"]
    ]
    score_gap_records = sorted(
        [r for r in merged if r.get("score_abs_diff") is not None and int(r["score_abs_diff"]) >= 2],
        key=lambda r: (-int(r["score_abs_diff"]), int(r["rank"])),
    )

    inconsistent_human = []
    for r in merged:
        by_score = score_to_conservative_binary(r.get("human_score"))
        by_verdict = "keep" if r.get("human_verdict") == "keep" else "not_keep"
        if r.get("human_verdict") == "maybe":
            by_verdict = "not_keep"
        if by_score is not None and r.get("human_verdict") is not None and by_score != by_verdict:
            inconsistent_human.append(r)

    write_jsonl(args.labels_out, merged)
    args.metrics_out.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report: list[str] = [
        "# Evergreen Human Verification Report",
        "",
        "This report compares the 50-record human audit against the DeepSeek teacher labels.",
        "",
        "## Headline",
        "",
        f"- Completed human annotations: {completed}/{total}",
        f"- Exact 3-way verdict agreement: {exact_verdict_agree}/{completed} ({pct(exact_verdict_agree, completed):.1%})",
        f"- Exact score agreement: {exact_score_agree}/{completed} ({pct(exact_score_agree, completed):.1%})",
        f"- Within-one score agreement: {within_one_score}/{completed} ({pct(within_one_score, completed):.1%})",
        f"- Conservative binary agreement (score 1-3 -> not_keep, 4-5 -> keep): {cons_agree}/{completed} ({pct(cons_agree, completed):.1%})",
        f"- Average human-minus-teacher score: {avg_diff}",
        f"- Average absolute score gap: {avg_abs_diff}",
        "",
        "## Distributions",
        "",
    ]

    report.extend(table([
        ["Bucket", "Counts"],
        ["Source", metrics["source_counts"]],
        ["Domain heuristic", metrics["domain_counts"]],
        ["Clean status", metrics["clean_counts"]],
        ["Teacher score", metrics["teacher_score_counts"]],
        ["Human score", metrics["human_score_counts"]],
        ["Teacher verdict", metrics["teacher_verdict_counts"]],
        ["Human verdict", metrics["human_verdict_counts"]],
    ]))

    report.extend([
        "",
        "## Per Source",
        "",
    ])
    source_rows = [["Source", "N", "Teacher scores", "Human scores", "Human verdicts", "3-way agree", "Conservative binary agree"]]
    for source, values in per_source.items():
        source_rows.append([
            source,
            values["n"],
            values["teacher_scores"],
            values["human_scores"],
            values["human_verdicts"],
            f"{values['exact_verdict_agreement_rate']:.1%}",
            f"{values['conservative_binary_agreement_rate']:.1%}",
        ])
    report.extend(table(source_rows))

    report.extend([
        "",
        "## Per Domain Heuristic",
        "",
    ])
    domain_rows = [["Domain", "N", "Human scores", "Human verdicts", "Human score <=3", "Human not_keep"]]
    for domain, values in per_domain.items():
        domain_rows.append([
            domain,
            values["n"],
            values["human_scores"],
            values["human_verdicts"],
            values["human_score_le_3"],
            values["human_not_keep"],
        ])
    report.extend(table(domain_rows))

    report.extend([
        "",
        "## Teacher x Human Verdict Confusion",
        "",
        "Rows are teacher normalized verdicts; values are human normalized verdict counts.",
        "",
        "```json",
        json.dumps(metrics["verdict_confusion_teacher_x_human"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## High-Disagreement Records",
        "",
    ])

    if score_gap_records:
        gap_rows = [["Rank", "Source", "Clean", "Teacher", "Human", "Score gap", "Human notes"]]
        for r in score_gap_records:
            gap_rows.append([
                f"#{int(r['rank']):02d}",
                r.get("source"),
                "clean" if r.get("is_clean") else "flagged",
                f"{r.get('teacher_score')} / {r.get('teacher_verdict_normalized')}",
                f"{r.get('human_score')} / {r.get('human_verdict')}",
                r.get("score_diff_human_minus_teacher"),
                r.get("human_notes") or "",
            ])
        report.extend(table(gap_rows))
    else:
        report.append("No records had score gap >= 2.")

    report.extend([
        "",
        "## 3-Way Verdict Disagreements",
        "",
    ])
    if disagreements:
        disagreement_rows = [["Rank", "Source", "Teacher", "Human", "Human notes"]]
        for r in disagreements:
            disagreement_rows.append([
                f"#{int(r['rank']):02d}",
                r.get("source"),
                f"{r.get('teacher_score')} / {r.get('teacher_verdict_normalized')}",
                f"{r.get('human_score')} / {r.get('human_verdict')}",
                r.get("human_notes") or "",
            ])
        report.extend(table(disagreement_rows))
    else:
        report.append("No 3-way verdict disagreements.")

    report.extend([
        "",
        "## Human Label Consistency Notes",
        "",
    ])
    if inconsistent_human:
        report.append(
            "These records have a human score/verdict mismatch under the conservative score mapping "
            "(1-3 -> not_keep, 4-5 -> keep). They are worth normalizing before using the labels as training data."
        )
        report.append("")
        inconsistent_rows = [["Rank", "Source", "Human score", "Human verdict", "Human notes"]]
        for r in inconsistent_human:
            inconsistent_rows.append([
                f"#{int(r['rank']):02d}",
                r.get("source"),
                r.get("human_score"),
                r.get("human_verdict"),
                r.get("human_notes") or "",
            ])
        report.extend(table(inconsistent_rows))
    else:
        report.append("No score/verdict consistency issues under the conservative score mapping.")

    report.extend([
        "",
        "## Interpretation",
        "",
        "- The human audit does not show a large teacher-label failure rate overall; most disagreements are boundary moves between `maybe`, `keep`, and `not_keep` rather than complete reversals.",
        "- The audit sample is not adequate for estimating math/code false-negative rates: the math/code-heavy subset is overwhelmingly `keep`, and the openmath slice has no human `not_keep` examples.",
        "- For v5, do not rely on another generic active-learning round alone. Build a targeted math/code hard-negative queue with real-answer checks where possible.",
        "",
        "## Recommended Next Step",
        "",
        "Create a targeted teacher-labeling batch for math/code hard negatives:",
        "",
        "- openmath: mine expected-answer mismatches, missing final answers, invalid `\\boxed{}` answers, and reasoning/final-answer contradictions.",
        "- code: mine code-like prompts with syntax/runtime/test failures where lightweight checks are available, plus ambiguous API/spec mismatches for teacher review.",
        "- keep a balancing slice of math/code `keep` examples so the next scorer does not learn `math/code -> not_keep`.",
        "- keep this batch separate from evergreen test data; use it for v5 training, not for benchmark leakage.",
        "",
    ])

    if parse_warnings:
        report.extend([
            "## Parse Warnings",
            "",
            *[f"- {warning}" for warning in parse_warnings],
            "",
        ])

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(report), encoding="utf-8")

    print(f"wrote {len(merged)} records")
    print(f"  labels:  {args.labels_out.relative_to(PROJECT_ROOT)}")
    print(f"  metrics: {args.metrics_out.relative_to(PROJECT_ROOT)}")
    print(f"  report:  {args.report.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
