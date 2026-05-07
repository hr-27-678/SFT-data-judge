"""Sample 100 flagged records from the full 188K processed pool to add a
flagged stratum to evergreen_test.

The 5,000 pool's flagged records were fully consumed by v2active002 priority,
so flagged samples must come from the broader 188K pool. All teacher-labeled
ids and all reserved-for-eval ids are excluded.

Same lock policy: NEVER passed to training. After teacher labeling, these
ids form the flagged stratum of the cross-version evergreen evaluation set.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--processed-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed" / "by_source",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test_flagged",
    )
    p.add_argument(
        "--report-path",
        type=Path,
        default=PROJECT_ROOT / "reports" / "evergreen_test_flagged_sampling_report.md",
    )
    p.add_argument("--quota-cot-zh", type=int, default=40)
    p.add_argument("--quota-finetome", type=int, default=60)
    p.add_argument(
        "--exclude-flag",
        action="append",
        default=None,
        help="Repeatable. Exclude records that carry this flag. Default: duplicate_pair.",
    )
    p.add_argument("--seed", type=int, default=20260506)
    p.add_argument("--batch-prefix", type=str, default="evergreen_test_flagged")
    p.add_argument("--rank-offset", type=int, default=500,
                   help="Continue numbering after the 500-record clean evergreen.")
    return p.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_excluded_ids() -> set[str]:
    excluded: set[str] = set()
    paths = [
        PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "pilot_teacher_labels.jsonl",
        PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "teacher_labels_1000.jsonl",
        PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "targeted_1200_teacher_labels.jsonl",
        PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "v2active001" / "v2active001_teacher_labels.jsonl",
        PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v2_active_pilot_002" / "v2active002_teacher_candidates_all.jsonl",
        PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test" / "teacher_candidates_all.jsonl",
        PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test_supplement" / "teacher_candidates_all.jsonl",
    ]
    for path in paths:
        if path.exists():
            for r in read_jsonl(path):
                if r.get("id"):
                    excluded.add(r["id"])

    locked_path = PROJECT_ROOT / "data" / "eval" / "locked_test_ids.json"
    if locked_path.exists():
        with locked_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        excluded.update(data.get("ids", []))

    return excluded


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    excluded_ids = load_excluded_ids()
    exclude_flags = set(args.exclude_flag) if args.exclude_flag else {"duplicate_pair"}

    quotas = {"cot_zh": args.quota_cot_zh, "finetome": args.quota_finetome}
    selected: list[dict[str, Any]] = []
    actual: dict[str, int] = {}

    for source, want in quotas.items():
        path = args.processed_dir / f"{source}.jsonl"
        bucket = [
            r for r in read_jsonl(path)
            if not r.get("is_clean")
            and r.get("id") not in excluded_ids
            and not (set(r.get("flags") or []) & exclude_flags)
        ]
        rng.shuffle(bucket)
        chosen = bucket[:want]
        actual[source] = len(chosen)
        selected.extend(chosen)

    rng.shuffle(selected)

    out_records: list[dict[str, Any]] = []
    for index, record in enumerate(selected):
        row = dict(record)
        rank = args.rank_offset + index
        row["teacher_sample_id"] = f"{args.batch_prefix}_{rank:05d}"
        row["selection"] = {
            "batch_prefix": args.batch_prefix,
            "selection_rank": rank,
            "selection_reason": "evergreen_test_baseline_flagged",
            "policy": "never_use_for_training_or_validation",
        }
        row["teacher_label"] = None
        row["raw_teacher_response"] = None
        row["validation_errors"] = []
        if "split" not in row:
            row["split"] = "test"
        out_records.append(row)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    all_path = args.output_dir / "teacher_candidates_all.jsonl"
    write_jsonl(all_path, out_records)

    source_counts = Counter(r["source"] for r in out_records)
    flag_counter: Counter[str] = Counter()
    for r in out_records:
        for flag in r.get("flags", []):
            flag_counter[flag] += 1

    lines = [
        "# Evergreen Baseline Test Flagged Stratum Sampling Report",
        "",
        "## Purpose",
        "",
        "Adds a 100-record flagged stratum to the evergreen cross-version test",
        "set so scorer behavior on rule-flagged records can be measured. The",
        "5,000 active-learning pool's flagged subset was fully consumed by",
        "v2active002 priority, so this batch samples directly from the 188K",
        "processed pool. Same lock policy: NEVER passed to training.",
        "",
        "## Inputs",
        "",
        f"- Processed pool: `data/processed/by_source/`",
        f"- Excluded ids (all teacher-labeled + locked + clean evergreen): {len(excluded_ids)}",
        "",
        "## Outputs",
        "",
        f"- Candidates: `{all_path.relative_to(PROJECT_ROOT)}`",
        "",
        "## Selected By Source",
        "",
        "| Source | Records |",
        "| --- | ---: |",
        f"| cot_zh | {source_counts.get('cot_zh', 0)} |",
        f"| finetome | {source_counts.get('finetome', 0)} |",
        f"| **Total** | **{len(out_records)}** |",
        "",
        "## Selected By Flag Type",
        "",
        "| Flag | Records |",
        "| --- | ---: |",
        *(f"| `{flag}` | {count} |" for flag, count in flag_counter.most_common()),
        "",
        "## Combined Evergreen Test Set",
        "",
        f"- Clean (v1 + supplement): 500",
        f"- Flagged (this batch): {len(out_records)}",
        f"- **Combined evergreen total: {500 + len(out_records)}**",
        "",
        "## Next Step",
        "",
        "Run teacher labeling on this batch:",
        "",
        "```powershell",
        f"python scripts/04_teacher_judge.py `",
        f"  --input {all_path.relative_to(PROJECT_ROOT)} `",
        f"  --output-dir data/labeled/teacher_judge/{args.batch_prefix} `",
        f"  --output-name {args.batch_prefix}_teacher_labels.jsonl `",
        "  --no-dry-run --resume",
        "```",
        "",
    ]
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "excluded_ids": len(excluded_ids),
        "selected": len(out_records),
        "by_source": dict(source_counts),
        "by_flag": dict(flag_counter),
        "outputs": {
            "candidates": str(all_path),
            "report": str(args.report_path),
        },
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
