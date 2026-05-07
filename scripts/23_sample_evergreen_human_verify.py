"""Sample 50 evergreen records for human verification.

The evergreen ground truth comes from a single teacher (DeepSeek). If
that teacher has systematic biases, both training and evergreen evaluation
share the bias and the metric looks better than reality.

This batch samples 50 records from the locked 600 evergreen set for the
user to manually re-judge. Comparing human verdicts against DeepSeek
labels gives a teacher-bias anchor: a high disagreement rate means the
evergreen numbers should be discounted.

Stratification (by source, proportional to evergreen):
- cot_zh: 30
- finetome: 15
- openmath_reasoning: 5

Within each source, sampling is uniform random across both clean and
flagged strata. Seed-fixed for reproducibility.

Outputs:
- data/eval/evergreen_human_verify/sample.jsonl  (machine-readable)
- data/eval/evergreen_human_verify/annotation.md (user-editable form)

After the user fills in human_verdict / human_score / human_notes in
the markdown (or jsonl), an analysis script can compute agreement.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANDIDATES_PATH = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test_merged_candidates.jsonl"
LABELS_PATH = PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_test_merged_teacher_labels.jsonl"
ARCHIVE_LABELS_PATH = PROJECT_ROOT / "data" / "_archive" / "evergreen_v0_2026-05-06" / "evergreen_test_merged_teacher_labels.jsonl"
OUT_DIR = PROJECT_ROOT / "data" / "eval" / "evergreen_human_verify"

QUOTAS = {
    "cot_zh": 30,
    "finetome": 15,
    "openmath_reasoning": 5,
}

INSTRUCTION_TRUNCATE = 800
OUTPUT_TRUNCATE = 1200


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=20260507)
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


def truncate(s: str, n: int) -> str:
    s = str(s or "")
    if len(s) <= n:
        return s
    return s[:n] + f"\n... [truncated, total {len(s)} chars]"


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    candidates = {r["id"]: r for r in read_jsonl(CANDIDATES_PATH)}

    labels_path = LABELS_PATH if LABELS_PATH.exists() else ARCHIVE_LABELS_PATH
    if not labels_path.exists():
        raise SystemExit(
            f"Cannot find merged evergreen teacher labels. Tried:\n"
            f"  {LABELS_PATH}\n  {ARCHIVE_LABELS_PATH}"
        )
    labels = {r["id"]: r for r in read_jsonl(labels_path)}
    print(f"using labels: {labels_path.relative_to(PROJECT_ROOT)}")

    by_source: dict[str, list[str]] = defaultdict(list)
    for sid, rec in candidates.items():
        src = rec.get("source", "")
        if src in QUOTAS:
            by_source[src].append(sid)

    sampled_ids: list[str] = []
    for src, want in QUOTAS.items():
        pool = by_source[src][:]
        rng.shuffle(pool)
        sampled_ids.extend(pool[:want])

    out_records: list[dict[str, Any]] = []
    for rank, sid in enumerate(sampled_ids):
        cand = candidates[sid]
        lab = labels.get(sid, {})
        teacher_label = lab.get("teacher_label") or {}
        out_records.append({
            "rank": rank,
            "id": sid,
            "source": cand.get("source"),
            "is_clean": bool(cand.get("is_clean")),
            "rule_flags": cand.get("flags") or [],
            "instruction": cand.get("instruction"),
            "output": cand.get("output"),
            "teacher_score": teacher_label.get("overall_score"),
            "teacher_verdict": teacher_label.get("verdict"),
            "teacher_major_issues": teacher_label.get("major_issues"),
            "teacher_rationale": teacher_label.get("rationale"),
            "human_score": None,
            "human_verdict": None,
            "human_notes": "",
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUT_DIR / "sample.jsonl", out_records)

    md_lines = [
        "# Evergreen Human Verification Annotation",
        "",
        "Fill in `human_score` (1-5) and `human_verdict` (keep / not_keep / maybe)",
        "for each record below. `human_notes` is optional. Compare your judgment",
        "to the DeepSeek teacher label printed in each block.",
        "",
        f"Total records: {len(out_records)}.",
        "",
        f"Sampled by `scripts/23_sample_evergreen_human_verify.py` with seed {args.seed}.",
        "",
        f"Source distribution: {dict(Counter(r['source'] for r in out_records))}.",
        "",
        "---",
        "",
    ]
    for r in out_records:
        md_lines.extend([
            f"## #{r['rank']:02d}  ({r['source']})",
            "",
            f"- id: `{r['id']}`",
            f"- is_clean: `{r['is_clean']}`",
            f"- rule_flags: `{json.dumps(r['rule_flags'], ensure_ascii=False)}`",
            f"- teacher_score: **{r['teacher_score']}**",
            f"- teacher_verdict: **{r['teacher_verdict']}**",
            f"- teacher_major_issues: `{json.dumps(r['teacher_major_issues'], ensure_ascii=False)}`",
            "- teacher_rationale:",
            "",
            f"  > {(r['teacher_rationale'] or '').replace(chr(10), ' ')}",
            "",
            "### instruction",
            "",
            "```",
            truncate(r["instruction"], INSTRUCTION_TRUNCATE),
            "```",
            "",
            "### output",
            "",
            "```",
            truncate(r["output"], OUTPUT_TRUNCATE),
            "```",
            "",
            "### YOUR ANNOTATION",
            "",
            "- human_score: ",
            "- human_verdict: ",
            "- human_notes: ",
            "",
            "---",
            "",
        ])

    (OUT_DIR / "annotation.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(f"wrote {len(out_records)} sampled records:")
    print(f"  - {(OUT_DIR / 'sample.jsonl').relative_to(PROJECT_ROOT)}")
    print(f"  - {(OUT_DIR / 'annotation.md').relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
