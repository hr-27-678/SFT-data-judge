"""Sample a supplement to evergreen_test to reach a 500-record total.

Same lock policy as evergreen_test: these ids must NEVER be passed to
`scripts/09_build_binary_scorer_sft.py`. They are a permanent cross-version
evaluation set.

The original evergreen_test has 200 clean records (cot_zh 120 / finetome 50
/ openmath 30). This supplement adds 300 more clean records to reach 500 total
at the same 60/25/15 source ratio. Flagged records cannot be sampled because
the 5,000 pool's flagged subset was fully consumed by v2active002 priority.
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
        "--pool",
        type=Path,
        default=PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v3_unlabeled_pool_5000" / "teacher_candidates_all.jsonl",
    )
    p.add_argument(
        "--exclude",
        type=Path,
        action="append",
        default=None,
        help="Repeatable. Default excludes v2active002 + evergreen_test.",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test_supplement",
    )
    p.add_argument(
        "--report-path",
        type=Path,
        default=PROJECT_ROOT / "reports" / "evergreen_test_supplement_sampling_report.md",
    )
    p.add_argument("--quota-cot-zh", type=int, default=180)
    p.add_argument("--quota-finetome", type=int, default=75)
    p.add_argument("--quota-openmath", type=int, default=45)
    p.add_argument("--seed", type=int, default=20260506)
    p.add_argument("--batch-prefix", type=str, default="evergreen_test_supplement")
    p.add_argument("--rank-offset", type=int, default=200,
                   help="Continue selection_rank numbering after the original 200.")
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


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    if args.exclude is None:
        args.exclude = [
            PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v2_active_pilot_002" / "v2active002_teacher_candidates_all.jsonl",
            PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test" / "teacher_candidates_all.jsonl",
        ]

    pool = read_jsonl(args.pool)
    excluded_ids: set[str] = set()
    for path in args.exclude:
        excluded_ids.update(r["id"] for r in read_jsonl(path))

    eligible = [r for r in pool if r["id"] not in excluded_ids and r.get("is_clean")]

    by_source: dict[str, list[dict[str, Any]]] = {}
    for r in eligible:
        by_source.setdefault(r["source"], []).append(r)

    quotas = {
        "cot_zh": args.quota_cot_zh,
        "finetome": args.quota_finetome,
        "openmath_reasoning": args.quota_openmath,
    }

    selected: list[dict[str, Any]] = []
    actual_quota: dict[str, int] = {}
    for source, want in quotas.items():
        bucket = by_source.get(source, [])
        rng.shuffle(bucket)
        chosen = bucket[:want]
        actual_quota[source] = len(chosen)
        selected.extend(chosen)

    rng.shuffle(selected)

    out_records: list[dict[str, Any]] = []
    for index, record in enumerate(selected):
        row = dict(record)
        for k in ("conservative_verdict", "confident_verdict", "agreement_bucket",
                  "priority_reasons", "selection_reason"):
            row.pop(k, None)
        selection = dict(row.get("selection") or {})
        rank = args.rank_offset + index
        selection.update({
            "batch_prefix": args.batch_prefix,
            "selection_rank": rank,
            "selection_reason": "evergreen_test_baseline",
            "policy": "never_use_for_training_or_validation",
        })
        row["selection"] = selection
        row["teacher_sample_id"] = f"{args.batch_prefix}_{rank:05d}"
        row["teacher_label"] = None
        row["raw_teacher_response"] = None
        row["validation_errors"] = []
        out_records.append(row)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    all_path = args.output_dir / "teacher_candidates_all.jsonl"
    write_jsonl(all_path, out_records)

    source_counts = Counter(r["source"] for r in out_records)

    lines = [
        "# Evergreen Baseline Test Supplement Sampling Report",
        "",
        "## Purpose",
        "",
        "Supplement to `evergreen_test` (200 records) to reach a 500-record",
        "total cross-version evaluation set at the 60/25/15 source ratio.",
        "Same lock policy: NEVER passed to training.",
        "",
        "## Inputs",
        "",
        f"- Source pool: `{args.pool}` ({len(pool)} records)",
        f"- Excluded: {len(excluded_ids)} ids "
        f"(v2active002 candidates + evergreen_test candidates)",
        f"- Eligible clean pool: {len(eligible)} records",
        "",
        "## Outputs",
        "",
        f"- Candidates: `{all_path.relative_to(PROJECT_ROOT)}`",
        "",
        "## Selected By Source",
        "",
        "| Source | Records | Combined with v1 (target 500) |",
        "| --- | ---: | ---: |",
        f"| cot_zh | {source_counts.get('cot_zh', 0)} | {source_counts.get('cot_zh', 0) + 120} |",
        f"| finetome | {source_counts.get('finetome', 0)} | {source_counts.get('finetome', 0) + 50} |",
        f"| openmath_reasoning | {source_counts.get('openmath_reasoning', 0)} | {source_counts.get('openmath_reasoning', 0) + 30} |",
        f"| **Total** | **{len(out_records)}** | **{len(out_records) + 200}** |",
        "",
        "## Note",
        "",
        "All records are clean. The 5,000 pool's flagged subset was fully",
        "consumed by `v2active002` priority queue, so flagged-record edge",
        "coverage is deferred to a future evergreen_test_v2 batch.",
        "",
        "## Next Step",
        "",
        "Run teacher labeling on this batch (parallel-safe with the original",
        "evergreen_test job and the v2active002 job):",
        "",
        "```powershell",
        f"python scripts/04_teacher_judge.py `",
        f"  --input {all_path.relative_to(PROJECT_ROOT)} `",
        f"  --output-dir data/labeled/teacher_judge/{args.batch_prefix} `",
        f"  --output-name {args.batch_prefix}_teacher_labels.jsonl `",
        "  --no-dry-run --resume",
        "```",
        "",
        "After this and `evergreen_test` both finish, the combined 500",
        "records form the cross-version baseline. The evaluation script",
        "`scripts/17_evaluate_on_evergreen.py` (TBD) will read both label",
        "files together and compute one comparison table.",
        "",
    ]
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "pool_total": len(pool),
        "excluded": len(excluded_ids),
        "eligible_clean": len(eligible),
        "selected": len(out_records),
        "by_source": dict(source_counts),
        "combined_with_v1": {
            "cot_zh": source_counts.get("cot_zh", 0) + 120,
            "finetome": source_counts.get("finetome", 0) + 50,
            "openmath_reasoning": source_counts.get("openmath_reasoning", 0) + 30,
            "total": len(out_records) + 200,
        },
        "outputs": {
            "candidates": str(all_path),
            "report": str(args.report_path),
        },
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
