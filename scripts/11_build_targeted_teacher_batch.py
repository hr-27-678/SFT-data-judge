#!/usr/bin/env python3
"""Build a targeted teacher-labeling batch for the next scorer round.

This batch is designed for active-ish labeling before we have full scorer
inference over the pool. It prioritizes weak sources, boundary-like examples,
and rule-flagged review cases, while excluding examples that already have
teacher labels.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POOL = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "teacher_candidates_all.jsonl"
DEFAULT_LABEL_DIR = PROJECT_ROOT / "data" / "labeled" / "teacher_judge"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "targeted_1200"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "teacher_sampling_targeted_1200_report.md"
SPLITS = ["train", "valid", "test"]


@dataclass(frozen=True)
class BucketSpec:
    name: str
    target: int
    note: str
    eligible: Callable[[dict[str, Any]], bool]
    score: Callable[[dict[str, Any]], float]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a targeted 1,000-example teacher batch.")
    parser.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--label-dir", type=Path, default=DEFAULT_LABEL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--total", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=20260502)
    parser.add_argument("--batch-prefix", type=str, default="targeted1200")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_labeled_ids(label_dir: Path) -> set[str]:
    labeled_ids: set[str] = set()
    if not label_dir.exists():
        return labeled_ids

    for path in sorted(label_dir.glob("*labels*.jsonl")):
        for row in read_jsonl(path):
            sample_id = row.get("id")
            if sample_id:
                labeled_ids.add(str(sample_id))
    return labeled_ids


def sampling(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("sampling")
    return value if isinstance(value, dict) else {}


def clean_status(record: dict[str, Any]) -> str:
    status = sampling(record).get("clean_status")
    if status:
        return str(status)
    return "clean" if record.get("is_clean") else "flagged"


def length_bucket(record: dict[str, Any]) -> str:
    return str(sampling(record).get("length_bucket", "unknown"))


def flags(record: dict[str, Any]) -> list[str]:
    value = record.get("flags")
    return value if isinstance(value, list) else []


def text(record: dict[str, Any]) -> str:
    return f"{record.get('instruction', '')}\n{record.get('output', '')}".lower()


def has_any(text_value: str, terms: list[str]) -> bool:
    return any(term in text_value for term in terms)


def base_score(record: dict[str, Any]) -> float:
    score = 0.0
    if clean_status(record) == "flagged":
        score += 2.0
    if length_bucket(record) == "short":
        score += 1.0
    if length_bucket(record) == "long":
        score += 0.8
    if flags(record):
        score += min(len(flags(record)), 3) * 0.5
    return score


def cot_score(record: dict[str, Any]) -> float:
    score = base_score(record)
    bucket = length_bucket(record)
    if bucket in {"short", "medium"}:
        score += 2.0
    if int(record.get("output_len", 0)) <= 80:
        score += 1.0
    return score


def finetome_score(record: dict[str, Any]) -> float:
    score = base_score(record)
    value = text(record)
    if has_any(
        value,
        [
            "python",
            "code",
            "program",
            "algorithm",
            "calculate",
            "solve",
            "proof",
            "equation",
            "statistics",
            "histogram",
            "stata",
            "function",
            "math",
        ],
    ):
        score += 2.5
    if length_bucket(record) in {"medium", "long"}:
        score += 1.0
    return score


def openmath_score(record: dict[str, Any]) -> float:
    score = base_score(record)
    if length_bucket(record) == "long":
        score += 2.0
    if clean_status(record) == "flagged":
        score += 2.0
    if int(record.get("output_len", 0)) > 2400:
        score += 1.0
    return score


def rule_flag_score(record: dict[str, Any]) -> float:
    score = 2.0 + base_score(record)
    if record.get("source") == "cot_zh":
        score += 0.7
    if record.get("source") == "finetome":
        score += 0.5
    return score


def maybe_like_score(record: dict[str, Any]) -> float:
    score = 0.0
    if record.get("source") == "cot_zh":
        score += 3.0
    if length_bucket(record) in {"short", "medium"}:
        score += 2.0
    if clean_status(record) == "clean":
        score += 1.0
    output_len = int(record.get("output_len", 0))
    if 20 <= output_len <= 180:
        score += 1.0
    return score


def bucket_specs(total: int) -> list[BucketSpec]:
    if total == 1200:
        targets = {
            "rule_flag_review": 160,
            "score3_like_review": 120,
            "cot_zh_hard": 560,
            "finetome_hard": 270,
            "openmath_hard": 90,
        }
    else:
        scale = total / 1000
        targets = {
            "rule_flag_review": round(120 * scale),
            "score3_like_review": round(80 * scale),
            "cot_zh_hard": round(440 * scale),
            "finetome_hard": round(240 * scale),
            "openmath_hard": round(120 * scale),
        }
        diff = total - sum(targets.values())
        targets["score3_like_review"] += diff

    specs = [
        BucketSpec(
            name="rule_flag_review",
            target=targets["rule_flag_review"],
            note="Proxy for rule/model disagreement until full scorer inference exists; all are rule-flagged.",
            eligible=lambda r: clean_status(r) == "flagged",
            score=rule_flag_score,
        ),
        BucketSpec(
            name="score3_like_review",
            target=targets["score3_like_review"],
            note="Likely ambiguous boundary cases; useful for deciding review/not_keep policy for score 3.",
            eligible=lambda r: clean_status(r) == "clean" and length_bucket(r) in {"short", "medium"},
            score=maybe_like_score,
        ),
        BucketSpec(
            name="cot_zh_hard",
            target=targets["cot_zh_hard"],
            note="Weakest evaluated source; focus on short/medium reasoning and noisy Chinese QA.",
            eligible=lambda r: r.get("source") == "cot_zh",
            score=cot_score,
        ),
        BucketSpec(
            name="finetome_hard",
            target=targets["finetome_hard"],
            note="General instruction hard cases, especially code/math/statistics and long incomplete answers.",
            eligible=lambda r: r.get("source") == "finetome",
            score=finetome_score,
        ),
        BucketSpec(
            name="openmath_hard",
            target=targets["openmath_hard"],
            note="Math reasoning hard negatives: long derivations, truncation-like outputs, and flagged samples.",
            eligible=lambda r: r.get("source") == "openmath_reasoning",
            score=openmath_score,
        ),
    ]
    return specs


def select_bucket(
    records: list[dict[str, Any]],
    spec: BucketSpec,
    rng: random.Random,
    used_ids: set[str],
) -> tuple[list[dict[str, Any]], int]:
    pool = [record for record in records if str(record.get("id")) not in used_ids and spec.eligible(record)]
    ranked = sorted(pool, key=lambda record: (spec.score(record), rng.random()), reverse=True)
    chosen = ranked[: spec.target]
    for record in chosen:
        used_ids.add(str(record.get("id")))
    return chosen, len(pool)


def assign_batch_fields(rows: list[dict[str, Any]], prefix: str, rng: random.Random) -> None:
    by_bucket_source: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_bucket_source[(row["selection"]["bucket"], row.get("source", "unknown"))].append(row)

    for group in by_bucket_source.values():
        rng.shuffle(group)
        n_total = len(group)
        n_valid = max(1, round(n_total * 0.10)) if n_total >= 10 else 0
        n_test = max(1, round(n_total * 0.10)) if n_total >= 10 else 0
        for idx, row in enumerate(group):
            original_split = row.get("split")
            if idx < n_valid:
                split = "valid"
            elif idx < n_valid + n_test:
                split = "test"
            else:
                split = "train"
            row["selection"]["original_split"] = original_split
            row["split"] = split

    for idx, row in enumerate(rows):
        original_teacher_sample_id = row.get("teacher_sample_id")
        row["selection"]["original_teacher_sample_id"] = original_teacher_sample_id
        row["teacher_sample_id"] = f"{prefix}_{idx:05d}"
        row["teacher_label"] = None


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_report(
    path: Path,
    rows: list[dict[str, Any]],
    specs: list[BucketSpec],
    pool_sizes: dict[str, int],
    outputs: dict[str, Path],
    labeled_ids: set[str],
    excluded_overlap: int,
) -> None:
    bucket_counts = Counter(row["selection"]["bucket"] for row in rows)
    source_counts = Counter(row.get("source") for row in rows)
    split_counts = Counter(row.get("split") for row in rows)
    status_counts = Counter(clean_status(row) for row in rows)
    source_bucket_counts = Counter((row.get("source"), row["selection"]["bucket"]) for row in rows)
    length_counts = Counter((row.get("source"), length_bucket(row)) for row in rows)

    lines = [
        f"# Targeted Teacher Sampling Report {len(rows)}",
        "",
        "This report is generated by `scripts/11_build_targeted_teacher_batch.py`.",
        "",
        "## Purpose",
        "",
        f"Build a targeted {len(rows)}-example batch for the next Teacher Judge labeling round.",
        "The batch prioritizes the current scorer weaknesses: `cot_zh`, score-2/4-like boundaries, hard keep/not_keep cases, and score-3-like review cases.",
        "",
        "## Outputs",
        "",
        markdown_table(["Artifact", "Path"], [[name, p.as_posix()] for name, p in outputs.items()]),
        "",
        "## Exclusions",
        "",
        markdown_table(
            ["Item", "Count"],
            [
                ["known_labeled_ids_seen", len(labeled_ids)],
                ["pool_records_excluded_by_id", excluded_overlap],
                ["selected_records", len(rows)],
            ],
        ),
        "",
        "## Bucket Targets And Results",
        "",
        markdown_table(
            ["Bucket", "Target", "Selected", "Eligible Pool", "Note"],
            [[spec.name, spec.target, bucket_counts.get(spec.name, 0), pool_sizes.get(spec.name, 0), spec.note] for spec in specs],
        ),
        "",
        "## Source Distribution",
        "",
        markdown_table(["Source", "Records"], [[source, source_counts[source]] for source in sorted(source_counts)]),
        "",
        "## Split Distribution",
        "",
        markdown_table(["Split", "Records"], [[split, split_counts.get(split, 0)] for split in SPLITS]),
        "",
        "## Clean Status",
        "",
        markdown_table(["Clean Status", "Records"], [[status, status_counts[status]] for status in sorted(status_counts)]),
        "",
        "## Source x Bucket",
        "",
        markdown_table(
            ["Source", *[spec.name for spec in specs]],
            [
                [source, *[source_bucket_counts.get((source, spec.name), 0) for spec in specs]]
                for source in sorted(source_counts)
            ],
        ),
        "",
        "## Source x Length Bucket",
        "",
        markdown_table(
            ["Source", "short", "medium", "long", "unknown"],
            [
                [
                    source,
                    length_counts.get((source, "short"), 0),
                    length_counts.get((source, "medium"), 0),
                    length_counts.get((source, "long"), 0),
                    length_counts.get((source, "unknown"), 0),
                ]
                for source in sorted(source_counts)
            ],
        ),
        "",
        "## Notes",
        "",
        "- `rule_flag_review` is a proxy bucket because full binary-scorer inference over the unlabeled pool has not been added yet.",
        "- `score3_like_review` examples are not assumed to be score 3; they are likely boundary cases for the Teacher Judge to decide.",
        "- The script overwrites `teacher_sample_id` with a unique targeted batch id and stores the original id under `selection.original_teacher_sample_id`.",
        "- The script reassigns train/valid/test splits inside each bucket/source stratum.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    records = read_jsonl(args.pool)
    labeled_ids = load_labeled_ids(args.label_dir)
    unlabeled = [record for record in records if str(record.get("id")) not in labeled_ids]
    excluded_overlap = len(records) - len(unlabeled)

    specs = bucket_specs(args.total)
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    pool_sizes: dict[str, int] = {}

    for spec in specs:
        chosen, pool_size = select_bucket(unlabeled, spec, rng, selected_ids)
        pool_sizes[spec.name] = pool_size
        for record in chosen:
            copied = json.loads(json.dumps(record, ensure_ascii=False))
            copied["selection"] = {
                "batch": args.batch_prefix,
                "bucket": spec.name,
                "bucket_note": spec.note,
                "selection_score": round(spec.score(copied), 4),
            }
            selected.append(copied)

    if len(selected) < args.total:
        fallback_pool = [record for record in unlabeled if str(record.get("id")) not in selected_ids]
        fallback_ranked = sorted(fallback_pool, key=lambda record: (base_score(record), rng.random()), reverse=True)
        for record in fallback_ranked[: args.total - len(selected)]:
            copied = json.loads(json.dumps(record, ensure_ascii=False))
            copied["selection"] = {
                "batch": args.batch_prefix,
                "bucket": "fallback_fill",
                "bucket_note": "Filled remaining quota from unlabeled pool.",
                "selection_score": round(base_score(copied), 4),
            }
            selected.append(copied)
            selected_ids.add(str(record.get("id")))

    if len(selected) != args.total:
        raise RuntimeError(f"Expected {args.total} selected records, got {len(selected)}.")

    assign_batch_fields(selected, args.batch_prefix, rng)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    all_path = args.output_dir / "targeted_teacher_candidates_all.jsonl"
    train_path = args.output_dir / "targeted_teacher_candidates_train.jsonl"
    valid_path = args.output_dir / "targeted_teacher_candidates_valid.jsonl"
    test_path = args.output_dir / "targeted_teacher_candidates_test.jsonl"
    summary_path = args.output_dir / "targeted_teacher_sampling_summary.json"
    outputs = {
        "combined_candidates": all_path,
        "train_candidates": train_path,
        "valid_candidates": valid_path,
        "test_candidates": test_path,
        "summary": summary_path,
        "report": args.report_path,
    }

    write_jsonl(all_path, selected)
    write_jsonl(train_path, [row for row in selected if row.get("split") == "train"])
    write_jsonl(valid_path, [row for row in selected if row.get("split") == "valid"])
    write_jsonl(test_path, [row for row in selected if row.get("split") == "test"])
    summary = {
        "pool": str(args.pool),
        "records_in_pool": len(records),
        "known_labeled_ids_seen": len(labeled_ids),
        "pool_records_excluded_by_id": excluded_overlap,
        "unlabeled_records_available": len(unlabeled),
        "selected_records": len(selected),
        "bucket_counts": dict(Counter(row["selection"]["bucket"] for row in selected)),
        "source_counts": dict(Counter(row.get("source") for row in selected)),
        "split_counts": dict(Counter(row.get("split") for row in selected)),
        "clean_status_counts": dict(Counter(clean_status(row) for row in selected)),
        "pool_sizes_by_bucket": pool_sizes,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(args.report_path, selected, specs, pool_sizes, outputs, labeled_ids, excluded_overlap)

    print(json.dumps({"outputs": {k: str(v) for k, v in outputs.items()}, "summary": summary}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
