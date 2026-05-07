"""Resample the evergreen baseline test set with a corrected design.

Replaces the original 600-record evergreen with a 1,500-record set that
addresses six known blind spots:

1. Source distribution now matches 188K production: 38.6% cot_zh,
   51.6% finetome, 9.9% openmath_reasoning. Old design overweighted
   cot_zh at 60%.
2. Flagged stratum grows from 100 to 300 records for tractable per-source
   CIs, and INCLUDES `duplicate_pair` (the dominant flag in production).
3. Length-stratification (short/medium/long buckets) applied to every
   stratum, so per-length analysis is possible.
4. Per-source minimum 120 records to keep CI under +/- 6%.
5. The 500 already-labeled clean records from the original evergreen
   (`data/labeled/teacher_judge/evergreen_test_salvaged_clean.jsonl`)
   are preserved with their original teacher labels and `teacher_sample_id`.
   Only 1,000 new records (700 clean + 300 flagged) need DeepSeek labeling.
6. The previously-labeled flagged 100 records are discarded because they
   excluded duplicate_pair and so misrepresent production flagged.

After running this script:
- `data/splits/teacher_judge/evergreen_test/teacher_candidates_all.jsonl`
  contains all 1,500 candidates.
- `data/labeled/teacher_judge/evergreen_test/evergreen_test_teacher_labels.jsonl`
  contains the 500 salvaged labels; running `04_teacher_judge.py --resume` on
  the candidates file labels only the remaining 1,000 records.
- `data/eval/evergreen_test_ids.json` is rebuilt with all 1,500 ids.
- The old extension directory and merged label file are archived.
"""

from __future__ import annotations

import json
import random
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "by_source"
SPLITS_OUT = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test"
LABELS_OUT = PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_test"
LOCK_PATH = PROJECT_ROOT / "data" / "eval" / "evergreen_test_ids.json"
SALVAGED = PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_test_salvaged_clean.jsonl"
REPORT_PATH = PROJECT_ROOT / "reports" / "evergreen_test_sampling_report.md"
ARCHIVE_DIR = PROJECT_ROOT / "data" / "_archive" / "evergreen_v0_2026-05-06"

# Production source ratios from the 188K processed pool
PRODUCTION_RATIO = {
    "cot_zh": 0.386,         # 74,771 / 194,023
    "finetome": 0.516,       # 100,000 / 194,023
    "openmath_reasoning": 0.099,
}

# Flagged source ratios (based on which sources actually have flagged records)
# 188K stats: cot_zh 2,416 flagged / finetome 3,439 / openmath 65
FLAGGED_RATIO = {
    "cot_zh": 0.408,
    "finetome": 0.581,
    "openmath_reasoning": 0.011,
}

CLEAN_TARGET = 1200
FLAGGED_TARGET = 300
SEED = 20260506


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
    ]
    for p in paths:
        if p.exists():
            for r in read_jsonl(p):
                if r.get("id"):
                    excluded.add(r["id"])

    locked_path = PROJECT_ROOT / "data" / "eval" / "locked_test_ids.json"
    if locked_path.exists():
        excluded.update(json.loads(locked_path.read_text(encoding="utf-8")).get("ids", []))

    return excluded


def length_bucket(record: dict[str, Any], q33: int, q66: int) -> str:
    n = int(record.get("output_len", 0))
    if n <= q33:
        return "short"
    if n <= q66:
        return "medium"
    return "long"


def stratified_sample(
    records: list[dict[str, Any]],
    target: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Three-bucket length-stratified sample. Returns up to `target` records."""
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
    remainder = target - per_bucket * 3

    selected: list[dict[str, Any]] = []
    for i, b in enumerate(("short", "medium", "long")):
        want = per_bucket + (1 if i < remainder else 0)
        pool = buckets[b]
        rng.shuffle(pool)
        chosen = pool[:want]
        selected.extend(chosen)
        # If a bucket is short, top up by drawing from the remaining pool
        if len(chosen) < want:
            other_pool = [r for b2, recs in buckets.items() if b2 != b for r in recs if r not in chosen]
            rng.shuffle(other_pool)
            shortfall = want - len(chosen)
            selected.extend(other_pool[:shortfall])
    return selected


def main() -> None:
    rng = random.Random(SEED)

    # Salvaged records from the v0 evergreen labeling. The old labels file
    # only preserved metadata (id, source, teacher_sample_id, sampling, etc.)
    # via 04_teacher_judge.py's `base` dict, so we have to re-fetch
    # instruction/output/is_clean/flags from the source pool by id.
    salvaged_labels = read_jsonl(SALVAGED)
    salvaged_ids = {r["id"] for r in salvaged_labels}
    label_by_id = {r["id"]: r for r in salvaged_labels}

    source_record_by_id: dict[str, dict[str, Any]] = {}
    for source in PRODUCTION_RATIO:
        for r in read_jsonl(PROCESSED_DIR / f"{source}.jsonl"):
            if r.get("id") in salvaged_ids:
                source_record_by_id[r["id"]] = r

    salvaged: list[dict[str, Any]] = []
    for sid in salvaged_ids:
        if sid not in source_record_by_id:
            print(f"[warn] salvaged id {sid} not found in source pool, skipping")
            continue
        full = dict(source_record_by_id[sid])
        # Carry over the labeling metadata from the old labels file.
        old = label_by_id[sid]
        full["teacher_sample_id"] = old.get("teacher_sample_id")
        full["pilot_sample_id"] = old.get("pilot_sample_id")
        full["sampling"] = old.get("sampling") or full.get("sampling")
        full["teacher_label"] = old.get("teacher_label")
        full["raw_teacher_response"] = old.get("raw_teacher_response")
        full["validation_errors"] = old.get("validation_errors") or []
        salvaged.append(full)

    salvaged_by_source = Counter(r["source"] for r in salvaged)
    salvaged_ids = {r["id"] for r in salvaged}
    print(f"[1/6] salvaged clean: {len(salvaged)} (by source: {dict(salvaged_by_source)})")

    # Compute clean target gap by source
    clean_target_per_source = {s: round(CLEAN_TARGET * r) for s, r in PRODUCTION_RATIO.items()}
    drift = CLEAN_TARGET - sum(clean_target_per_source.values())
    clean_target_per_source["finetome"] += drift  # absorb rounding
    clean_gap = {s: max(0, clean_target_per_source[s] - salvaged_by_source.get(s, 0)) for s in clean_target_per_source}
    print(f"[2/6] clean target {clean_target_per_source}, gap {clean_gap}")

    flagged_target_per_source = {s: round(FLAGGED_TARGET * r) for s, r in FLAGGED_RATIO.items()}
    drift = FLAGGED_TARGET - sum(flagged_target_per_source.values())
    flagged_target_per_source["finetome"] += drift
    print(f"[2/6] flagged target {flagged_target_per_source}")

    excluded = load_excluded_ids() | salvaged_ids
    print(f"[3/6] excluded ids (labeled + locked + v2active002 + salvaged): {len(excluded)}")

    new_clean: list[dict[str, Any]] = []
    new_flagged: list[dict[str, Any]] = []
    for source in PRODUCTION_RATIO:
        all_recs = read_jsonl(PROCESSED_DIR / f"{source}.jsonl")
        eligible = [r for r in all_recs if r.get("id") not in excluded]
        clean_pool = [r for r in eligible if r.get("is_clean")]
        flagged_pool = [r for r in eligible if not r.get("is_clean")]

        sampled_clean = stratified_sample(clean_pool, clean_gap[source], rng)
        sampled_flagged = stratified_sample(flagged_pool, flagged_target_per_source[source], rng)

        new_clean.extend(sampled_clean)
        new_flagged.extend(sampled_flagged)
        print(f"[4/6] {source}: new clean {len(sampled_clean)}/{clean_gap[source]}, "
              f"new flagged {len(sampled_flagged)}/{flagged_target_per_source[source]}")

    rng.shuffle(new_clean)
    rng.shuffle(new_flagged)

    # Build candidate records.
    # - Salvaged clean records: preserve their original teacher_sample_id so
    #   the existing label file can be reused via --resume.
    # - New clean records: assign new teacher_sample_id with prefix
    #   `evergreen_resample_clean_NNNNN`.
    # - New flagged records: prefix `evergreen_resample_flagged_NNNNN`.
    out_records: list[dict[str, Any]] = []
    for r in salvaged:
        # The candidate file is the input to 04_teacher_judge.py and to
        # downstream inference scripts. teacher_label must be None in the
        # candidate file (resume mode looks at the SEPARATE labels file to
        # decide what to skip).
        c = dict(r)
        c["teacher_label"] = None
        c["raw_teacher_response"] = None
        c["validation_errors"] = []
        out_records.append(c)

    for index, r in enumerate(new_clean):
        c = dict(r)
        c["teacher_sample_id"] = f"evergreen_resample_clean_{index:05d}"
        c["selection"] = {
            "batch_prefix": "evergreen_resample_clean",
            "selection_rank": index,
            "selection_reason": "evergreen_v1_resample",
            "policy": "never_use_for_training_or_validation",
        }
        c["teacher_label"] = None
        c["raw_teacher_response"] = None
        c["validation_errors"] = []
        out_records.append(c)

    for index, r in enumerate(new_flagged):
        c = dict(r)
        c["teacher_sample_id"] = f"evergreen_resample_flagged_{index:05d}"
        c["selection"] = {
            "batch_prefix": "evergreen_resample_flagged",
            "selection_rank": index,
            "selection_reason": "evergreen_v1_resample",
            "policy": "never_use_for_training_or_validation",
        }
        c["teacher_label"] = None
        c["raw_teacher_response"] = None
        c["validation_errors"] = []
        out_records.append(c)

    # Archive old artifacts
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    for src in [
        PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test",
        PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test_extension",
        PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_test",
        PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_test_extension",
    ]:
        if src.exists():
            dest = ARCHIVE_DIR / src.relative_to(PROJECT_ROOT / "data")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))

    merged = PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_test_merged_teacher_labels.jsonl"
    if merged.exists():
        shutil.move(str(merged), str(ARCHIVE_DIR / merged.name))

    # Write new candidates file
    SPLITS_OUT.mkdir(parents=True, exist_ok=True)
    LABELS_OUT.mkdir(parents=True, exist_ok=True)
    candidates_path = SPLITS_OUT / "teacher_candidates_all.jsonl"
    write_jsonl(candidates_path, out_records)
    print(f"[5/6] wrote {len(out_records)} candidates to {candidates_path.name}")

    # Pre-populate labels file with salvaged labels so --resume on the
    # candidates file skips them (record_key == teacher_sample_id is in the
    # completed set).
    labels_path = LABELS_OUT / "evergreen_test_teacher_labels.jsonl"
    write_jsonl(labels_path, salvaged)  # each record has teacher_label set, validation_errors empty
    print(f"[5/6] wrote {len(salvaged)} salvaged labels to {labels_path.name}")

    # Build new lock file
    by_source = Counter(r["source"] for r in out_records)
    by_clean_flag = Counter("clean" if r.get("is_clean") else "flagged" for r in out_records)
    flag_dist: Counter[str] = Counter()
    for r in out_records:
        if not r.get("is_clean"):
            for f in r.get("flags") or []:
                flag_dist[f] += 1

    payload = {
        "description": (
            "Evergreen cross-version baseline test ids. 1,500 records reserved "
            "permanently for cross-version comparison. Resampled 2026-05-06 from "
            "the original 600-record design to address blindspots: source "
            "distribution now matches 188K production (38.6/51.6/9.9), flagged "
            "stratum grew to 300 records and INCLUDES duplicate_pair, length "
            "stratification applied to every stratum. Salvaged 500 already-"
            "labeled clean records from the v0 evergreen; archive at "
            "data/_archive/evergreen_v0_2026-05-06/. MUST NEVER appear in any "
            "training or validation split."
        ),
        "locked_date": "2026-05-06",
        "count": len(out_records),
        "design": {
            "clean_target": CLEAN_TARGET,
            "flagged_target": FLAGGED_TARGET,
            "production_ratio": PRODUCTION_RATIO,
            "flagged_ratio": FLAGGED_RATIO,
        },
        "actual": {
            "by_source": dict(by_source),
            "by_clean_flag": dict(by_clean_flag),
            "flagged_flag_distribution": dict(flag_dist),
            "salvaged_from_v0": len(salvaged),
            "newly_sampled": len(out_records) - len(salvaged),
        },
        "ids": [r["id"] for r in out_records],
    }
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"[6/6] wrote lock file: {LOCK_PATH.name}")

    # Validation summary
    print("\n=== validation summary ===")
    print(f"total candidates: {len(out_records)} (target {CLEAN_TARGET + FLAGGED_TARGET})")
    print(f"by_source: {dict(by_source)}")
    print(f"by_clean_flag: {dict(by_clean_flag)}")
    print(f"flagged flag distribution: {dict(flag_dist)}")
    print(f"salvaged labels written: {len(salvaged)} (--resume will skip them)")
    print(f"new records to label: {len(out_records) - len(salvaged)}")

    # Cross-checks
    all_ids = [r["id"] for r in out_records]
    assert len(all_ids) == len(set(all_ids)), "duplicate ids in candidates"
    excluded = load_excluded_ids()
    overlap = set(all_ids) & excluded
    assert not overlap, f"overlap with excluded: {len(overlap)} ids"
    print("checks: no duplicate ids, no overlap with reservations [OK]")

    # Write sampling report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join([
            "# Evergreen Baseline Test Resampling Report",
            "",
            "## Purpose",
            "",
            "Resampled to fix six known blindspots. See PROJECT_PLAN.md for",
            "full rationale.",
            "",
            "## Inputs",
            "",
            f"- Salvaged from v0: {len(salvaged)} clean records (preserved labels).",
            f"- Excluded reservations: {len(excluded)} ids.",
            "",
            "## Outputs",
            "",
            f"- Candidates: `data/splits/teacher_judge/evergreen_test/teacher_candidates_all.jsonl` ({len(out_records)} records).",
            f"- Pre-populated labels: `data/labeled/teacher_judge/evergreen_test/evergreen_test_teacher_labels.jsonl` ({len(salvaged)} salvaged).",
            f"- Lock: `data/eval/evergreen_test_ids.json`.",
            "",
            "## By Source",
            "",
            "| Source | Records | Production target |",
            "| --- | ---: | ---: |",
            *[f"| {s} | {by_source.get(s,0)} | {PRODUCTION_RATIO[s]*100:.1f}% |"
              for s in PRODUCTION_RATIO],
            "",
            "## By Clean / Flagged",
            "",
            "| Stratum | Records | Target |",
            "| --- | ---: | ---: |",
            f"| clean | {by_clean_flag.get('clean', 0)} | {CLEAN_TARGET} |",
            f"| flagged | {by_clean_flag.get('flagged', 0)} | {FLAGGED_TARGET} |",
            "",
            "## Flagged Flag Distribution (duplicate_pair INCLUDED)",
            "",
            "| Flag | Records |",
            "| --- | ---: |",
            *[f"| `{f}` | {c} |" for f, c in flag_dist.most_common()],
            "",
            "## Next Steps",
            "",
            "1. DeepSeek-label the remaining 1,000 records:",
            "",
            "```powershell",
            "python scripts/04_teacher_judge.py `",
            "  --input data/splits/teacher_judge/evergreen_test/teacher_candidates_all.jsonl `",
            "  --output-dir data/labeled/teacher_judge/evergreen_test `",
            "  --output-name evergreen_test_teacher_labels.jsonl `",
            "  --no-dry-run --resume",
            "```",
            "",
            "2. Re-run script 18 to rebuild LF dataset, regenerate predict configs, re-run all 6 adapters, re-run script 17 aggregator.",
            "",
        ]),
        encoding="utf-8",
    )
    print(f"[done] report: {REPORT_PATH.name}")


if __name__ == "__main__":
    main()
