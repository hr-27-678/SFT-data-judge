"""Prepare v4 input batches for scripts/09_build_binary_scorer_sft.py.

scripts/09 expects per-prefix label files split into _train.jsonl /
_valid.jsonl / _test.jsonl. Three of v4's input batches need preparation:

- v2active002: candidates already have train/valid/test split assignments
  (1900/233/232). Monolithic label file exists. Need to split labels by
  matching candidate.split via id.
- v4_random_supplement: candidates have no split. Need to assign 80/10/10
  deterministically by id hash, write candidates back, split labels.
- v4_cot_zh_short_clean: same as v4_random_supplement.

Dedup behavior: when the label file has multiple rows for one
teacher_sample_id (resume-append residue), the LAST row wins. This
matches the documented project behavior.

Records with null teacher_label or non-empty validation_errors are dropped
from the split files so they do not show up as candidates for 09 to
silently skip.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
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


def deterministic_split(record_id: str, *, valid_pct: int = 10, test_pct: int = 10) -> str:
    """Map an id to train/valid/test deterministically.

    Uses md5(id) % 100. Given valid_pct=10, test_pct=10 the split is
    exactly 80/10/10 over uniform-distributed hashes.
    """
    h = int(hashlib.md5(record_id.encode("utf-8")).hexdigest(), 16) % 100
    if h < test_pct:
        return "test"
    if h < test_pct + valid_pct:
        return "valid"
    return "train"


def label_is_valid(record: dict[str, Any]) -> bool:
    if record.get("validation_errors"):
        return False
    label = record.get("teacher_label")
    if not isinstance(label, dict):
        return False
    score = label.get("overall_score")
    if not isinstance(score, int) or not 1 <= score <= 5:
        return False
    return True


def dedupe_by_ts_id(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Last-write-wins dedup on teacher_sample_id. Preserves order of last
    occurrence."""
    by_ts: dict[str, dict[str, Any]] = {}
    for r in records:
        by_ts[r.get("teacher_sample_id")] = r
    return list(by_ts.values())


def process_batch(
    *,
    name: str,
    candidates_path: Path,
    labels_path: Path,
    candidates_out: Path | None,  # if not None, rewrite candidates with assigned splits
    label_split_dir: Path,
    label_split_prefix: str,
    assign_split: bool,
) -> dict[str, int]:
    print(f"\n=== {name} ===")
    cands = read_jsonl(candidates_path)
    labels_raw = read_jsonl(labels_path)
    labels = dedupe_by_ts_id(labels_raw)
    print(f"  candidates: {len(cands)}")
    print(f"  labels:     raw {len(labels_raw)} -> dedup {len(labels)}")

    valid_labels = [r for r in labels if label_is_valid(r)]
    dropped = len(labels) - len(valid_labels)
    if dropped:
        print(f"  dropped {dropped} invalid labels (null / validation_errors / bad score)")

    # If needed, assign split to candidates and write back
    if assign_split:
        for c in cands:
            if c.get("split") is None:
                c["split"] = deterministic_split(c["id"])
        if candidates_out is not None:
            write_jsonl(candidates_out, cands)
            print(f"  wrote candidates with splits -> {candidates_out.relative_to(PROJECT_ROOT)}")

    # Build id -> split map from candidates
    split_by_id: dict[str, str] = {c["id"]: c.get("split") or "train" for c in cands}

    # Split labels by candidate.split, matched on id
    by_split: dict[str, list[dict[str, Any]]] = {"train": [], "valid": [], "test": []}
    unmatched = 0
    for r in valid_labels:
        sp = split_by_id.get(r.get("id"))
        if sp not in by_split:
            unmatched += 1
            continue
        by_split[sp].append(r)

    if unmatched:
        print(f"  WARN: {unmatched} labels had no matching candidate id")

    counts: dict[str, int] = {}
    for sp, recs in by_split.items():
        out_path = label_split_dir / f"{label_split_prefix}_{sp}.jsonl"
        write_jsonl(out_path, recs)
        counts[sp] = len(recs)
        print(f"  wrote {len(recs):>5} labels -> {out_path.relative_to(PROJECT_ROOT)}")

    return counts


def main() -> None:
    summary = []

    # v2active002: candidates already split, labels need split
    counts = process_batch(
        name="v2active002",
        candidates_path=PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v2_active_pilot_002" / "v2active002_teacher_candidates_all.jsonl",
        labels_path=PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "v2active002" / "v2active002_teacher_labels.jsonl",
        candidates_out=None,  # candidates already have splits, leave alone
        label_split_dir=PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "v2active002",
        label_split_prefix="v2active002_teacher_labels",
        assign_split=False,
    )
    summary.append(("v2active002", counts))

    # v4_random_supplement: assign split, write back, split labels
    cand_path = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v4_random_supplement" / "teacher_candidates_all.jsonl"
    counts = process_batch(
        name="v4_random_supplement",
        candidates_path=cand_path,
        labels_path=PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "v4_random_supplement" / "v4_random_supplement_teacher_labels.jsonl",
        candidates_out=cand_path,
        label_split_dir=PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "v4_random_supplement",
        label_split_prefix="v4_random_supplement_teacher_labels",
        assign_split=True,
    )
    summary.append(("v4_random_supplement", counts))

    # v4_cot_zh_short_clean: assign split, write back, split labels
    cand_path = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v4_cot_zh_short_clean" / "teacher_candidates_all.jsonl"
    counts = process_batch(
        name="v4_cot_zh_short_clean",
        candidates_path=cand_path,
        labels_path=PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "v4_cot_zh_short_clean" / "v4_cot_zh_short_clean_teacher_labels.jsonl",
        candidates_out=cand_path,
        label_split_dir=PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "v4_cot_zh_short_clean",
        label_split_prefix="v4_cot_zh_short_clean_teacher_labels",
        assign_split=True,
    )
    summary.append(("v4_cot_zh_short_clean", counts))

    print("\n=== summary ===")
    print(f"{'batch':<30} {'train':>8} {'valid':>8} {'test':>8} {'total':>8}")
    for name, counts in summary:
        t = counts.get("train", 0)
        v = counts.get("valid", 0)
        s = counts.get("test", 0)
        print(f"{name:<30} {t:>8} {v:>8} {s:>8} {t+v+s:>8}")


if __name__ == "__main__":
    main()
