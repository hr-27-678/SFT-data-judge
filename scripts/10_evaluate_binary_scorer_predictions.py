#!/usr/bin/env python3
"""Evaluate binary scorer predictions produced by LLaMA-Factory."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


VERDICTS = ["keep", "not_keep"]


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
    return isinstance(obj, dict) and obj.get("verdict") in VERDICTS


def pct(num: int | float, den: int | float) -> str:
    return f"{100 * num / den:.2f}%" if den else "0.00%"


def f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def matrix_md(counts: Counter[tuple[str, str]]) -> str:
    lines = [
        "## Confusion Matrix",
        "",
        "| Label \\ Predict | keep | not_keep |",
        "| --- | ---: | ---: |",
    ]
    for label in VERDICTS:
        lines.append(f"| {label} | {counts.get((label, 'keep'), 0)} | {counts.get((label, 'not_keep'), 0)} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--split", default="valid")
    parser.add_argument("--run-name", default="")
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()

    pred_rows = read_jsonl(args.predictions)
    ref_rows = read_jsonl(args.reference)
    if len(pred_rows) != len(ref_rows):
        raise ValueError(f"Prediction rows ({len(pred_rows)}) != reference rows ({len(ref_rows)}).")

    n = len(pred_rows)
    valid_pred_json = 0
    valid_label_json = 0
    schema_valid = 0
    accuracy = 0
    pred_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    confusion: Counter[tuple[str, str]] = Counter()
    by_source: dict[str, Counter[str]] = defaultdict(Counter)
    bad_examples: list[dict[str, Any]] = []

    for idx, (pred_row, ref_row) in enumerate(zip(pred_rows, ref_rows)):
        pred_obj, pred_ok = parse_json_object(pred_row.get("predict"))
        label_obj, label_ok = parse_json_object(pred_row.get("label"))
        if not label_ok:
            label_obj, label_ok = parse_json_object(ref_row.get("output"))

        source = ref_row.get("meta", {}).get("source", "unknown")
        valid_pred_json += int(pred_ok)
        valid_label_json += int(label_ok)
        schema_valid += int(is_schema_valid(pred_obj))
        by_source[source]["records"] += 1
        by_source[source]["pred_json_ok"] += int(pred_ok)
        by_source[source]["schema_ok"] += int(is_schema_valid(pred_obj))

        if not pred_ok or not label_ok or not pred_obj or not label_obj:
            if len(bad_examples) < 5:
                bad_examples.append(
                    {
                        "index": idx,
                        "pred_json_ok": pred_ok,
                        "label_json_ok": label_ok,
                        "predict_preview": str(pred_row.get("predict", ""))[:300],
                    }
                )
            continue

        pred_verdict = pred_obj.get("verdict")
        label_verdict = label_obj.get("verdict")
        if label_verdict in VERDICTS:
            label_counts[label_verdict] += 1
        if pred_verdict in VERDICTS:
            pred_counts[pred_verdict] += 1

        if label_verdict in VERDICTS and pred_verdict in VERDICTS:
            confusion[(label_verdict, pred_verdict)] += 1
            accuracy += int(label_verdict == pred_verdict)
            by_source[source]["accuracy"] += int(label_verdict == pred_verdict)

    keep_tp = confusion[("keep", "keep")]
    keep_fp = confusion[("not_keep", "keep")]
    keep_fn = confusion[("keep", "not_keep")]
    nk_tp = confusion[("not_keep", "not_keep")]
    nk_fp = confusion[("keep", "not_keep")]
    nk_fn = confusion[("not_keep", "keep")]

    keep_precision = keep_tp / (keep_tp + keep_fp) if keep_tp + keep_fp else 0.0
    keep_recall = keep_tp / (keep_tp + keep_fn) if keep_tp + keep_fn else 0.0
    nk_precision = nk_tp / (nk_tp + nk_fp) if nk_tp + nk_fp else 0.0
    nk_recall = nk_tp / (nk_tp + nk_fn) if nk_tp + nk_fn else 0.0

    metrics = {
        "split": args.split,
        "run_name": args.run_name,
        "records": n,
        "valid_prediction_json": valid_pred_json,
        "valid_prediction_json_rate": valid_pred_json / n if n else 0,
        "prediction_schema_valid": schema_valid,
        "prediction_schema_valid_rate": schema_valid / n if n else 0,
        "valid_label_json": valid_label_json,
        "accuracy": accuracy,
        "accuracy_rate": accuracy / n if n else 0,
        "keep_precision": keep_precision,
        "keep_recall": keep_recall,
        "keep_f1": f1(keep_precision, keep_recall),
        "not_keep_precision": nk_precision,
        "not_keep_recall": nk_recall,
        "not_keep_f1": f1(nk_precision, nk_recall),
        "label_counts": dict(label_counts),
        "prediction_counts": dict(pred_counts),
    }
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# Binary Scorer Eval Report ({args.split})",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Run",
        "",
        f"- Run name: `{args.run_name or 'unknown'}`",
        f"- Predictions: `{args.predictions}`",
        f"- Reference: `{args.reference}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Records | {n} |",
        f"| Prediction JSON valid | {valid_pred_json}/{n} ({pct(valid_pred_json, n)}) |",
        f"| Prediction schema valid | {schema_valid}/{n} ({pct(schema_valid, n)}) |",
        f"| Label JSON valid | {valid_label_json}/{n} ({pct(valid_label_json, n)}) |",
        f"| Accuracy | {accuracy}/{n} ({pct(accuracy, n)}) |",
        f"| Keep precision | {keep_tp}/{keep_tp + keep_fp} ({pct(keep_tp, keep_tp + keep_fp)}) |",
        f"| Keep recall | {keep_tp}/{keep_tp + keep_fn} ({pct(keep_tp, keep_tp + keep_fn)}) |",
        f"| Keep F1 | {f1(keep_precision, keep_recall):.3f} |",
        f"| Not-keep precision | {nk_tp}/{nk_tp + nk_fp} ({pct(nk_tp, nk_tp + nk_fp)}) |",
        f"| Not-keep recall | {nk_tp}/{nk_tp + nk_fn} ({pct(nk_tp, nk_tp + nk_fn)}) |",
        f"| Not-keep F1 | {f1(nk_precision, nk_recall):.3f} |",
        "",
        "## Distribution",
        "",
        "| Verdict | Label | Prediction |",
        "| --- | ---: | ---: |",
    ]
    for verdict in VERDICTS:
        lines.append(f"| {verdict} | {label_counts.get(verdict, 0)} | {pred_counts.get(verdict, 0)} |")

    lines.extend(["", "## Per Source", "", "| Source | Records | JSON valid | Schema valid | Accuracy |", "| --- | ---: | ---: | ---: | ---: |"])
    for source in sorted(by_source):
        c = by_source[source]
        records = c["records"]
        lines.append(
            f"| {source} | {records} | {pct(c['pred_json_ok'], records)} | {pct(c['schema_ok'], records)} | {pct(c['accuracy'], records)} |"
        )
    lines.extend(["", matrix_md(confusion)])

    if bad_examples:
        lines.extend(["## Bad JSON Examples", "", "```json", json.dumps(bad_examples, ensure_ascii=False, indent=2), "```", ""])

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote markdown report: {args.output_md.name}")
    if args.output_json:
        print(f"Wrote metrics JSON: {args.output_json.name}")


if __name__ == "__main__":
    main()
