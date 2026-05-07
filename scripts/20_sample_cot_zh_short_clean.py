"""Sample cot_zh short-clean records as a v4 targeted supplement.

Evergreen evaluation showed cot_zh is the weakest source inside the clean
stratum: 86/300 true not_keep on evergreen clean cot_zh, but v3 conservative
recall only 12.79%. Short cot_zh records have the highest expected drop
rate. This batch directly enlarges that hardest sub-slice.

Selection rule:
- source = cot_zh
- is_clean = True
- length bucket = short (<= per-source 33rd percentile of output_len)
- excluded against all prior teacher labels + locked + evergreen
  + v2active002 + v4_random_supplement candidates

Output:
- data/splits/teacher_judge/v4_cot_zh_short_clean/teacher_candidates_all.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "by_source"
OUT_DIR = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v4_cot_zh_short_clean"
REPORT_PATH = PROJECT_ROOT / "reports" / "v4_cot_zh_short_clean_sampling_report.md"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--total", type=int, default=300)
    p.add_argument("--seed", type=int, default=20260507)
    p.add_argument("--batch-prefix", type=str, default="v4_cot_zh_short_clean")
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
        PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "starter_1000_teacher_labels.jsonl",
        PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "targeted_1200_teacher_labels.jsonl",
        PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "v2active001" / "v2active001_teacher_labels.jsonl",
        PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v2_active_pilot_002" / "v2active002_teacher_candidates_all.jsonl",
        PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test" / "teacher_candidates_all.jsonl",
        PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test_extension" / "teacher_candidates_all.jsonl",
        PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v4_random_supplement" / "teacher_candidates_all.jsonl",
    ]
    for p in paths:
        if p.exists():
            for r in read_jsonl(p):
                if r.get("id"):
                    excluded.add(r["id"])

    locked = PROJECT_ROOT / "data" / "eval" / "locked_test_ids.json"
    if locked.exists():
        excluded.update(json.loads(locked.read_text(encoding="utf-8")).get("ids", []))

    evergreen = PROJECT_ROOT / "data" / "eval" / "evergreen_test_ids.json"
    if evergreen.exists():
        excluded.update(json.loads(evergreen.read_text(encoding="utf-8")).get("ids", []))

    return excluded


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    excluded = load_excluded_ids()
    print(f"excluded reservations: {len(excluded)}")

    all_recs = read_jsonl(PROCESSED_DIR / "cot_zh.jsonl")
    print(f"cot_zh total: {len(all_recs)}")

    eligible = [r for r in all_recs if r.get("is_clean") and r.get("id") not in excluded]
    print(f"cot_zh clean eligible: {len(eligible)}")

    output_lens = sorted(int(r.get("output_len", 0)) for r in eligible)
    q33 = output_lens[len(output_lens) // 3]
    print(f"short cutoff (output_len <= {q33})")

    short_pool = [r for r in eligible if int(r.get("output_len", 0)) <= q33]
    print(f"short pool: {len(short_pool)}")

    rng.shuffle(short_pool)
    selected = short_pool[: args.total]

    out_records: list[dict[str, Any]] = []
    for index, record in enumerate(selected):
        c = dict(record)
        c["teacher_sample_id"] = f"{args.batch_prefix}_{index:05d}"
        c["selection"] = {
            "batch_prefix": args.batch_prefix,
            "selection_rank": index,
            "selection_reason": "v4_cot_zh_short_clean_targeted",
            "policy": "cot_zh_only_clean_only_short_bucket",
            "short_cutoff_output_len": q33,
        }
        c["teacher_label"] = None
        c["raw_teacher_response"] = None
        c["validation_errors"] = []
        out_records.append(c)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "teacher_candidates_all.jsonl"
    write_jsonl(out_path, out_records)

    by_source = Counter(r["source"] for r in out_records)
    print(f"\nselected {len(out_records)} records: {dict(by_source)}")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join([
            "# v4 cot_zh Short-Clean Targeted Sampling Report",
            "",
            "## Purpose",
            "",
            "Evergreen evaluation isolated cot_zh clean as the weakest slice",
            "for current scorers (true drop rate ~28.7%, v3 cons recall 12.79%).",
            "Short cot_zh records dominate the failure mode. This batch",
            f"adds {len(out_records)} cot_zh short-clean records to v4.",
            "",
            "## Inputs",
            "",
            f"- Excluded reservations: {len(excluded)}.",
            f"- cot_zh clean eligible pool: {len(eligible)}.",
            f"- Short bucket cutoff: output_len <= {q33}.",
            f"- Short pool size: {len(short_pool)}.",
            "",
            "## Outputs",
            "",
            f"- Candidates: `data/splits/teacher_judge/{args.batch_prefix}/teacher_candidates_all.jsonl`",
            f"  ({len(out_records)} records).",
            "",
            "## Next Steps",
            "",
            "Label with DeepSeek:",
            "",
            "```powershell",
            "python scripts/04_teacher_judge.py `",
            f"  --input data/splits/teacher_judge/{args.batch_prefix}/teacher_candidates_all.jsonl `",
            f"  --output-dir data/labeled/teacher_judge/{args.batch_prefix} `",
            f"  --output-name {args.batch_prefix}_teacher_labels.jsonl `",
            "  --no-dry-run --resume",
            "```",
            "",
        ]),
        encoding="utf-8",
    )
    print(f"wrote report: {REPORT_PATH.name}")


if __name__ == "__main__":
    main()
