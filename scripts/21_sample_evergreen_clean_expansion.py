"""Sample evergreen clean expansion: cot_zh 200 + finetome 100.

Current evergreen has too few true negatives per source to estimate
not_keep recall reliably:

- openmath clean has 9 true negatives (unusable)
- finetome clean has 24 true negatives
- cot_zh clean has 86 true negatives (workable but tight)

This batch enlarges the cot_zh and finetome clean true-negative pools.
At ~24-29% true drop rate, 200 cot_zh + 100 finetome adds roughly
~58 cot_zh + ~24 finetome new true negatives, lifting per-source
not_keep support to ~144 cot_zh + ~48 finetome.

openmath is intentionally skipped: its true drop rate is too low to
justify another 100 records of which ~12 would be true negatives.

Selection rule:
- source in {cot_zh, finetome}
- is_clean = True
- length-stratified equal-thirds (short/medium/long) within each source
- excluded against ALL prior teacher labels + locked + every evergreen
  reservation + every active-learning candidate file + v4 supplements

Output:
- data/splits/teacher_judge/evergreen_clean_expansion/teacher_candidates_all.jsonl

After teacher labeling, the labels can be merged into evergreen v2
(planned, not done by this script).
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "by_source"
OUT_DIR = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_clean_expansion"
REPORT_PATH = PROJECT_ROOT / "reports" / "evergreen_clean_expansion_sampling_report.md"

SOURCE_QUOTAS = {
    "cot_zh": 200,
    "finetome": 100,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=20260507)
    p.add_argument("--batch-prefix", type=str, default="evergreen_clean_expansion")
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
        PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v4_cot_zh_short_clean" / "teacher_candidates_all.jsonl",
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


def length_bucket(record: dict[str, Any], q33: int, q66: int) -> str:
    n = int(record.get("output_len", 0))
    if n <= q33:
        return "short"
    if n <= q66:
        return "medium"
    return "long"


def stratified_sample(records: list[dict[str, Any]], target: int, rng: random.Random) -> list[dict[str, Any]]:
    if not records or target <= 0:
        return []
    output_lens = sorted(int(r.get("output_len", 0)) for r in records)
    n = len(output_lens)
    q33 = output_lens[n // 3] if n >= 3 else output_lens[0]
    q66 = output_lens[2 * n // 3] if n >= 3 else output_lens[-1]
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        buckets[length_bucket(r, q33, q66)].append(r)
    per_bucket = target // 3
    rem = target - per_bucket * 3
    selected: list[dict[str, Any]] = []
    for i, b in enumerate(("short", "medium", "long")):
        want = per_bucket + (1 if i < rem else 0)
        pool = buckets[b]
        rng.shuffle(pool)
        selected.extend(pool[:want])
    return selected


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    excluded = load_excluded_ids()
    print(f"excluded reservations: {len(excluded)}")

    selected: list[dict[str, Any]] = []
    eligible_counts: dict[str, int] = {}
    for source, want in SOURCE_QUOTAS.items():
        all_recs = read_jsonl(PROCESSED_DIR / f"{source}.jsonl")
        eligible = [r for r in all_recs if r.get("is_clean") and r.get("id") not in excluded]
        eligible_counts[source] = len(eligible)
        sampled = stratified_sample(eligible, want, rng)
        print(f"  {source}: sampled {len(sampled)}/{want} (eligible pool {len(eligible)})")
        selected.extend(sampled)

    rng.shuffle(selected)

    out_records: list[dict[str, Any]] = []
    for index, record in enumerate(selected):
        c = dict(record)
        c["teacher_sample_id"] = f"{args.batch_prefix}_{index:05d}"
        c["selection"] = {
            "batch_prefix": args.batch_prefix,
            "selection_rank": index,
            "selection_reason": "evergreen_clean_true_negative_expansion",
            "policy": "cot_zh_finetome_clean_length_stratified",
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
            "# Evergreen Clean Expansion Sampling Report",
            "",
            "## Purpose",
            "",
            "Enlarge cot_zh and finetome clean true-negative pools so per-source",
            "not_keep recall on evergreen v2 has stable estimates.",
            "",
            "## Inputs",
            "",
            f"- Excluded reservations: {len(excluded)}.",
            *[f"- {s} clean eligible pool: {eligible_counts.get(s, 0)}." for s in SOURCE_QUOTAS],
            "",
            "## Outputs",
            "",
            f"- Candidates: `data/splits/teacher_judge/{args.batch_prefix}/teacher_candidates_all.jsonl`",
            f"  ({len(out_records)} records).",
            "",
            "## By Source",
            "",
            "| Source | Records | Quota |",
            "| --- | ---: | ---: |",
            *[f"| {s} | {by_source.get(s, 0)} | {SOURCE_QUOTAS[s]} |" for s in SOURCE_QUOTAS],
            f"| **Total** | **{len(out_records)}** | **{sum(SOURCE_QUOTAS.values())}** |",
            "",
            "## Next Steps",
            "",
            "1. DeepSeek-label these records:",
            "",
            "```powershell",
            "python scripts/04_teacher_judge.py `",
            f"  --input data/splits/teacher_judge/{args.batch_prefix}/teacher_candidates_all.jsonl `",
            f"  --output-dir data/labeled/teacher_judge/{args.batch_prefix} `",
            f"  --output-name {args.batch_prefix}_teacher_labels.jsonl `",
            "  --no-dry-run --resume",
            "```",
            "",
            "2. Merge into evergreen v2 (separate task, not handled here).",
            "",
        ]),
        encoding="utf-8",
    )
    print(f"wrote report: {REPORT_PATH.name}")


if __name__ == "__main__":
    main()
