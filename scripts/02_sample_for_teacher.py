"""Phase 2 stratified sampling for teacher judging.

The output of this script is not labeled data yet. It creates a balanced set of
candidate samples for a future Teacher LLM judge, keeping the three data sources
separate and stratifying inside each source.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "data" / "processed" / "by_source"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "splits" / "teacher_judge"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "teacher_sampling_report.md"

DEFAULT_SOURCE_SIZES = {
    "cot_zh": 1200,
    "finetome": 1200,
    "openmath_reasoning": 1200,
}

DEFAULT_EXCLUDE_LABEL_FILES = [
    PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "pilot_teacher_labels.jsonl",
    PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "teacher_labels_1000.jsonl",
    PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "targeted_1200_teacher_labels.jsonl",
    PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "v2active001" / "v2active001_teacher_labels.jsonl",
]


def parse_source_sizes(value: str | None) -> dict[str, int]:
    if not value:
        return DEFAULT_SOURCE_SIZES.copy()

    sizes: dict[str, int] = {}
    for item in value.split(","):
        if not item.strip():
            continue
        name, size = item.split("=", 1)
        sizes[name.strip()] = int(size)

    return sizes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build stratified Teacher Judge candidate samples.")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help="Directory containing per-source JSONL files from phase 1.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for teacher judge candidate outputs.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Markdown sampling report path.",
    )
    parser.add_argument(
        "--source-sizes",
        type=str,
        default=None,
        help="Comma separated source sizes, e.g. cot_zh=1200,finetome=1200,openmath_reasoning=1200.",
    )
    parser.add_argument(
        "--flagged-ratio",
        type=float,
        default=0.20,
        help="Target ratio of rule-flagged samples per source.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--exclude-label-files",
        type=Path,
        action="append",
        default=None,
        help=(
            "Teacher-label JSONL file whose original sample ids should be excluded from sampling. "
            "Repeatable. If omitted, defaults to all canonical teacher-label files in "
            "data/labeled/teacher_judge/."
        ),
    )
    parser.add_argument(
        "--no-exclude-defaults",
        action="store_true",
        help="Do not load the default exclude label files. Useful for reproducing legacy v1 sampling runs.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def quantile(values: list[int], ratio: float) -> int:
    if not values:
        return 0
    sorted_values = sorted(values)
    index = round((len(sorted_values) - 1) * ratio)
    return sorted_values[index]


def add_sampling_fields(records: list[dict[str, Any]]) -> None:
    lengths = [int(record.get("output_len", 0)) for record in records]
    q33 = quantile(lengths, 0.33)
    q66 = quantile(lengths, 0.66)

    for record in records:
        output_len = int(record.get("output_len", 0))
        if output_len <= q33:
            length_bucket = "short"
        elif output_len <= q66:
            length_bucket = "medium"
        else:
            length_bucket = "long"

        record["sampling"] = {
            "clean_status": "clean" if record.get("is_clean") else "flagged",
            "length_bucket": length_bucket,
            "source_output_len_q33": q33,
            "source_output_len_q66": q66,
        }


def split_target(total: int, flagged_ratio: float) -> dict[str, int]:
    flagged = round(total * flagged_ratio)
    clean = total - flagged
    return {"clean": clean, "flagged": flagged}


def allocate_bucket_targets(total: int, bucket_names: list[str]) -> dict[str, int]:
    if not bucket_names:
        return {}

    base = total // len(bucket_names)
    remainder = total % len(bucket_names)
    targets = {}
    for index, bucket in enumerate(bucket_names):
        targets[bucket] = base + (1 if index < remainder else 0)
    return targets


def sample_without_replacement(
    candidates: list[dict[str, Any]],
    count: int,
    rng: random.Random,
    selected_ids: set[str],
) -> list[dict[str, Any]]:
    pool = [record for record in candidates if record["id"] not in selected_ids]
    if not pool or count <= 0:
        return []
    count = min(count, len(pool))
    sampled = rng.sample(pool, count)
    selected_ids.update(record["id"] for record in sampled)
    return sampled


def stratified_sample_source(
    records: list[dict[str, Any]],
    source: str,
    total: int,
    flagged_ratio: float,
    rng: random.Random,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    add_sampling_fields(records)
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    by_status_bucket: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = (record["sampling"]["clean_status"], record["sampling"]["length_bucket"])
        by_status_bucket[key].append(record)

    status_targets = split_target(total, flagged_ratio)
    bucket_names = ["short", "medium", "long"]

    requested: dict[str, dict[str, int]] = {}
    actual_first_pass: dict[str, dict[str, int]] = {}
    for status, status_total in status_targets.items():
        bucket_targets = allocate_bucket_targets(status_total, bucket_names)
        requested[status] = bucket_targets
        actual_first_pass[status] = {}

        for bucket, bucket_target in bucket_targets.items():
            candidates = by_status_bucket.get((status, bucket), [])
            sampled = sample_without_replacement(candidates, bucket_target, rng, selected_ids)
            selected.extend(sampled)
            actual_first_pass[status][bucket] = len(sampled)

    if len(selected) < total:
        selected.extend(sample_without_replacement(records, total - len(selected), rng, selected_ids))

    selected = selected[:total]
    for order, record in enumerate(selected):
        record["teacher_sample_id"] = f"tj_{source}_{order:05d}"
        record["teacher_label"] = None

    assign_splits(selected, rng)
    summary = summarize_sample(source, records, selected, requested, actual_first_pass)
    return selected, summary


def assign_splits(records: list[dict[str, Any]], rng: random.Random) -> None:
    by_stratum: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = (record["sampling"]["clean_status"], record["sampling"]["length_bucket"])
        by_stratum[key].append(record)

    for group in by_stratum.values():
        rng.shuffle(group)
        n_total = len(group)
        n_valid = max(1, round(n_total * 0.10)) if n_total >= 10 else 0
        n_test = max(1, round(n_total * 0.10)) if n_total >= 10 else 0

        for index, record in enumerate(group):
            if index < n_valid:
                split = "valid"
            elif index < n_valid + n_test:
                split = "test"
            else:
                split = "train"
            record["split"] = split


def summarize_sample(
    source: str,
    records: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    requested: dict[str, dict[str, int]],
    actual_first_pass: dict[str, dict[str, int]],
) -> dict[str, Any]:
    source_counter = Counter(record["sampling"]["clean_status"] for record in selected)
    bucket_counter = Counter(record["sampling"]["length_bucket"] for record in selected)
    split_counter = Counter(record["split"] for record in selected)
    status_bucket_counter = Counter(
        (record["sampling"]["clean_status"], record["sampling"]["length_bucket"]) for record in selected
    )

    return {
        "source": source,
        "available": len(records),
        "sampled": len(selected),
        "requested": requested,
        "actual_first_pass": actual_first_pass,
        "sampled_clean_status": dict(source_counter),
        "sampled_length_bucket": dict(bucket_counter),
        "sampled_split": dict(split_counter),
        "sampled_status_bucket": {f"{status}:{bucket}": count for (status, bucket), count in status_bucket_counter.items()},
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, summaries: list[dict[str, Any]], outputs: dict[str, Path]) -> None:
    rows = []
    for item in summaries:
        rows.append(
            [
                item["source"],
                item["available"],
                item["sampled"],
                item["sampled_clean_status"].get("clean", 0),
                item["sampled_clean_status"].get("flagged", 0),
                item["sampled_length_bucket"].get("short", 0),
                item["sampled_length_bucket"].get("medium", 0),
                item["sampled_length_bucket"].get("long", 0),
                item["sampled_split"].get("train", 0),
                item["sampled_split"].get("valid", 0),
                item["sampled_split"].get("test", 0),
            ]
        )

    lines = [
        "# Phase 2 Teacher Sampling Report",
        "",
        "This report is generated by `scripts/02_sample_for_teacher.py`.",
        "",
        "## Outputs",
        "",
        markdown_table(["Artifact", "Path"], [[name, p.as_posix()] for name, p in outputs.items()]),
        "",
        "## Sampling Summary",
        "",
        markdown_table(
            [
                "source",
                "available",
                "sampled",
                "clean",
                "flagged",
                "short",
                "medium",
                "long",
                "train",
                "valid",
                "test",
            ],
            rows,
        ),
        "",
        "## Notes",
        "",
        "- Sampling is source-separated. There is no mixed random draw across all sources.",
        "- Each source targets 80% clean and 20% rule-flagged samples by default.",
        "- Within clean/flagged groups, samples are spread across source-specific output length buckets.",
        "- Candidate files are unlabeled. `teacher_label` is intentionally null until a Teacher LLM is run.",
        "- `split` is assigned inside each source and stratum so scorer evaluation can stay source-aware.",
        "",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def load_excluded_ids(args: argparse.Namespace) -> tuple[set[str], list[Path]]:
    files: list[Path] = []
    if not args.no_exclude_defaults:
        files.extend(p for p in DEFAULT_EXCLUDE_LABEL_FILES if p.exists())
    if args.exclude_label_files:
        files.extend(args.exclude_label_files)

    excluded: set[str] = set()
    for path in files:
        if not path.exists():
            raise FileNotFoundError(f"Exclude label file not found: {path}")
        with path.open("r", encoding="utf-8-sig") as file:
            for line in file:
                if not line.strip():
                    continue
                record = json.loads(line)
                rid = record.get("id")
                if rid:
                    excluded.add(rid)
    return excluded, files


def main() -> None:
    args = parse_args()
    source_sizes = parse_source_sizes(args.source_sizes)
    rng = random.Random(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    excluded_ids, exclude_files = load_excluded_ids(args)
    if exclude_files:
        print(f"[exclude] Loaded {len(excluded_ids)} ids from {len(exclude_files)} label file(s).")

    all_selected: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    outputs: dict[str, Path] = {}

    for source, total in source_sizes.items():
        source_path = args.source_dir / f"{source}.jsonl"
        if not source_path.exists():
            raise FileNotFoundError(f"Missing source file: {source_path}")

        records = read_jsonl(source_path)
        if excluded_ids:
            before = len(records)
            records = [r for r in records if r.get("id") not in excluded_ids]
            removed = before - len(records)
            if removed:
                print(f"[exclude] {source}: removed {removed} already-labeled records before sampling.")
        if total > len(records):
            total = len(records)

        selected, summary = stratified_sample_source(records, source, total, args.flagged_ratio, rng)
        summaries.append(summary)
        all_selected.extend(selected)

        source_out = args.output_dir / f"{source}_teacher_candidates.jsonl"
        write_jsonl(source_out, selected)
        outputs[f"{source}_candidates"] = source_out

    combined_path = args.output_dir / "teacher_candidates_all.jsonl"
    train_path = args.output_dir / "teacher_candidates_train.jsonl"
    valid_path = args.output_dir / "teacher_candidates_valid.jsonl"
    test_path = args.output_dir / "teacher_candidates_test.jsonl"
    summary_path = args.output_dir / "teacher_sampling_summary.json"
    write_jsonl(combined_path, all_selected)
    write_jsonl(train_path, [record for record in all_selected if record["split"] == "train"])
    write_jsonl(valid_path, [record for record in all_selected if record["split"] == "valid"])
    write_jsonl(test_path, [record for record in all_selected if record["split"] == "test"])
    summary_path.write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")

    outputs["combined_candidates"] = combined_path
    outputs["train_candidates"] = train_path
    outputs["valid_candidates"] = valid_path
    outputs["test_candidates"] = test_path
    outputs["summary"] = summary_path
    outputs["report"] = args.report_path
    write_report(args.report_path, summaries, outputs)

    print(json.dumps({"outputs": {k: str(v) for k, v in outputs.items()}, "summaries": summaries}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
