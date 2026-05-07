"""Analyze v3 conservative/confident scorer agreement on an unlabeled pool.

Joins both prediction files by `id`, builds the 4-bucket agreement matrix
(overall / by source / by rule-flag), and emits:

- `data/scored/<pool>_model_agreement_metrics.json`
- `data/scored/<pool>_model_disagreements.jsonl`
- `data/scored/<pool>_teacher_review_priority.jsonl` (priority + calibration)
- `reports/<pool>_model_agreement_report.md`

The priority JSONL is the input expected by `scripts/13_build_teacher_review_batch.py`.

Calibration random samples are drawn from `conf_keep__cons_keep` and
`conf_not_keep__cons_not_keep` so the next teacher batch can also surface
silent agreement errors (where both scorers agree but teacher would disagree).
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="V3 scorer agreement analysis on unlabeled pool.")
    p.add_argument("--pool-name", type=str, default="v3_unlabeled_pool_5000")
    p.add_argument(
        "--pool-source",
        type=Path,
        default=PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v3_unlabeled_pool_5000" / "teacher_candidates_all.jsonl",
    )
    p.add_argument(
        "--conservative",
        type=Path,
        default=PROJECT_ROOT / "data" / "scored" / "v3_unlabeled_pool_5000_conservative_predictions.jsonl",
    )
    p.add_argument(
        "--confident",
        type=Path,
        default=PROJECT_ROOT / "data" / "scored" / "v3_unlabeled_pool_5000_confident_predictions.jsonl",
    )
    p.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data" / "scored")
    p.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports")
    p.add_argument("--calibration-keep", type=int, default=100,
                   help="Random sample size from conf_keep__cons_keep.")
    p.add_argument("--calibration-not-keep", type=int, default=50,
                   help="Random sample size from conf_not_keep__cons_not_keep.")
    p.add_argument("--seed", type=int, default=20260506)
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


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def agreement_bucket(cons_v: str, conf_v: str) -> str:
    return f"conf_{conf_v}__cons_{cons_v}"


def priority_reasons_for(record: dict[str, Any]) -> list[str]:
    cons = record["conservative_verdict"]
    conf = record["confident_verdict"]
    is_clean = bool(record.get("is_clean"))
    reasons: list[str] = []
    if cons != conf:
        reasons.append("model_disagreement")
    if cons == "not_keep" and conf == "not_keep":
        reasons.append("both_not_keep")
    if cons == "not_keep" and is_clean:
        reasons.append("conservative_clean_not_keep")
    if conf == "not_keep" and is_clean:
        reasons.append("confident_clean_not_keep")
    if not is_clean and (cons == "keep" or conf == "keep"):
        reasons.append("flagged_but_model_keep")
    return reasons


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    pool = {r["id"]: r for r in read_jsonl(args.pool_source)}
    cons_preds = {r["id"]: r for r in read_jsonl(args.conservative)}
    conf_preds = {r["id"]: r for r in read_jsonl(args.confident)}

    common_ids = set(pool) & set(cons_preds) & set(conf_preds)
    missing = (set(pool) - common_ids) | (set(cons_preds) - common_ids) | (set(conf_preds) - common_ids)
    if missing:
        print(f"[warn] {len(missing)} ids missing from one of the three sources; ignoring.")

    joined: list[dict[str, Any]] = []
    for sid in common_ids:
        base = dict(pool[sid])
        base["conservative_verdict"] = cons_preds[sid]["verdict"]
        base["confident_verdict"] = conf_preds[sid]["verdict"]
        base["agreement_bucket"] = agreement_bucket(base["conservative_verdict"], base["confident_verdict"])
        base["priority_reasons"] = priority_reasons_for(base)
        joined.append(base)

    bucket_counts: Counter[str] = Counter(r["agreement_bucket"] for r in joined)
    by_source: defaultdict[str, Counter[str]] = defaultdict(Counter)
    by_clean: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for r in joined:
        by_source[r["source"]][r["agreement_bucket"]] += 1
        by_clean["clean" if r.get("is_clean") else "flagged"][r["agreement_bucket"]] += 1

    agree = bucket_counts.get("conf_keep__cons_keep", 0) + bucket_counts.get("conf_not_keep__cons_not_keep", 0)
    disagree = len(joined) - agree

    priority_records = [r for r in joined if r["priority_reasons"]]

    keep_keep = [r for r in joined if r["agreement_bucket"] == "conf_keep__cons_keep"]
    nk_nk = [r for r in joined if r["agreement_bucket"] == "conf_not_keep__cons_not_keep"]
    cal_keep = rng.sample(keep_keep, min(args.calibration_keep, len(keep_keep)))
    cal_nk = rng.sample(nk_nk, min(args.calibration_not_keep, len(nk_nk)))

    priority_ids = {r["id"] for r in priority_records}
    calibration_records: list[dict[str, Any]] = []
    for r in cal_keep + cal_nk:
        if r["id"] in priority_ids:
            continue
        cr = dict(r)
        cr["priority_reasons"] = ["calibration_random"]
        cr["selection_reason"] = "calibration"
        calibration_records.append(cr)

    for r in priority_records:
        r["selection_reason"] = "priority"

    combined = priority_records + calibration_records

    disagreements = [r for r in joined if r["conservative_verdict"] != r["confident_verdict"]]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = args.output_dir / f"{args.pool_name}_model_agreement_metrics.json"
    disagree_path = args.output_dir / f"{args.pool_name}_model_disagreements.jsonl"
    priority_path = args.output_dir / f"{args.pool_name}_teacher_review_priority.jsonl"
    report_path = args.report_dir / f"{args.pool_name}_model_agreement_report.md"

    metrics = {
        "pool": args.pool_name,
        "records": len(joined),
        "agree": agree,
        "disagree": disagree,
        "agreement_rate": round(agree / len(joined), 6) if joined else 0.0,
        "buckets": dict(bucket_counts),
        "by_source": {s: dict(c) for s, c in by_source.items()},
        "by_clean_flag": {k: dict(c) for k, c in by_clean.items()},
        "priority_records": len(priority_records),
        "priority_by_reason": dict(Counter(reason for r in priority_records for reason in r["priority_reasons"])),
        "calibration_keep_keep": len(cal_keep),
        "calibration_nk_nk": len(cal_nk),
        "calibration_after_dedup": len(calibration_records),
        "combined_priority_plus_calibration": len(combined),
    }

    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    write_jsonl(disagree_path, disagreements)
    write_jsonl(priority_path, combined)

    sources_sorted = sorted(by_source)
    buckets_sorted = ["conf_keep__cons_keep", "conf_keep__cons_not_keep",
                      "conf_not_keep__cons_keep", "conf_not_keep__cons_not_keep"]

    lines = [
        f"# {args.pool_name} Model Agreement Report",
        "",
        "## Report Metadata",
        "",
        md_table(["Field", "Value"], [
            ["Generated", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Report type", "Model agreement / active-learning triage"],
            ["Project stage", "V3 scorer deployment / teacher relabeling selection"],
            ["Report status", "Generated"],
        ]),
        "",
        "## Experiment Context",
        "",
        md_table(["Field", "Value"], [
            ["Input pool", f"`{args.pool_source}`"],
            ["Records", len(joined)],
            ["Conservative model", "scorer_binary_v3_conservative_qwen3_8b_lora_e3"],
            ["Confident model", "scorer_binary_v3_confident_qwen3_8b_lora_e3"],
            ["Pool teacher-label exclusion", "applied at sampling time (script 02)"],
            ["Locked test overlap", "verified 0 (2026-05-06)"],
        ]),
        "",
        "## Headline",
        "",
        f"The two Qwen3-8B v3 scorers agree on {agree} / {len(joined)} records "
        f"({agree/len(joined)*100:.2f}%) and disagree on {disagree} records.",
        "",
        "## Agreement Buckets",
        "",
        md_table(["bucket", "count"], [[b, bucket_counts.get(b, 0)] for b in buckets_sorted]),
        "",
        "## By Source",
        "",
        md_table(["source"] + buckets_sorted,
                 [[s] + [by_source[s].get(b, 0) for b in buckets_sorted] for s in sources_sorted]),
        "",
        "## By Rule Flag",
        "",
        md_table(["rule status"] + buckets_sorted,
                 [[k] + [by_clean[k].get(b, 0) for b in buckets_sorted] for k in sorted(by_clean)]),
        "",
        "## Priority Queue",
        "",
        md_table(["Metric", "Count"], [
            ["Priority records (any reason)", len(priority_records)],
            ["Calibration random (after dedup vs priority)", len(calibration_records)],
            ["Combined output rows", len(combined)],
        ]),
        "",
        "## Priority Records By Reason",
        "",
        md_table(["reason", "count"],
                 sorted(metrics["priority_by_reason"].items(), key=lambda x: -x[1])),
        "",
        "## Outputs",
        "",
        md_table(["Artifact", "Path"], [
            ["Agreement metrics", f"`{metrics_path}`"],
            ["Disagreements JSONL", f"`{disagree_path}`"],
            ["Priority + calibration JSONL", f"`{priority_path}`"],
        ]),
        "",
        "## Interpretation",
        "",
        "- `conf_keep__cons_keep`: most likely usable; sampled randomly as calibration to detect silent scorer errors.",
        "- `conf_keep__cons_not_keep`: conservative-only rejection; tests if conservative is over-rejecting.",
        "- `conf_not_keep__cons_keep`: confident-only rejection; small but high-signal boundary cases.",
        "- `conf_not_keep__cons_not_keep`: strongest hard-negative candidates; sampled randomly as calibration too.",
        "- `calibration_random`: marked with `selection_reason=calibration` so downstream analysis can",
        "  separately measure how often teacher disagrees with both scorers when both scorers agree.",
        "",
        "## Next Step",
        "",
        f"Run `scripts/13_build_teacher_review_batch.py` with `--input {priority_path}`",
        "and a fresh `--batch-prefix` (e.g. `v2active002`) to dedup against existing teacher labels",
        "and produce the next teacher-labeling batch.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "records": len(joined),
        "agree": agree,
        "disagree": disagree,
        "agreement_rate": round(agree / len(joined), 4) if joined else 0.0,
        "priority_records": len(priority_records),
        "calibration_records": len(calibration_records),
        "combined": len(combined),
        "outputs": {
            "metrics": str(metrics_path),
            "disagreements": str(disagree_path),
            "priority": str(priority_path),
            "report": str(report_path),
        },
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
