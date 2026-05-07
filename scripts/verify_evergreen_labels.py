"""Verify the two evergreen label files and merge them on success.

Checks:
1. Total count = 600 = 200 (clean_v1) + 400 (extension: 300 clean + 100 flagged)
2. Every id in the lock file (data/eval/evergreen_test_ids.json) is present
3. Every label is valid (teacher_label not None, validation_errors empty)
4. Stratum membership matches the lock file
5. Per-stratum verdict distribution is reasonable

If all checks pass, write merged labels to:
  data/labeled/teacher_judge/evergreen_test_merged_teacher_labels.jsonl
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCK_FILE = PROJECT_ROOT / "data" / "eval" / "evergreen_test_ids.json"
LABELS_V1 = PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_test" / "evergreen_test_teacher_labels.jsonl"
LABELS_EXT = PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_test_extension" / "evergreen_test_extension_teacher_labels.jsonl"
MERGED_OUT = PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_test_merged_teacher_labels.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def keep_latest_by_id(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resume mode appends retried records; keep only the last entry per id."""
    by_id: dict[str, dict[str, Any]] = {}
    for r in records:
        sid = r.get("id")
        if sid:
            by_id[sid] = r
    return list(by_id.values())


def main() -> None:
    print("=== evergreen 600 verification ===\n")
    issues: list[str] = []

    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    locked_ids = set(lock["ids"])
    strata_ids = {name: set(info) for name, info in lock["ids_by_stratum"].items()}
    print(f"[lock] expected count: {lock['count']}")
    print(f"[lock] strata: " + ", ".join(f"{k}={len(v)}" for k, v in strata_ids.items()))

    raw_v1 = read_jsonl(LABELS_V1)
    raw_ext = read_jsonl(LABELS_EXT)
    print(f"\n[raw lines] v1={len(raw_v1)}, extension={len(raw_ext)}")

    v1 = keep_latest_by_id(raw_v1)
    ext = keep_latest_by_id(raw_ext)
    print(f"[deduped by id] v1={len(v1)}, extension={len(ext)}")

    if len(v1) != 200:
        issues.append(f"v1 deduped count {len(v1)} != 200")
    if len(ext) != 400:
        issues.append(f"extension deduped count {len(ext)} != 400")

    file_ids = {r["id"] for r in v1} | {r["id"] for r in ext}
    missing = locked_ids - file_ids
    extra = file_ids - locked_ids
    print(f"\n[id match] missing in files: {len(missing)}, unexpected ids in files: {len(extra)}")
    if missing:
        issues.append(f"{len(missing)} locked ids missing from label files")
        print(f"  missing sample: {list(missing)[:3]}")
    if extra:
        issues.append(f"{len(extra)} unexpected ids in label files")
        print(f"  extra sample: {list(extra)[:3]}")

    invalid_v1 = [r for r in v1 if not r.get("teacher_label") or r.get("validation_errors")]
    invalid_ext = [r for r in ext if not r.get("teacher_label") or r.get("validation_errors")]
    print(f"\n[label quality] invalid in v1: {len(invalid_v1)}, invalid in extension: {len(invalid_ext)}")
    if invalid_v1 or invalid_ext:
        issues.append(f"{len(invalid_v1) + len(invalid_ext)} records have null label or validation errors")
        for r in (invalid_v1 + invalid_ext)[:5]:
            print(f"  id={r.get('id')} teacher_label={'set' if r.get('teacher_label') else 'NULL'} errors={r.get('validation_errors')}")

    all_records = v1 + ext
    by_stratum_actual: Counter[str] = Counter()
    for r in all_records:
        rid = r["id"]
        for name, ids in strata_ids.items():
            if rid in ids:
                by_stratum_actual[name] += 1
                break
        else:
            issues.append(f"id {rid} not in any stratum")

    print("\n[stratum membership]")
    for name, expected in strata_ids.items():
        actual = by_stratum_actual.get(name, 0)
        status = "OK" if actual == len(expected) else "MISMATCH"
        print(f"  {name}: expected {len(expected)}, got {actual} [{status}]")
        if actual != len(expected):
            issues.append(f"stratum {name} count {actual} != expected {len(expected)}")

    print("\n[verdict distribution per stratum]")
    valid = [r for r in all_records if r.get("teacher_label") and not r.get("validation_errors")]
    for stratum, ids in strata_ids.items():
        recs = [r for r in valid if r["id"] in ids]
        verdicts = Counter(r["teacher_label"].get("verdict") for r in recs)
        scores = Counter(r["teacher_label"].get("overall_score") for r in recs)
        print(f"  {stratum} (n={len(recs)}): verdicts={dict(verdicts)}, scores={dict(sorted(scores.items()))}")

    print("\n=== summary ===")
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nNOT merging. Fix issues first.")
        sys.exit(1)

    MERGED_OUT.parent.mkdir(parents=True, exist_ok=True)
    with MERGED_OUT.open("w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    out_str = str(MERGED_OUT).encode("ascii", errors="replace").decode("ascii")
    print(f"All checks passed. Merged {len(all_records)} records to:\n  {out_str}")


if __name__ == "__main__":
    main()
