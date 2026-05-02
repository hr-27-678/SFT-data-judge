"""Build a small, source-separated pilot set for Teacher Judge validation."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE_DIR = PROJECT_ROOT / "data" / "splits" / "teacher_judge"
DEFAULT_OUTPUT_DIR = DEFAULT_CANDIDATE_DIR / "pilot"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "pilot_sampling_report.md"
DEFAULT_SOURCES = ["cot_zh", "finetome", "openmath_reasoning"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a small pilot set for teacher judging.")
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--per-source", type=int, default=20, help="Pilot samples per source.")
    parser.add_argument("--flagged-ratio", type=float, default=0.30, help="Pilot ratio for suspicious/flagged samples.")
    parser.add_argument("--seed", type=int, default=7)
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


def allocate(total: int, buckets: list[str]) -> dict[str, int]:
    if not buckets:
        return {}
    base = total // len(buckets)
    remainder = total % len(buckets)
    return {bucket: base + (1 if i < remainder else 0) for i, bucket in enumerate(buckets)}


def sample_group(
    candidates: list[dict[str, Any]],
    count: int,
    rng: random.Random,
    selected_ids: set[str],
) -> list[dict[str, Any]]:
    pool = [record for record in candidates if record["id"] not in selected_ids]
    if not pool or count <= 0:
        return []
    sampled = rng.sample(pool, min(count, len(pool)))
    selected_ids.update(record["id"] for record in sampled)
    return sampled


def sample_source(
    records: list[dict[str, Any]],
    source: str,
    per_source: int,
    flagged_ratio: float,
    rng: random.Random,
) -> list[dict[str, Any]]:
    by_status_bucket: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        sampling = record.get("sampling", {})
        status = sampling.get("clean_status", "clean" if record.get("is_clean") else "flagged")
        bucket = sampling.get("length_bucket", "unknown")
        by_status_bucket[(status, bucket)].append(record)

    target_flagged = round(per_source * flagged_ratio)
    target_clean = per_source - target_flagged
    targets = {
        "clean": allocate(target_clean, ["short", "medium", "long"]),
        "flagged": allocate(target_flagged, ["short", "medium", "long"]),
    }

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    for status, bucket_targets in targets.items():
        for bucket, count in bucket_targets.items():
            selected.extend(sample_group(by_status_bucket.get((status, bucket), []), count, rng, selected_ids))

    if len(selected) < per_source:
        selected.extend(sample_group(records, per_source - len(selected), rng, selected_ids))

    selected = selected[:per_source]
    for index, record in enumerate(selected):
        record["pilot_sample_id"] = f"pilot_{source}_{index:04d}"
        record["is_pilot"] = True
    return selected


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, selected_by_source: dict[str, list[dict[str, Any]]], outputs: dict[str, Path]) -> None:
    rows = []
    for source, records in selected_by_source.items():
        status_counts = Counter(record.get("sampling", {}).get("clean_status") for record in records)
        bucket_counts = Counter(record.get("sampling", {}).get("length_bucket") for record in records)
        rows.append(
            [
                source,
                len(records),
                status_counts.get("clean", 0),
                status_counts.get("flagged", 0),
                bucket_counts.get("short", 0),
                bucket_counts.get("medium", 0),
                bucket_counts.get("long", 0),
            ]
        )

    lines = [
        "# Phase 3 Pilot Sampling Report",
        "",
        "This report is generated by `scripts/03_build_pilot.py`.",
        "",
        "## Outputs",
        "",
        markdown_table(["Artifact", "Path"], [[name, p.as_posix()] for name, p in outputs.items()]),
        "",
        "## Pilot Summary",
        "",
        markdown_table(["source", "sampled", "clean", "flagged", "short", "medium", "long"], rows),
        "",
        "## Why Pilot",
        "",
        "Pilot samples are used to test the Teacher Judge prompt, JSON parsing, and score calibration before labeling the full candidate set.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    selected_by_source: dict[str, list[dict[str, Any]]] = {}
    outputs: dict[str, Path] = {}
    all_selected: list[dict[str, Any]] = []

    for source in DEFAULT_SOURCES:
        path = args.candidate_dir / f"{source}_teacher_candidates.jsonl"
        if not path.exists():
            raise FileNotFoundError(f"Missing teacher candidate file: {path}")
        records = read_jsonl(path)
        selected = sample_source(records, source, args.per_source, args.flagged_ratio, rng)
        selected_by_source[source] = selected
        all_selected.extend(selected)

        source_path = args.output_dir / f"{source}_pilot_candidates.jsonl"
        write_jsonl(source_path, selected)
        outputs[f"{source}_pilot"] = source_path

    combined_path = args.output_dir / "pilot_candidates_all.jsonl"
    write_jsonl(combined_path, all_selected)
    outputs["combined_pilot"] = combined_path
    outputs["report"] = args.report_path
    write_report(args.report_path, selected_by_source, outputs)

    print(json.dumps({"outputs": {k: str(v) for k, v in outputs.items()}}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
