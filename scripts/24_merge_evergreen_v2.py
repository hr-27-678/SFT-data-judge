"""Merge the 300 evergreen_clean_expansion records into evergreen v2.

Inputs:
- evergreen v1 (600 records): existing merged candidates and teacher labels
- evergreen_clean_expansion (300 records): new candidates and teacher labels

Outputs (all written, side-by-side with v1, never overwriting):
- data/splits/teacher_judge/evergreen_v2_merged_candidates.jsonl (~900)
- data/labeled/teacher_judge/evergreen_v2_merged_teacher_labels.jsonl (~900)
- data/eval/evergreen_v2_test_ids.json (lock file)
- data/labeled/evergreen_lf_v2/{evergreen_test.jsonl, dataset_info.json}
- data/labeled/evergreen_lf_v2_noflag/{evergreen_test.jsonl, dataset_info.json}

Why v2 lives next to v1 instead of replacing:
- All published v1 metrics and reports remain reproducible
- Cross-version comparison (v3 cons on v1 vs v2) becomes possible
- v1 prediction caches in C:\\Users\\haoran27\\llamafactory_outputs\\*_predict_evergreen
  remain valid for the v1-only subset
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Inputs
V1_CANDS = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test_merged_candidates.jsonl"
V1_LABELS = PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_test_merged_teacher_labels.jsonl"
EXP_CANDS = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_clean_expansion" / "teacher_candidates_all.jsonl"
EXP_LABELS = PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_clean_expansion" / "evergreen_clean_expansion_teacher_labels.jsonl"

# Outputs
V2_CANDS = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_v2_merged_candidates.jsonl"
V2_LABELS = PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_v2_merged_teacher_labels.jsonl"
V2_LOCK = PROJECT_ROOT / "data" / "eval" / "evergreen_v2_test_ids.json"
LF_V2_DIR = PROJECT_ROOT / "data" / "labeled" / "evergreen_lf_v2"
LF_V2_NOFLAG_DIR = PROJECT_ROOT / "data" / "labeled" / "evergreen_lf_v2_noflag"

BINARY_SYSTEM = (
    "You are a binary data quality filter for supervised fine-tuning samples. "
    "Judge whether an instruction-output pair is usable training data for a small language model. "
    "Return only valid JSON with this schema: {\"verdict\": \"keep|not_keep\"}. "
    "Use keep only for samples that are clearly useful, correct, relevant, complete, and not corrupted. "
    "Use not_keep for incorrect, irrelevant, incomplete, corrupted, or ambiguous samples."
)


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


def compact_metadata(record: dict[str, Any]) -> dict[str, Any]:
    meta = record.get("meta") if isinstance(record.get("meta"), dict) else {}
    out = {}
    for key in ["expected_answer", "problem_type", "pass_rate_72b_tir", "score", "input", "original_source", "original_score"]:
        if key in meta and meta[key] not in (None, ""):
            out[key] = meta[key]
    return out


def build_user_prompt(candidate: dict[str, Any], no_rule_fields: bool) -> str:
    metadata = compact_metadata(candidate)
    metadata_text = json.dumps(metadata, ensure_ascii=False, sort_keys=True) if metadata else "{}"
    flags = candidate.get("flags") if isinstance(candidate.get("flags"), list) else []
    sampling = candidate.get("sampling") if isinstance(candidate.get("sampling"), dict) else {}

    lines = [
        "Evaluate this supervised fine-tuning data sample as binary training data quality.",
        "Return only the JSON binary label. Do not include markdown, explanation, or extra text.",
        "",
        f"source: {candidate.get('source', '')}",
        f"language: {candidate.get('language', '')}",
        f"task_type: {candidate.get('task_type', '')}",
    ]
    if not no_rule_fields:
        lines.extend([
            f"rule_clean: {bool(candidate.get('is_clean'))}",
            f"rule_flags: {json.dumps(flags, ensure_ascii=False)}",
        ])
    lines.extend([
        f"sampling: {json.dumps(sampling, ensure_ascii=False, sort_keys=True)}",
        f"metadata: {metadata_text}",
        "",
        "instruction:",
        str(candidate.get("instruction", "")),
        "",
        "output:",
        str(candidate.get("output", "")),
    ])
    return "\n".join(lines)


def build_lf_dataset(candidates: list[dict[str, Any]], out_dir: Path, no_rule_fields: bool, dataset_key: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "evergreen_test.jsonl"
    info_path = out_dir / "dataset_info.json"

    out_records = []
    for c in candidates:
        out_records.append({
            "instruction": build_user_prompt(c, no_rule_fields=no_rule_fields),
            "input": "",
            "output": '{"verdict": "keep"}',
            "system": BINARY_SYSTEM,
            "_evergreen_id": c["id"],
        })
    with out_path.open("w", encoding="utf-8") as f:
        for r in out_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    info = {
        dataset_key: {
            "file_name": "evergreen_test.jsonl",
            "columns": {
                "prompt": "instruction",
                "query": "input",
                "response": "output",
                "system": "system",
            },
        }
    }
    with info_path.open("w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(f"  wrote {len(out_records)} records to {out_path.relative_to(PROJECT_ROOT)}")


def main() -> None:
    print("--- inputs ---")
    v1_cands = read_jsonl(V1_CANDS)
    v1_labels = read_jsonl(V1_LABELS)
    exp_cands = read_jsonl(EXP_CANDS)
    exp_labels = read_jsonl(EXP_LABELS)
    print(f"v1 candidates: {len(v1_cands)}")
    print(f"v1 labels:     {len(v1_labels)}")
    print(f"exp candidates: {len(exp_cands)}")
    print(f"exp labels:    {len(exp_labels)}")

    # Build merged candidates: deduplicate by id, v1 wins on conflict
    cand_by_id: dict[str, dict[str, Any]] = {}
    for r in v1_cands:
        cand_by_id[r["id"]] = r
    n_dup_cand = 0
    for r in exp_cands:
        if r["id"] in cand_by_id:
            n_dup_cand += 1
            continue
        cand_by_id[r["id"]] = r
    if n_dup_cand:
        print(f"WARN: {n_dup_cand} expansion candidates collided with v1 ids (skipped, v1 kept)")

    # Build merged labels: same dedup
    label_by_id: dict[str, dict[str, Any]] = {}
    for r in v1_labels:
        label_by_id[r["id"]] = r
    n_dup_lab = 0
    for r in exp_labels:
        if r["id"] in label_by_id:
            n_dup_lab += 1
            continue
        label_by_id[r["id"]] = r
    if n_dup_lab:
        print(f"WARN: {n_dup_lab} expansion labels collided with v1 ids (skipped, v1 kept)")

    # Sanity: every candidate must have a label
    missing = [sid for sid in cand_by_id if sid not in label_by_id]
    if missing:
        raise SystemExit(f"{len(missing)} candidates have no teacher label; e.g. {missing[:3]}")

    # Stable order: v1 records first (in original order), then expansion in original order
    ordered_cands: list[dict[str, Any]] = []
    seen: set[str] = set()
    for r in v1_cands:
        if r["id"] in cand_by_id and r["id"] not in seen:
            ordered_cands.append(cand_by_id[r["id"]])
            seen.add(r["id"])
    for r in exp_cands:
        if r["id"] in cand_by_id and r["id"] not in seen:
            ordered_cands.append(cand_by_id[r["id"]])
            seen.add(r["id"])

    ordered_labels = [label_by_id[r["id"]] for r in ordered_cands]

    print()
    print("--- outputs ---")
    write_jsonl(V2_CANDS, ordered_cands)
    print(f"  wrote {len(ordered_cands)} -> {V2_CANDS.relative_to(PROJECT_ROOT)}")
    write_jsonl(V2_LABELS, ordered_labels)
    print(f"  wrote {len(ordered_labels)} -> {V2_LABELS.relative_to(PROJECT_ROOT)}")

    # Lock file
    by_source = Counter(r.get("source", "") for r in ordered_cands)
    by_clean = Counter("clean" if r.get("is_clean") else "flagged" for r in ordered_cands)
    score_dist = Counter()
    for r in ordered_labels:
        sc = (r.get("teacher_label") or {}).get("overall_score")
        score_dist[sc] += 1

    lock = {
        "description": "Evergreen v2 test set lock. Built from evergreen v1 (600) + evergreen_clean_expansion (300).",
        "version": "v2",
        "locked_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "count": len(ordered_cands),
        "by_source": dict(by_source),
        "by_clean_flag": dict(by_clean),
        "score_distribution": {str(k): v for k, v in score_dist.items()},
        "ids": [r["id"] for r in ordered_cands],
    }
    V2_LOCK.parent.mkdir(parents=True, exist_ok=True)
    V2_LOCK.write_text(json.dumps(lock, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote lock -> {V2_LOCK.relative_to(PROJECT_ROOT)}")

    # LF datasets
    print()
    print("--- LF datasets ---")
    print("flagged-prompt LF v2:")
    build_lf_dataset(ordered_cands, LF_V2_DIR, no_rule_fields=False, dataset_key="evergreen_test_v2")
    print("noflag-prompt LF v2:")
    build_lf_dataset(ordered_cands, LF_V2_NOFLAG_DIR, no_rule_fields=True, dataset_key="evergreen_test_v2_noflag")

    # Summary
    print()
    print("--- summary ---")
    print(f"total records:    {len(ordered_cands)}")
    print(f"by source:        {dict(by_source)}")
    print(f"by is_clean:      {dict(by_clean)}")
    print("score distribution:")
    for sc in [1, 2, 3, 4, 5]:
        print(f"  score={sc}: {score_dist.get(sc, 0)}")
    print()
    print("Per-source clean stratum not_keep support (conservative, score 1-2-3):")
    for src in sorted(by_source):
        clean_neg = sum(
            1 for r, lab in zip(ordered_cands, ordered_labels)
            if r.get("source") == src and r.get("is_clean")
            and (lab.get("teacher_label") or {}).get("overall_score") in (1, 2, 3)
        )
        clean_total = sum(
            1 for r in ordered_cands
            if r.get("source") == src and r.get("is_clean")
        )
        print(f"  {src} clean: {clean_neg} / {clean_total} ({100*clean_neg/max(1,clean_total):.1f}%)")


if __name__ == "__main__":
    main()
