"""Sample 1,000 random clean records as a v4 training supplement.

Plan B v4 strategy: the existing v2active002 active-learning batch is
heavily biased toward boundary cases (model disagreements + both_not_keep
+ flagged_but_keep). The evergreen evaluation showed the scorers learned a
"rule_clean=True -> keep" shortcut and barely discriminate inside the
clean stratum. Active-learning records cannot fix this, because they
themselves are not random clean.

This batch adds 1,000 fresh records sampled from the 188K production pool
with the same source distribution as production (38/52/10). Expected
~24% drop rate per teacher -> ~240 new "clean but actually drop" training
examples. Combined with the prompt-template change (drop rule_clean and
rule_flags fields, see scripts/09_build_binary_scorer_sft.py
--no-rule-fields), this aims to break the rule-flag shortcut.

Output:
- `data/splits/teacher_judge/v4_random_supplement/teacher_candidates_all.jsonl`
- After teacher labeling, the labels are passed to scripts/09 as a regular
  --label-prefix arg when building v4 binary datasets.
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
OUT_DIR = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v4_random_supplement"
REPORT_PATH = PROJECT_ROOT / "reports" / "v4_random_supplement_sampling_report.md"

PRODUCTION_RATIO = {
    "cot_zh": 0.386,
    "finetome": 0.516,
    "openmath_reasoning": 0.099,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--total", type=int, default=1000)
    p.add_argument("--seed", type=int, default=20260507)
    p.add_argument("--batch-prefix", type=str, default="v4_random_supplement")
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

    quotas = {s: round(args.total * r) for s, r in PRODUCTION_RATIO.items()}
    drift = args.total - sum(quotas.values())
    quotas["finetome"] += drift

    selected: list[dict[str, Any]] = []
    for source, want in quotas.items():
        all_recs = read_jsonl(PROCESSED_DIR / f"{source}.jsonl")
        eligible = [r for r in all_recs if r.get("is_clean") and r.get("id") not in excluded]
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
            "selection_reason": "v4_random_clean_supplement",
            "policy": "production_distribution_random_clean",
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
            "# v4 Random Clean Supplement Sampling Report",
            "",
            "## Purpose",
            "",
            "Plan B v4 strategy supplement: 1,000 random clean records from",
            "the 188K production pool, source-stratified at 38/52/10 to match",
            "production. All `is_clean=True`. Goal: provide ~240 new",
            "production-distribution clean+not_keep training examples to",
            "break the rule-flag shortcut.",
            "",
            "## Inputs",
            "",
            f"- Excluded reservations: {len(excluded)} (all teacher-labeled + locked + v2active002 + evergreen).",
            "",
            "## Outputs",
            "",
            f"- Candidates: `data/splits/teacher_judge/v4_random_supplement/teacher_candidates_all.jsonl`",
            "  ({total} records).".format(total=len(out_records)),
            "",
            "## By Source",
            "",
            "| Source | Records | Production target |",
            "| --- | ---: | ---: |",
            *[f"| {s} | {by_source.get(s,0)} | {PRODUCTION_RATIO[s]*100:.1f}% |"
              for s in PRODUCTION_RATIO],
            f"| **Total** | **{len(out_records)}** | 100% |",
            "",
            "## Next Steps",
            "",
            "1. DeepSeek-label these 1,000 records:",
            "",
            "```powershell",
            "python scripts/04_teacher_judge.py `",
            f"  --input data/splits/teacher_judge/{args.batch_prefix}/teacher_candidates_all.jsonl `",
            f"  --output-dir data/labeled/teacher_judge/{args.batch_prefix} `",
            f"  --output-name {args.batch_prefix}_teacher_labels.jsonl `",
            "  --no-dry-run --resume",
            "```",
            "",
            "2. After labeling completes, pass this batch to",
            "   `scripts/09_build_binary_scorer_sft.py` with `--no-rule-fields`",
            "   (Plan B prompt change) to build v4 binary scorer datasets.",
            "",
        ]),
        encoding="utf-8",
    )
    print(f"wrote report: {REPORT_PATH.name}")


if __name__ == "__main__":
    main()
