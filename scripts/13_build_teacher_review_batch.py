"""Build a deduplicated teacher-review batch from scorer triage outputs.

This script is for the active-learning loop:

1. run local scorer(s) over a candidate pool
2. build a priority JSONL from model disagreements / likely hard negatives
3. exclude samples already labeled by the teacher, using the original sample id
4. write a new teacher-labeling candidate batch with a unique batch prefix

The resulting candidate JSONL can be passed directly to `04_teacher_judge.py`.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "scored" / "teacher_candidates_all_v2_teacher_review_priority.jsonl"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v2_active_pilot_001"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "teacher_sampling_v2_active_pilot_001_report.md"
DEFAULT_KNOWN_LABEL_FILES = [
    PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "pilot_teacher_labels.jsonl",
    PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "teacher_labels_1000.jsonl",
    PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "targeted_1200_teacher_labels.jsonl",
    PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "v2active001" / "v2active001_teacher_labels.jsonl",
    # v2active002 candidates (in-progress labeling): exclude by candidate id
    # since the label file may not exist yet during incremental runs.
    PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v2_active_pilot_002" / "v2active002_teacher_candidates_all.jsonl",
    # Evergreen baseline test ids must NEVER enter active-learning batches.
    PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test" / "teacher_candidates_all.jsonl",
    PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test_extension" / "teacher_candidates_all.jsonl",
]

SPLITS = ["train", "valid", "test"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an unlabeled teacher-review batch from scorer priority data.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Scorer priority/review JSONL.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--known-label-file",
        type=Path,
        action="append",
        default=None,
        help="Existing teacher-label JSONL to exclude by original id. Repeatable.",
    )
    parser.add_argument("--batch-prefix", type=str, default="v2active001")
    parser.add_argument("--max-samples", type=int, default=500, help="Cap selected unlabeled records after sorting.")
    parser.add_argument("--min-samples", type=int, default=0, help="Warn in the report if selected records are below this.")
    parser.add_argument(
        "--include-bucket",
        action="append",
        default=None,
        help="Optional agreement bucket filter. Repeatable. Example: conf_not_keep__cons_not_keep",
    )
    parser.add_argument("--seed-note", type=str, default="deterministic_priority_order")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
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


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def original_id(record: dict[str, Any]) -> str:
    return str(record.get("id") or "")


def load_known_ids(paths: list[Path]) -> tuple[set[str], dict[str, int]]:
    known_ids: set[str] = set()
    counts: dict[str, int] = {}
    for path in paths:
        if not path.exists():
            counts[str(path)] = 0
            continue

        records = read_jsonl(path)
        counts[str(path)] = len(records)
        for record in records:
            sample_id = original_id(record)
            if sample_id:
                known_ids.add(sample_id)

    return known_ids, counts


def priority_reasons(record: dict[str, Any]) -> list[str]:
    reasons = record.get("priority_reasons")
    if isinstance(reasons, list):
        return [str(reason) for reason in reasons]
    reason = record.get("priority_reason")
    if reason:
        return [str(reason)]
    return []


def priority_rank(record: dict[str, Any]) -> tuple[int, int, str, str]:
    reasons = set(priority_reasons(record))
    bucket = str(record.get("agreement_bucket") or "")

    if "model_disagreement" in reasons:
        tier = 0
    elif "both_not_keep" in reasons or bucket == "conf_not_keep__cons_not_keep":
        tier = 1
    elif "conservative_clean_not_keep" in reasons:
        tier = 2
    elif "confident_clean_not_keep" in reasons:
        tier = 3
    elif "flagged_but_model_keep" in reasons:
        tier = 4
    else:
        tier = 9

    flag_count = len(record.get("flags") if isinstance(record.get("flags"), list) else [])
    return (tier, -flag_count, str(record.get("source") or ""), original_id(record))


def build_selected_records(
    records: list[dict[str, Any]],
    known_ids: set[str],
    batch_prefix: str,
    max_samples: int | None,
    include_buckets: set[str] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    deduped: dict[str, dict[str, Any]] = {}
    duplicate_input_ids: list[dict[str, Any]] = []

    for record in records:
        sample_id = original_id(record)
        if not sample_id:
            continue
        if include_buckets and str(record.get("agreement_bucket") or "") not in include_buckets:
            continue
        if sample_id in deduped:
            duplicate_input_ids.append(record)
            continue
        deduped[sample_id] = record

    existing = [record for record in deduped.values() if original_id(record) in known_ids]
    unlabeled = [record for record in deduped.values() if original_id(record) not in known_ids]
    unlabeled.sort(key=priority_rank)
    if max_samples is not None:
        unlabeled = unlabeled[:max_samples]

    selected: list[dict[str, Any]] = []
    for index, record in enumerate(unlabeled):
        row = dict(record)
        selection = row.get("selection") if isinstance(row.get("selection"), dict) else {}
        selection = dict(selection)
        selection.update(
            {
                "batch_prefix": batch_prefix,
                "selection_rank": index,
                "source_teacher_sample_id": row.get("teacher_sample_id"),
                "source_agreement_bucket": row.get("agreement_bucket"),
                "source_priority_reasons": priority_reasons(row),
            }
        )
        row["selection"] = selection
        row["teacher_sample_id"] = f"{batch_prefix}_{index:05d}"
        row["teacher_label"] = None
        row["raw_teacher_response"] = None
        row["validation_errors"] = []
        selected.append(row)

    return selected, existing, duplicate_input_ids


def count_by(records: list[dict[str, Any]], key: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for record in records:
        value = record.get(key)
        counter[str(value) if value not in (None, "") else "unknown"] += 1
    return counter


def count_reasons(records: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for record in records:
        for reason in priority_reasons(record):
            counter[reason] += 1
    return counter


def write_report(
    path: Path,
    args: argparse.Namespace,
    outputs: dict[str, Path],
    input_records: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    existing: list[dict[str, Any]],
    duplicate_input_ids: list[dict[str, Any]],
    known_counts: dict[str, int],
) -> None:
    split_counts = count_by(selected, "split")
    source_counts = count_by(selected, "source")
    bucket_counts = count_by(selected, "agreement_bucket")
    reason_counts = count_reasons(selected)
    existing_bucket_counts = count_by(existing, "agreement_bucket")

    warning_lines: list[str] = []
    if args.min_samples and len(selected) < args.min_samples:
        warning_lines.append(f"- Selected records `{len(selected)}` is below requested minimum `{args.min_samples}`.")

    lines = [
        "# Teacher Review Batch Report",
        "",
        "## Report Metadata",
        "",
        markdown_table(
            ["Field", "Value"],
            [
                ["Report type", "Active-learning teacher batch"],
                ["Project stage", "V2 scorer triage / teacher relabeling"],
                ["Report status", "Generated"],
                ["Batch prefix", f"`{args.batch_prefix}`"],
            ],
        ),
        "",
        "## Experiment Context",
        "",
        markdown_table(
            ["Field", "Value"],
            [
                ["Input priority file", f"`{args.input}`"],
                ["Existing label exclusion", "original sample `id` only"],
                ["Max samples", args.max_samples],
                ["Ordering", args.seed_note],
                ["Current use", "Send selected unlabeled hard cases to the teacher model"],
            ],
        ),
        "",
        "## Summary",
        "",
        markdown_table(
            ["Metric", "Count"],
            [
                ["Input records", len(input_records)],
                ["Already teacher-labeled by original id", len(existing)],
                ["Selected unlabeled records", len(selected)],
                ["Duplicate ids inside input skipped", len(duplicate_input_ids)],
            ],
        ),
    ]

    if warning_lines:
        lines.extend(["", "## Warnings", "", *warning_lines])

    lines.extend(
        [
            "",
            "## Known Label Files",
            "",
            markdown_table(["Path", "Records"], [[path, count] for path, count in known_counts.items()]),
            "",
            "## Outputs",
            "",
            markdown_table(["Artifact", "Path"], [[name, f"`{output}`"] for name, output in outputs.items()]),
            "",
            "## Selected By Source",
            "",
            markdown_table(["Source", "Records"], [[name, count] for name, count in source_counts.most_common()]),
            "",
            "## Selected By Split",
            "",
            markdown_table(["Split", "Records"], [[split, split_counts.get(split, 0)] for split in SPLITS]),
            "",
            "## Selected By Agreement Bucket",
            "",
            markdown_table(["Agreement bucket", "Records"], [[name, count] for name, count in bucket_counts.most_common()]),
            "",
            "## Selected By Priority Reason",
            "",
            markdown_table(["Priority reason", "Records"], [[name, count] for name, count in reason_counts.most_common()]),
            "",
            "## Already Labeled By Agreement Bucket",
            "",
            markdown_table(
                ["Agreement bucket", "Records"],
                [[name, count] for name, count in existing_bucket_counts.most_common()],
            ),
            "",
            "## Recommended Commands",
            "",
            "Render prompts:",
            "",
            "```powershell",
            (
                "python scripts/04_teacher_judge.py "
                f"--input {outputs['all_candidates']} "
                f"--output-dir data/labeled/teacher_judge/{args.batch_prefix} "
                f"--output-name {args.batch_prefix}_teacher_prompts.jsonl "
                "--dry-run"
            ),
            "```",
            "",
            "Run teacher labeling:",
            "",
            "```powershell",
            (
                "python scripts/04_teacher_judge.py "
                f"--input {outputs['all_candidates']} "
                f"--output-dir data/labeled/teacher_judge/{args.batch_prefix} "
                f"--output-name {args.batch_prefix}_teacher_labels.jsonl "
                "--no-dry-run --resume"
            ),
            "```",
            "",
            "Split/analyze labels after the teacher run:",
            "",
            "```powershell",
            (
                "python scripts/05_analyze_teacher_labels.py "
                f"--input data/labeled/teacher_judge/{args.batch_prefix}/{args.batch_prefix}_teacher_labels.jsonl "
                "--output-dir data/labeled/teacher_judge "
                f"--split-prefix {args.batch_prefix}_teacher_labels "
                f"--report-path reports/teacher_label_report_{args.batch_prefix}.md"
            ),
            "```",
            "",
            "Then add the new candidate file and label prefix to `scripts/09_build_binary_scorer_sft.py` when building v3.",
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    known_label_files = args.known_label_file or DEFAULT_KNOWN_LABEL_FILES
    include_buckets = set(args.include_bucket) if args.include_bucket else None

    input_records = read_jsonl(args.input)
    known_ids, known_counts = load_known_ids(known_label_files)
    selected, existing, duplicate_input_ids = build_selected_records(
        input_records,
        known_ids,
        args.batch_prefix,
        args.max_samples,
        include_buckets,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    all_path = args.output_dir / f"{args.batch_prefix}_teacher_candidates_all.jsonl"
    outputs = {
        "all_candidates": all_path,
        "train_candidates": args.output_dir / f"{args.batch_prefix}_teacher_candidates_train.jsonl",
        "valid_candidates": args.output_dir / f"{args.batch_prefix}_teacher_candidates_valid.jsonl",
        "test_candidates": args.output_dir / f"{args.batch_prefix}_teacher_candidates_test.jsonl",
        "already_labeled_matches": args.output_dir / f"{args.batch_prefix}_already_labeled_matches.jsonl",
        "duplicate_input_ids": args.output_dir / f"{args.batch_prefix}_duplicate_input_ids.jsonl",
    }

    write_jsonl(outputs["all_candidates"], selected)
    for split in SPLITS:
        write_jsonl(outputs[f"{split}_candidates"], [record for record in selected if record.get("split") == split])
    write_jsonl(outputs["already_labeled_matches"], existing)
    write_jsonl(outputs["duplicate_input_ids"], duplicate_input_ids)

    write_report(args.report_path, args, outputs, input_records, selected, existing, duplicate_input_ids, known_counts)

    print(
        json.dumps(
            {
                "input": str(args.input),
                "output_dir": str(args.output_dir),
                "report": str(args.report_path),
                "selected": len(selected),
                "already_labeled": len(existing),
                "duplicate_input_ids": len(duplicate_input_ids),
                "outputs": {name: str(path) for name, path in outputs.items()},
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
