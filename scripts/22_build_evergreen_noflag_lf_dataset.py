"""Build the no-flag evergreen LF dataset for prompt-ablation evaluation.

Mirrors scripts/18_build_evergreen_lf_dataset.py exactly, except the
rule_clean and rule_flags lines are removed from the user prompt. Used
to:

1. Quantify the rule_clean shortcut: compare existing 6 adapters'
   evergreen scores on the original prompt vs this stripped prompt. The
   gap on clean stratum not_keep recall = how much each adapter relied
   on the rule_clean signal.
2. Evaluate the v3 conservative noflag adapter (trained with the
   matching no-rule-fields prompt) on its native evaluation distribution.

Output:
- data/labeled/evergreen_lf_noflag/evergreen_test.jsonl
- data/labeled/evergreen_lf_noflag/dataset_info.json (LF-registerable)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test_merged_candidates.jsonl"
OUT_DIR = PROJECT_ROOT / "data" / "labeled" / "evergreen_lf_noflag"
OUT_FILE = OUT_DIR / "evergreen_test.jsonl"
DATASET_INFO = OUT_DIR / "dataset_info.json"

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


def compact_metadata(record: dict[str, Any]) -> dict[str, Any]:
    meta = record.get("meta") if isinstance(record.get("meta"), dict) else {}
    useful_meta = {}
    for key in ["expected_answer", "problem_type", "pass_rate_72b_tir", "score", "input", "original_source", "original_score"]:
        if key in meta and meta[key] not in (None, ""):
            useful_meta[key] = meta[key]
    return useful_meta


def build_user_prompt_noflag(candidate: dict[str, Any]) -> str:
    metadata = compact_metadata(candidate)
    metadata_text = json.dumps(metadata, ensure_ascii=False, sort_keys=True) if metadata else "{}"
    sampling = candidate.get("sampling") if isinstance(candidate.get("sampling"), dict) else {}

    return "\n".join([
        "Evaluate this supervised fine-tuning data sample as binary training data quality.",
        "Return only the JSON binary label. Do not include markdown, explanation, or extra text.",
        "",
        f"source: {candidate.get('source', '')}",
        f"language: {candidate.get('language', '')}",
        f"task_type: {candidate.get('task_type', '')}",
        f"sampling: {json.dumps(sampling, ensure_ascii=False, sort_keys=True)}",
        f"metadata: {metadata_text}",
        "",
        "instruction:",
        str(candidate.get("instruction", "")),
        "",
        "output:",
        str(candidate.get("output", "")),
    ])


def main() -> None:
    candidates = read_jsonl(INPUT)
    assert len(candidates) == 600, f"expected 600, got {len(candidates)}"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_records = []
    for c in candidates:
        out_records.append({
            "instruction": build_user_prompt_noflag(c),
            "input": "",
            "output": '{"verdict": "keep"}',
            "system": BINARY_SYSTEM,
            "_evergreen_id": c["id"],
        })

    with OUT_FILE.open("w", encoding="utf-8") as f:
        for r in out_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    info = {
        "evergreen_test_noflag": {
            "file_name": "evergreen_test.jsonl",
            "columns": {
                "prompt": "instruction",
                "query": "input",
                "response": "output",
                "system": "system",
            },
        }
    }
    with DATASET_INFO.open("w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    print(f"wrote {len(out_records)} records to {OUT_FILE.name}")
    print(f"wrote dataset_info.json to {DATASET_INFO.parent.name}/")


if __name__ == "__main__":
    main()
