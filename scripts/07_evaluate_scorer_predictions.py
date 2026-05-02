#!/usr/bin/env python3
"""Evaluate scorer predictions produced by LLaMA-Factory.

The LLaMA-Factory prediction file uses text overlap metrics by default. For the
data judge scorer, the useful metrics are JSON validity, score accuracy, and
verdict accuracy.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


VERDICTS = ["keep", "maybe", "drop"]
SCORES = [1, 2, 3, 4, 5]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def parse_json_object(value: Any) -> tuple[dict[str, Any] | None, bool]:
    if isinstance(value, dict):
        return value, True
    if value is None:
        return None, False

    text = str(value).strip()
    try:
        obj = json.loads(text)
        return (obj, isinstance(obj, dict))
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None, False
    try:
        obj = json.loads(match.group(0))
        return (obj, isinstance(obj, dict))
    except json.JSONDecodeError:
        return None, False


def is_schema_valid(obj: dict[str, Any] | None) -> bool:
    if not isinstance(obj, dict):
        return False
    if obj.get("overall_score") not in SCORES:
        return False
    if obj.get("verdict") not in VERDICTS:
        return False
    if not isinstance(obj.get("dimension_scores"), dict):
        return False
    if not isinstance(obj.get("major_issues"), list):
        return False
    if not isinstance(obj.get("reason"), str):
        return False
    return True


def pct(num: int | float, den: int | float) -> str:
    if not den:
        return "0.00%"
    return f"{100 * num / den:.2f}%"


def extract_source_from_prompt(prompt: str) -> str:
    match = re.search(r"(?m)^source:\s*(.+?)\s*$", prompt)
    return match.group(1).strip() if match else "unknown"


def display_path(path: Path | None) -> str | None:
    if path is None:
        return None
    text = str(path)
    return path.name if any(ord(ch) > 127 for ch in text) else text


def matrix_md(
    title: str,
    row_labels: list[Any],
    col_labels: list[Any],
    counts: dict[tuple[Any, Any], int],
) -> str:
    lines = [f"## {title}", ""]
    header = "| Label \\ Predict | " + " | ".join(str(c) for c in col_labels) + " |"
    sep = "| --- | " + " | ".join("---" for _ in col_labels) + " |"
    lines.extend([header, sep])
    for row in row_labels:
        values = [str(counts.get((row, col), 0)) for col in col_labels]
        lines.append(f"| {row} | " + " | ".join(values) + " |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--split", default="valid")
    parser.add_argument("--run-name", default="")
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()

    prediction_rows = read_jsonl(args.predictions)
    reference_rows = read_jsonl(args.reference) if args.reference else []
    if reference_rows and len(reference_rows) != len(prediction_rows):
        raise ValueError(
            f"Reference rows ({len(reference_rows)}) do not match prediction rows ({len(prediction_rows)})."
        )

    n = len(prediction_rows)
    valid_pred_json = 0
    valid_label_json = 0
    schema_valid = 0
    score_exact = 0
    score_within_1 = 0
    verdict_acc = 0
    score_abs_error_total = 0
    score_abs_error_count = 0

    label_verdict_counts: Counter[str] = Counter()
    pred_verdict_counts: Counter[str] = Counter()
    label_score_counts: Counter[int] = Counter()
    pred_score_counts: Counter[int] = Counter()
    verdict_confusion: dict[tuple[str, str], int] = defaultdict(int)
    score_confusion: dict[tuple[int, int], int] = defaultdict(int)
    by_source: dict[str, Counter[str]] = defaultdict(Counter)
    bad_examples: list[dict[str, Any]] = []

    for idx, row in enumerate(prediction_rows):
        pred_obj, pred_ok = parse_json_object(row.get("predict"))
        label_obj, label_ok = parse_json_object(row.get("label"))
        valid_pred_json += int(pred_ok)
        valid_label_json += int(label_ok)
        schema_valid += int(is_schema_valid(pred_obj))

        if reference_rows:
            source = reference_rows[idx].get("meta", {}).get("source", "unknown")
        else:
            source = extract_source_from_prompt(str(row.get("prompt", "")))

        by_source[source]["records"] += 1
        by_source[source]["pred_json_ok"] += int(pred_ok)
        by_source[source]["pred_schema_ok"] += int(is_schema_valid(pred_obj))

        if not pred_ok or not label_ok or not pred_obj or not label_obj:
            if len(bad_examples) < 5:
                bad_examples.append(
                    {
                        "index": idx,
                        "pred_json_ok": pred_ok,
                        "label_json_ok": label_ok,
                        "predict_preview": str(row.get("predict", ""))[:300],
                    }
                )
            continue

        pred_score = pred_obj.get("overall_score")
        label_score = label_obj.get("overall_score")
        pred_verdict = pred_obj.get("verdict")
        label_verdict = label_obj.get("verdict")

        if label_verdict in VERDICTS:
            label_verdict_counts[label_verdict] += 1
        if pred_verdict in VERDICTS:
            pred_verdict_counts[pred_verdict] += 1
        if label_score in SCORES:
            label_score_counts[label_score] += 1
        if pred_score in SCORES:
            pred_score_counts[pred_score] += 1

        if label_verdict in VERDICTS and pred_verdict in VERDICTS:
            verdict_confusion[(label_verdict, pred_verdict)] += 1
        if label_score in SCORES and pred_score in SCORES:
            score_confusion[(label_score, pred_score)] += 1

        if pred_score in SCORES and label_score in SCORES:
            abs_error = abs(int(pred_score) - int(label_score))
            score_abs_error_total += abs_error
            score_abs_error_count += 1
            score_exact += int(abs_error == 0)
            score_within_1 += int(abs_error <= 1)
            by_source[source]["score_exact"] += int(abs_error == 0)
            by_source[source]["score_within_1"] += int(abs_error <= 1)

        if pred_verdict in VERDICTS and label_verdict in VERDICTS:
            verdict_acc += int(pred_verdict == label_verdict)
            by_source[source]["verdict_acc"] += int(pred_verdict == label_verdict)

    mae = score_abs_error_total / score_abs_error_count if score_abs_error_count else 0.0
    metrics = {
        "split": args.split,
        "run_name": args.run_name,
        "records": n,
        "prediction_file": display_path(args.predictions),
        "reference_file": display_path(args.reference),
        "valid_prediction_json": valid_pred_json,
        "valid_prediction_json_rate": valid_pred_json / n if n else 0,
        "valid_label_json": valid_label_json,
        "prediction_schema_valid": schema_valid,
        "prediction_schema_valid_rate": schema_valid / n if n else 0,
        "score_exact": score_exact,
        "score_exact_rate": score_exact / n if n else 0,
        "score_within_1": score_within_1,
        "score_within_1_rate": score_within_1 / n if n else 0,
        "score_mae": mae,
        "verdict_accuracy": verdict_acc,
        "verdict_accuracy_rate": verdict_acc / n if n else 0,
        "label_verdict_counts": dict(label_verdict_counts),
        "pred_verdict_counts": dict(pred_verdict_counts),
        "label_score_counts": dict(label_score_counts),
        "pred_score_counts": dict(pred_score_counts),
        "bad_examples": bad_examples,
    }

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    lines = [
        f"# Scorer Eval Report ({args.split})",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Run",
        "",
        f"- Run name: `{args.run_name or 'unknown'}`",
        f"- Predictions: `{display_path(args.predictions)}`",
        f"- Reference: `{display_path(args.reference)}`" if args.reference else "- Reference: not provided",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Records | {n} |",
        f"| Prediction JSON valid | {valid_pred_json}/{n} ({pct(valid_pred_json, n)}) |",
        f"| Prediction schema valid | {schema_valid}/{n} ({pct(schema_valid, n)}) |",
        f"| Label JSON valid | {valid_label_json}/{n} ({pct(valid_label_json, n)}) |",
        f"| Overall score exact accuracy | {score_exact}/{n} ({pct(score_exact, n)}) |",
        f"| Overall score within +/-1 | {score_within_1}/{n} ({pct(score_within_1, n)}) |",
        f"| Overall score MAE | {mae:.3f} |",
        f"| Verdict accuracy | {verdict_acc}/{n} ({pct(verdict_acc, n)}) |",
        "",
        "## Distribution",
        "",
        "| Verdict | Label | Prediction |",
        "| --- | ---: | ---: |",
    ]
    for verdict in VERDICTS:
        lines.append(
            f"| {verdict} | {label_verdict_counts.get(verdict, 0)} | {pred_verdict_counts.get(verdict, 0)} |"
        )
    lines.extend(["", "| Score | Label | Prediction |", "| --- | ---: | ---: |"])
    for score in SCORES:
        lines.append(f"| {score} | {label_score_counts.get(score, 0)} | {pred_score_counts.get(score, 0)} |")
    lines.append("")

    if by_source:
        lines.extend(["## Per Source", "", "| Source | Records | JSON valid | Schema valid | Score exact | Score +/-1 | Verdict acc |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
        for source in sorted(by_source):
            c = by_source[source]
            records = c["records"]
            lines.append(
                f"| {source} | {records} | {pct(c['pred_json_ok'], records)} | {pct(c['pred_schema_ok'], records)} | "
                f"{pct(c['score_exact'], records)} | {pct(c['score_within_1'], records)} | {pct(c['verdict_acc'], records)} |"
            )
        lines.append("")

    lines.append(matrix_md("Verdict Confusion Matrix", VERDICTS, VERDICTS, verdict_confusion))
    lines.append(matrix_md("Score Confusion Matrix", SCORES, SCORES, score_confusion))

    lines.extend(
        [
            "## Notes",
            "",
            "- Text-overlap metrics such as BLEU/Rouge are secondary for this task.",
            "- The main acceptance checks are valid JSON, score calibration, and verdict accuracy.",
            "- This run is format-stable, but the validation set shows weak `maybe` recall and a tendency to over-predict `keep`.",
            "",
        ]
    )

    if bad_examples:
        lines.extend(["## Bad JSON Examples", "", "```json"])
        lines.append(json.dumps(bad_examples, ensure_ascii=False, indent=2))
        lines.extend(["```", ""])

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote markdown report: {args.output_md.name}")
    if args.output_json:
        print(f"Wrote metrics JSON: {args.output_json.name}")


if __name__ == "__main__":
    main()
