"""Sample the evergreen baseline test set.

These records are reserved as a permanent cross-version evaluation set:
they must NEVER be passed to `scripts/09_build_binary_scorer_sft.py` as
training data. Every scorer (past and future) is evaluated on the same
ids so cross-version metric deltas are honest.

Source: the 5,000-record v3 unlabeled pool, minus the ids selected for
`v2active002`. Sampling is source-stratified to match the pool's
proportions (cot_zh 60%, finetome 25%, openmath_reasoning 15%).
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
        "--exclude-batch",
        type=Path,
        default=PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v2_active_pilot_002" / "v2active002_teacher_candidates_all.jsonl",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test",
    )
    p.add_argument(
        "--report-path",
        type=Path,
        default=PROJECT_ROOT / "reports" / "evergreen_test_sampling_report.md",
    )
    p.add_argument("--total", type=int, default=200)
    p.add_argument("--cot-zh-share", type=float, default=0.60)
    p.add_argument("--finetome-share", type=float, default=0.25)
    p.add_argument("--openmath-share", type=float, default=0.15)
    p.add_argument("--seed", type=int, default=20260506)
    p.add_argument("--batch-prefix", type=str, default="evergreen_test")
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

    pool = read_jsonl(args.pool)
    excluded_ids = {r["id"] for r in read_jsonl(args.exclude_batch)}
    eligible = [r for r in pool if r["id"] not in excluded_ids]

    by_source: dict[str, list[dict[str, Any]]] = {}
    for r in eligible:
        by_source.setdefault(r["source"], []).append(r)

    quotas = {
        "cot_zh": round(args.total * args.cot_zh_share),
        "finetome": round(args.total * args.finetome_share),
        "openmath_reasoning": round(args.total * args.openmath_share),
    }
    diff = args.total - sum(quotas.values())
    quotas["cot_zh"] += diff

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
        row.pop("conservative_verdict", None)
        row.pop("confident_verdict", None)
        row.pop("agreement_bucket", None)
        row.pop("priority_reasons", None)
        row.pop("selection_reason", None)
        selection = dict(row.get("selection") or {})
        selection.update({
            "batch_prefix": args.batch_prefix,
            "selection_rank": index,
            "selection_reason": "evergreen_test_baseline",
            "policy": "never_use_for_training_or_validation",
        })
        row["selection"] = selection
        row["teacher_sample_id"] = f"{args.batch_prefix}_{index:05d}"
        row["teacher_label"] = None
        row["raw_teacher_response"] = None
        row["validation_errors"] = []
        out_records.append(row)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    all_path = args.output_dir / "teacher_candidates_all.jsonl"
    ids_path = PROJECT_ROOT / "data" / "eval" / "evergreen_test_ids.json"

    write_jsonl(all_path, out_records)
    ids_payload = {
        "description": (
            "Evergreen cross-version baseline test ids. These records must "
            "NEVER appear in any scorer training or validation split. They are "
            "reserved as a permanent honest comparison set across all scorer "
            "versions (v1 4B, v1 8B, v2 conservative, v2 confident, v3, v4+)."
        ),
        "locked_date": "2026-05-06",
        "source": str(all_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "count": len(out_records),
        "ids": [r["id"] for r in out_records],
    }
    ids_path.parent.mkdir(parents=True, exist_ok=True)
    with ids_path.open("w", encoding="utf-8") as f:
        json.dump(ids_payload, f, ensure_ascii=False, indent=2)

    source_counts = Counter(r["source"] for r in out_records)
    flag_counts = Counter("flagged" if not r.get("is_clean") else "clean" for r in out_records)

    lines = [
        "# Evergreen Baseline Test Sampling Report",
        "",
        "## Purpose",
        "",
        "Permanent cross-version honest comparison test set. NEVER use these",
        "ids for training or validation. Every scorer (past and future) is",
        "evaluated on the same ids so metric deltas are not contaminated by",
        "training-set leakage.",
        "",
        "## Inputs",
        "",
        f"- Source pool: `{args.pool}` ({len(pool)} records)",
        f"- Excluded batch: `{args.exclude_batch}` ({len(excluded_ids)} ids)",
        f"- Eligible pool: {len(eligible)} records",
        "",
        "## Outputs",
        "",
        f"- Candidates: `{all_path.relative_to(PROJECT_ROOT)}`",
        f"- Locked id list: `{ids_path.relative_to(PROJECT_ROOT)}`",
        "",
        "## Selected By Source",
        "",
        "| Source | Records | Target share |",
        "| --- | ---: | ---: |",
        f"| cot_zh | {source_counts.get('cot_zh', 0)} | {args.cot_zh_share*100:.0f}% |",
        f"| finetome | {source_counts.get('finetome', 0)} | {args.finetome_share*100:.0f}% |",
        f"| openmath_reasoning | {source_counts.get('openmath_reasoning', 0)} | {args.openmath_share*100:.0f}% |",
        f"| **Total** | **{len(out_records)}** | 100% |",
        "",
        "## Selected By Rule Flag",
        "",
        "| Flag status | Records |",
        "| --- | ---: |",
        f"| clean | {flag_counts.get('clean', 0)} |",
        f"| flagged | {flag_counts.get('flagged', 0)} |",
        "",
        "## Next Step",
        "",
        "Run teacher labeling in a SEPARATE PowerShell window (parallel with",
        "the v2active002 labeling job is fine):",
        "",
        "```powershell",
        f"python scripts/04_teacher_judge.py `",
        f"  --input {all_path.relative_to(PROJECT_ROOT)} `",
        f"  --output-dir data/labeled/teacher_judge/{args.batch_prefix} `",
        f"  --output-name {args.batch_prefix}_teacher_labels.jsonl `",
        "  --no-dry-run --resume",
        "```",
        "",
        "After labeling, build a small evaluation script that runs every",
        "scorer adapter against this set and produces a single comparison",
        "table. Do NOT add the labels to `scripts/09_build_binary_scorer_sft.py`",
        "`--label-prefix` arguments.",
        "",
    ]
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "pool_total": len(pool),
        "excluded": len(excluded_ids),
        "eligible": len(eligible),
        "selected": len(out_records),
        "by_source": dict(source_counts),
        "by_clean_flag": dict(flag_counts),
        "outputs": {
            "candidates": str(all_path),
            "ids_lock": str(ids_path),
            "report": str(args.report_path),
        },
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
