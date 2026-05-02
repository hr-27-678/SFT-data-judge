#!/usr/bin/env python3
"""Analyze scorer prediction errors across validation/test splits."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


VERDICTS = ["keep", "maybe", "drop"]
SCORES = [1, 2, 3, 4, 5]


@dataclass
class CaseSpec:
    split: str
    predictions: Path
    reference: Path


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


def parse_json_object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if value is None:
        return None
    text = str(value).strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None
    try:
        obj = json.loads(match.group(0))
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


def extract_blocks(instruction_text: str) -> tuple[str, str]:
    instruction = ""
    output = ""
    inst_match = re.search(r"(?s)\ninstruction:\n(.*?)\n\noutput:\n", instruction_text)
    out_match = re.search(r"(?s)\noutput:\n(.*)$", instruction_text)
    if inst_match:
        instruction = inst_match.group(1).strip()
    if out_match:
        output = out_match.group(1).strip()
    return instruction, output


def short(text: str, limit: int = 360) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def pct(num: int | float, den: int | float) -> str:
    return f"{100 * num / den:.2f}%" if den else "0.00%"


def verdict_from_score(score: Any) -> str | None:
    if score in (4, 5):
        return "keep"
    if score == 3:
        return "maybe"
    if score in (1, 2):
        return "drop"
    return None


def load_cases(specs: list[CaseSpec]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for spec in specs:
        pred_rows = read_jsonl(spec.predictions)
        ref_rows = read_jsonl(spec.reference)
        if len(pred_rows) != len(ref_rows):
            raise ValueError(
                f"{spec.split}: predictions ({len(pred_rows)}) and reference ({len(ref_rows)}) differ."
            )
        for idx, (pred_row, ref_row) in enumerate(zip(pred_rows, ref_rows)):
            pred = parse_json_object(pred_row.get("predict"))
            label = parse_json_object(pred_row.get("label")) or parse_json_object(ref_row.get("output"))
            instruction, response = extract_blocks(ref_row.get("instruction", ""))
            meta = ref_row.get("meta", {})
            label_score = label.get("overall_score") if label else None
            pred_score = pred.get("overall_score") if pred else None
            label_verdict = label.get("verdict") if label else None
            pred_verdict = pred.get("verdict") if pred else None
            if label_verdict not in VERDICTS:
                label_verdict = verdict_from_score(label_score)
            if pred_verdict not in VERDICTS:
                pred_verdict = verdict_from_score(pred_score)
            score_error = None
            if label_score in SCORES and pred_score in SCORES:
                score_error = int(pred_score) - int(label_score)
            records.append(
                {
                    "split": spec.split,
                    "index": idx,
                    "id": meta.get("id", ""),
                    "teacher_sample_id": meta.get("teacher_sample_id", ""),
                    "source": meta.get("source", "unknown"),
                    "clean_status": meta.get("clean_status", ""),
                    "label": label,
                    "pred": pred,
                    "label_score": label_score,
                    "pred_score": pred_score,
                    "label_verdict": label_verdict,
                    "pred_verdict": pred_verdict,
                    "score_error": score_error,
                    "instruction": instruction,
                    "response": response,
                }
            )
    return records


def add_example(lines: list[str], title: str, record: dict[str, Any]) -> None:
    label = record["label"] or {}
    pred = record["pred"] or {}
    lines.extend(
        [
            f"### {title}",
            "",
            f"- Split/source/id: `{record['split']}` / `{record['source']}` / `{record['teacher_sample_id'] or record['id']}`",
            f"- Label: score `{record['label_score']}`, verdict `{record['label_verdict']}`",
            f"- Predict: score `{record['pred_score']}`, verdict `{record['pred_verdict']}`",
            f"- Score error: `{record['score_error']}`",
            f"- Label reason: {short(str(label.get('reason', '')))}",
            f"- Predict reason: {short(str(pred.get('reason', '')))}",
            "",
            "**Instruction**",
            "",
            short(record["instruction"], 700),
            "",
            "**Output**",
            "",
            short(record["response"], 700),
            "",
        ]
    )


def build_report(records: list[dict[str, Any]], output_md: Path, output_json: Path | None) -> None:
    total = len(records)
    by_source: dict[str, Counter[str]] = defaultdict(Counter)
    by_split: dict[str, Counter[str]] = defaultdict(Counter)
    verdict_confusion: Counter[tuple[str, str]] = Counter()
    score_confusion: Counter[tuple[int, int]] = Counter()
    categories: dict[str, list[dict[str, Any]]] = {
        "drop_pred_keep": [],
        "keep_pred_drop": [],
        "maybe_missed": [],
        "score_error_ge_2": [],
        "cot_zh_errors": [],
    }

    pred_keep = label_keep = true_keep_pred_keep = 0
    pred_drop = label_drop = true_drop_pred_drop = 0
    label_maybe = true_maybe_pred_maybe = 0

    for rec in records:
        source = rec["source"]
        split = rec["split"]
        lv = rec["label_verdict"]
        pv = rec["pred_verdict"]
        ls = rec["label_score"]
        ps = rec["pred_score"]
        score_error = rec["score_error"]

        for bucket in (by_source[source], by_split[split]):
            bucket["records"] += 1
            bucket["verdict_correct"] += int(lv == pv)
            bucket["score_exact"] += int(ls == ps)
            bucket["score_within_1"] += int(score_error is not None and abs(score_error) <= 1)
            bucket["drop_pred_keep"] += int(lv == "drop" and pv == "keep")
            bucket["keep_pred_drop"] += int(lv == "keep" and pv == "drop")
            bucket["maybe_missed"] += int(lv == "maybe" and pv != "maybe")

        if lv in VERDICTS and pv in VERDICTS:
            verdict_confusion[(lv, pv)] += 1
        if ls in SCORES and ps in SCORES:
            score_confusion[(ls, ps)] += 1

        pred_keep += int(pv == "keep")
        label_keep += int(lv == "keep")
        true_keep_pred_keep += int(lv == "keep" and pv == "keep")
        pred_drop += int(pv == "drop")
        label_drop += int(lv == "drop")
        true_drop_pred_drop += int(lv == "drop" and pv == "drop")
        label_maybe += int(lv == "maybe")
        true_maybe_pred_maybe += int(lv == "maybe" and pv == "maybe")

        if lv == "drop" and pv == "keep":
            categories["drop_pred_keep"].append(rec)
        if lv == "keep" and pv == "drop":
            categories["keep_pred_drop"].append(rec)
        if lv == "maybe" and pv != "maybe":
            categories["maybe_missed"].append(rec)
        if score_error is not None and abs(score_error) >= 2:
            categories["score_error_ge_2"].append(rec)
        if source == "cot_zh" and (lv != pv or ls != ps):
            categories["cot_zh_errors"].append(rec)

    metrics = {
        "records": total,
        "keep_precision": true_keep_pred_keep / pred_keep if pred_keep else 0,
        "keep_recall": true_keep_pred_keep / label_keep if label_keep else 0,
        "drop_precision": true_drop_pred_drop / pred_drop if pred_drop else 0,
        "drop_recall": true_drop_pred_drop / label_drop if label_drop else 0,
        "maybe_recall": true_maybe_pred_maybe / label_maybe if label_maybe else 0,
        "category_counts": {k: len(v) for k, v in categories.items()},
    }
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Scorer Error Analysis",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Records | {total} |",
        f"| Keep precision | {true_keep_pred_keep}/{pred_keep} ({pct(true_keep_pred_keep, pred_keep)}) |",
        f"| Keep recall | {true_keep_pred_keep}/{label_keep} ({pct(true_keep_pred_keep, label_keep)}) |",
        f"| Drop precision | {true_drop_pred_drop}/{pred_drop} ({pct(true_drop_pred_drop, pred_drop)}) |",
        f"| Drop recall | {true_drop_pred_drop}/{label_drop} ({pct(true_drop_pred_drop, label_drop)}) |",
        f"| Maybe recall | {true_maybe_pred_maybe}/{label_maybe} ({pct(true_maybe_pred_maybe, label_maybe)}) |",
        "",
        "## High-Risk Error Counts",
        "",
        "| Category | Count | Why it matters |",
        "| --- | ---: | --- |",
        f"| label drop -> predict keep | {len(categories['drop_pred_keep'])} | Bad samples would pass filtering. |",
        f"| label keep -> predict drop | {len(categories['keep_pred_drop'])} | Good samples would be thrown away. |",
        f"| label maybe missed | {len(categories['maybe_missed'])} | Boundary cases are not calibrated. |",
        f"| score error >= 2 | {len(categories['score_error_ge_2'])} | Model is not just off by one. |",
        f"| cot_zh score/verdict errors | {len(categories['cot_zh_errors'])} | Main weak source. |",
        "",
        "## By Split",
        "",
        "| Split | Records | Verdict acc | Score exact | Score +/-1 | drop->keep | keep->drop | maybe missed |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for split in sorted(by_split):
        c = by_split[split]
        n = c["records"]
        lines.append(
            f"| {split} | {n} | {pct(c['verdict_correct'], n)} | {pct(c['score_exact'], n)} | "
            f"{pct(c['score_within_1'], n)} | {c['drop_pred_keep']} | {c['keep_pred_drop']} | {c['maybe_missed']} |"
        )

    lines.extend(
        [
            "",
            "## By Source",
            "",
            "| Source | Records | Verdict acc | Score exact | Score +/-1 | drop->keep | keep->drop | maybe missed |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for source in sorted(by_source):
        c = by_source[source]
        n = c["records"]
        lines.append(
            f"| {source} | {n} | {pct(c['verdict_correct'], n)} | {pct(c['score_exact'], n)} | "
            f"{pct(c['score_within_1'], n)} | {c['drop_pred_keep']} | {c['keep_pred_drop']} | {c['maybe_missed']} |"
        )

    lines.extend(
        [
            "",
            "## Diagnosis",
            "",
            "- The model has learned the output schema, but it is not yet a reliable teacher replacement.",
            "- The dominant failure is calibration, not JSON formatting.",
            "- `cot_zh` is the main bottleneck. It mixes translated entailment/math-style prompts, option wording noise, and terse answers; the student often over-trusts or over-penalizes these examples.",
            "- `maybe` is not learned as a real middle class. It is treated as either keep or drop, so a 3-way scorer is currently poorly calibrated.",
            "- For filtering, `keep` precision is usable for a first-pass high-quality pool, but `drop` recall is too low to safely remove all bad data.",
            "",
            "## Recommended Adjustments",
            "",
            "1. Do not tune hyperparameters first. The bottleneck is data coverage and label boundary calibration.",
            "2. Add targeted teacher labels: more `cot_zh`, more `maybe`, and more `drop` cases that look superficially fluent.",
            "3. Consider a two-stage label: first `usable/not_usable`, then optional 1-5 score. This can improve filtering utility even if exact scores remain noisy.",
            "4. Add eval during training for the next run, so we can stop by validation verdict accuracy instead of only train loss.",
            "5. For immediate use, treat predictions conservatively: only auto-keep high-confidence keep-style outputs after spot checks; do not auto-drop based only on this model yet.",
            "",
            "## Representative Errors",
            "",
        ]
    )

    example_specs = [
        ("drop_pred_keep", "Teacher drop, model keep"),
        ("keep_pred_drop", "Teacher keep, model drop"),
        ("maybe_missed", "Teacher maybe, model missed"),
        ("cot_zh_errors", "cot_zh mismatch"),
    ]
    for key, title in example_specs:
        examples = sorted(
            categories[key],
            key=lambda r: abs(r["score_error"] or 0),
            reverse=True,
        )[:4]
        if not examples:
            continue
        lines.extend([f"## {title}", ""])
        for i, rec in enumerate(examples, start=1):
            add_example(lines, f"{title} #{i}", rec)

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote markdown report: {output_md.name}")
    if output_json:
        print(f"Wrote metrics JSON: {output_json.name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case",
        action="append",
        nargs=3,
        metavar=("SPLIT", "PREDICTIONS", "REFERENCE"),
        required=True,
        help="Add one split to analyze.",
    )
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    specs = [CaseSpec(split, Path(pred), Path(ref)) for split, pred, ref in args.case]
    records = load_cases(specs)
    build_report(records, args.output_md, args.output_json)


if __name__ == "__main__":
    main()
