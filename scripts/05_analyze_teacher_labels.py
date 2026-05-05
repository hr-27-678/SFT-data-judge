"""Analyze Teacher Judge labels and write split label files.

This script validates a teacher-label JSONL file, summarizes score/verdict
distributions, and splits records by their existing train/valid/test field.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "teacher_labels_1000.jsonl"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "labeled" / "teacher_judge"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "teacher_label_report_1000.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze Teacher Judge labels.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--split-prefix", type=str, default="teacher_labels_1000")
    parser.add_argument(
        "--dedupe-by-id",
        action="store_true",
        help="Keep the last record for duplicate original sample ids. Useful when retry outputs are appended.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8-sig") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))
    return records


def dedupe_by_id(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    first_seen_order: list[str] = []
    duplicate_ids: Counter[str] = Counter()
    missing_id_records: list[dict[str, Any]] = []

    for record in records:
        key = str(record.get("id") or "")
        if not key:
            missing_id_records.append(record)
            continue
        if key in deduped:
            duplicate_ids[key] += 1
        else:
            first_seen_order.append(key)
        deduped[key] = record

    output_records = [deduped[key] for key in first_seen_order] + missing_id_records
    return output_records, {
        "raw_records": len(records),
        "records_after_dedupe": len(output_records),
        "duplicate_id_rows": sum(duplicate_ids.values()),
        "duplicate_id_examples": duplicate_ids.most_common(10),
        "missing_id_records": len(missing_id_records),
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def score_value(record: dict[str, Any]) -> int | None:
    label = record.get("teacher_label")
    if not isinstance(label, dict):
        return None
    score = label.get("overall_score")
    return score if isinstance(score, int) else None


def verdict_value(record: dict[str, Any]) -> str | None:
    label = record.get("teacher_label")
    if not isinstance(label, dict):
        return None
    verdict = label.get("verdict")
    return verdict if isinstance(verdict, str) else None


def has_validation_errors(record: dict[str, Any]) -> bool:
    errors = record.get("validation_errors")
    return bool(errors)


def count_by(records: list[dict[str, Any]], key: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for record in records:
        value = record.get(key)
        counter[str(value) if value is not None else "missing"] += 1
    return counter


def score_rows(records: list[dict[str, Any]]) -> list[list[Any]]:
    counter = Counter(score_value(record) for record in records if score_value(record) is not None)
    return [[score, counter.get(score, 0)] for score in range(1, 6)]


def verdict_rows(records: list[dict[str, Any]]) -> list[list[Any]]:
    counter = Counter(verdict_value(record) for record in records if verdict_value(record) is not None)
    return [[verdict, counter.get(verdict, 0)] for verdict in ["keep", "maybe", "drop"]]


def source_score_rows(records: list[dict[str, Any]]) -> list[list[Any]]:
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_source[str(record.get("source", "missing"))].append(record)

    rows = []
    for source in sorted(by_source):
        subset = by_source[source]
        counter = Counter(score_value(record) for record in subset if score_value(record) is not None)
        rows.append(
            [
                source,
                len(subset),
                counter.get(1, 0),
                counter.get(2, 0),
                counter.get(3, 0),
                counter.get(4, 0),
                counter.get(5, 0),
            ]
        )
    return rows


def clean_status_score_rows(records: list[dict[str, Any]]) -> list[list[Any]]:
    by_status: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        sampling = record.get("sampling") if isinstance(record.get("sampling"), dict) else {}
        status = str(sampling.get("clean_status", "missing"))
        by_status[status].append(record)

    rows = []
    for status in sorted(by_status):
        subset = by_status[status]
        counter = Counter(score_value(record) for record in subset if score_value(record) is not None)
        rows.append(
            [
                status,
                len(subset),
                counter.get(1, 0),
                counter.get(2, 0),
                counter.get(3, 0),
                counter.get(4, 0),
                counter.get(5, 0),
            ]
        )
    return rows


def major_issue_rows(records: list[dict[str, Any]]) -> list[list[Any]]:
    counter: Counter[str] = Counter()
    for record in records:
        label = record.get("teacher_label") if isinstance(record.get("teacher_label"), dict) else {}
        issues = label.get("major_issues", [])
        if isinstance(issues, list):
            for issue in issues:
                counter[str(issue)] += 1
    return [[issue, count] for issue, count in counter.most_common()]


def split_outputs(records: list[dict[str, Any]], output_dir: Path, split_prefix: str) -> dict[str, Path]:
    outputs = {}
    for split in ["train", "valid", "test"]:
        path = output_dir / f"{split_prefix}_{split}.jsonl"
        write_jsonl(path, [record for record in records if record.get("split") == split])
        outputs[split] = path
    return outputs


def write_report(
    path: Path,
    records: list[dict[str, Any]],
    split_paths: dict[str, Path],
    split_prefix: str,
    dedupe_metadata: dict[str, Any] | None = None,
) -> None:
    null_labels = sum(1 for record in records if record.get("teacher_label") is None)
    validation_errors = sum(1 for record in records if has_validation_errors(record))
    split_counter = count_by(records, "split")
    source_counter = count_by(records, "source")
    validation_rows = [
        ["Records", len(records)],
        ["Null labels", null_labels],
        ["Rows with validation errors", validation_errors],
    ]
    if dedupe_metadata:
        validation_rows.extend(
            [
                ["Raw input rows", dedupe_metadata["raw_records"]],
                ["Rows after id dedupe", dedupe_metadata["records_after_dedupe"]],
                ["Duplicate id rows removed", dedupe_metadata["duplicate_id_rows"]],
                ["Rows missing original id", dedupe_metadata["missing_id_records"]],
            ]
        )

    lines = [
        f"# Teacher Label Report ({split_prefix})",
        "",
        "This report is generated by `scripts/05_analyze_teacher_labels.py`.",
        "",
        "## Validation",
        "",
        markdown_table(
            ["Check", "Result"],
            validation_rows,
        ),
        "",
        "## Split Outputs",
        "",
        markdown_table(["Split", "Path", "Records"], [[split, path.as_posix(), split_counter.get(split, 0)] for split, path in split_paths.items()]),
        "",
        "## Source Balance",
        "",
        markdown_table(["Source", "Records"], [[source, source_counter[source]] for source in sorted(source_counter)]),
        "",
        "## Score Distribution",
        "",
        markdown_table(["Score", "Count"], score_rows(records)),
        "",
        "## Verdict Distribution",
        "",
        markdown_table(["Verdict", "Count"], verdict_rows(records)),
        "",
        "## Score By Source",
        "",
        markdown_table(["Source", "Total", "Score 1", "Score 2", "Score 3", "Score 4", "Score 5"], source_score_rows(records)),
        "",
        "## Score By Clean Status",
        "",
        markdown_table(["Clean Status", "Total", "Score 1", "Score 2", "Score 3", "Score 4", "Score 5"], clean_status_score_rows(records)),
        "",
        "## Major Issue Tags",
        "",
        markdown_table(["Issue", "Count"], major_issue_rows(records) or [["none", 0]]),
        "",
        "## Notes",
        "",
        "- `validation_errors` checks whether Teacher LLM output matches the required JSON schema.",
        "- `is_clean`/`clean_status` is rule-based preprocessing; it is not the same as semantic quality.",
        "- Score 5/4 maps to keep, score 3 maps to maybe, and score 2/1 maps to drop.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    raw_records = read_jsonl(args.input)
    dedupe_metadata = None
    records = raw_records
    if args.dedupe_by_id:
        records, dedupe_metadata = dedupe_by_id(raw_records)
    split_paths = split_outputs(records, args.output_dir, args.split_prefix)
    write_report(args.report_path, records, split_paths, args.split_prefix, dedupe_metadata)
    print(
        json.dumps(
            {
                "input": str(args.input),
                "raw_records": len(raw_records),
                "records": len(records),
                "dedupe_by_id": args.dedupe_by_id,
                "duplicate_id_rows": dedupe_metadata["duplicate_id_rows"] if dedupe_metadata else 0,
                "report": str(args.report_path),
                "split_outputs": {split: str(path) for split, path in split_paths.items()},
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
