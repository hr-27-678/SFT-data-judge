"""Sample a targeted v5 teacher batch for math/code hard negatives.

The first evergreen human audit showed strong teacher/human agreement, but
almost no math/code negative support. This script builds a candidate queue
that deliberately targets clean-looking math/code failures while keeping a
small positive-control balance slice.

The output is a teacher-labeling candidate batch, not training labels.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import random
import re
import warnings
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "by_source"
OUT_DIR = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "v5_math_code_hard_negatives"
REPORT_PATH = PROJECT_ROOT / "reports" / "teacher_sampling_v5_math_code_hard_negatives_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sample v5 math/code hard-negative teacher candidates.")
    parser.add_argument("--batch-prefix", default="v5_math_code_hardneg")
    parser.add_argument("--seed", type=int, default=20260514)
    parser.add_argument("--openmath-hard", type=int, default=300)
    parser.add_argument("--code-hard", type=int, default=150)
    parser.add_argument("--openmath-keep", type=int, default=75)
    parser.add_argument("--code-keep", type=int, default=75)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def stable_hash(text: str, n: int = 12) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:n]


def load_excluded_ids(out_dir: Path) -> set[str]:
    excluded: set[str] = set()
    roots = [
        PROJECT_ROOT / "data" / "labeled" / "teacher_judge",
        PROJECT_ROOT / "data" / "splits" / "teacher_judge",
        PROJECT_ROOT / "data" / "eval",
    ]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.jsonl"):
            try:
                path.relative_to(out_dir)
                continue
            except ValueError:
                pass
            for record in read_jsonl(path):
                sid = record.get("id")
                if isinstance(sid, str):
                    excluded.add(sid)
    locked_path = PROJECT_ROOT / "data" / "eval" / "locked_test_ids.json"
    if locked_path.exists():
        try:
            data = json.loads(locked_path.read_text(encoding="utf-8-sig"))
            if isinstance(data, list):
                excluded.update(str(x) for x in data)
        except json.JSONDecodeError:
            pass
    return excluded


def extract_boxed_answers(text: str) -> list[str]:
    answers: list[str] = []
    i = 0
    marker = r"\boxed{"
    while True:
        start = text.find(marker, i)
        if start < 0:
            break
        j = start + len(marker)
        depth = 1
        chars: list[str] = []
        while j < len(text) and depth > 0:
            ch = text[j]
            if ch == "{":
                depth += 1
                chars.append(ch)
            elif ch == "}":
                depth -= 1
                if depth > 0:
                    chars.append(ch)
            else:
                chars.append(ch)
            j += 1
        if chars:
            answers.append("".join(chars).strip())
        i = j
    return answers


def normalize_answer(text: Any) -> str:
    s = str(text or "").lower().strip()
    s = re.sub(r"\\left|\\right|\\boxed|\\text", "", s)
    s = re.sub(r"[\s{}$\\(),.;:=\"'`]", "", s)
    s = s.replace("converges", "convergent")
    s = s.replace("diverges", "divergent")
    return s


def answer_matches(expected: str, predicted: str) -> bool:
    exp = normalize_answer(expected)
    pred = normalize_answer(predicted)
    if not exp or not pred:
        return False
    return exp == pred or exp in pred or pred in exp


def select_openmath(records: list[dict[str, Any]], excluded: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    hard: list[dict[str, Any]] = []
    keep_controls: list[dict[str, Any]] = []
    for record in records:
        if record.get("id") in excluded or not record.get("is_clean"):
            continue
        expected = (record.get("meta") or {}).get("expected_answer")
        if not expected:
            continue
        output = str(record.get("output") or "")
        boxed = extract_boxed_answers(output)
        reasons: list[str] = []
        if not boxed:
            reasons.append("missing_boxed_answer")
        elif not answer_matches(str(expected), boxed[-1]):
            reasons.append("heuristic_answer_mismatch")
        if re.search(r"\b(cannot solve|unable to solve|not enough information)\b", output, re.I):
            reasons.append("math_refusal_or_uncertainty")

        item = dict(record)
        item["selection_reasons"] = reasons
        item["selection_expected_answer"] = expected
        item["selection_extracted_boxed"] = boxed[-1] if boxed else None
        if reasons:
            hard.append(item)
        else:
            keep_controls.append(item)
    return hard, keep_controls


def code_like(record: dict[str, Any]) -> bool:
    text = f"{record.get('instruction') or ''}\n{record.get('output') or ''}".lower()
    markers = [
        "python",
        "```python",
        "write a function",
        "write a program",
        "implement",
        "return an iterator",
        "opengl",
        "javascript",
        "c++",
    ]
    return any(marker in text for marker in markers)


def extract_python_blocks(output: str) -> list[str]:
    blocks = re.findall(r"```(?:python|py)?\s*(.*?)```", output, flags=re.I | re.DOTALL)
    if blocks:
        return [block.strip() for block in blocks if block.strip()]
    if "def " in output:
        return [output.strip()]
    return []


def python_syntax_ok(blocks: list[str]) -> bool | None:
    if not blocks:
        return None
    for block in blocks:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                ast.parse(block)
        except SyntaxError:
            return False
    return True


def select_code(records: list[dict[str, Any]], excluded: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    hard: list[dict[str, Any]] = []
    keep_controls: list[dict[str, Any]] = []
    for record in records:
        if record.get("id") in excluded or not record.get("is_clean") or not code_like(record):
            continue
        instruction = str(record.get("instruction") or "")
        output = str(record.get("output") or "")
        blocks = extract_python_blocks(output)
        syntax_ok = python_syntax_ok(blocks)
        reasons: list[str] = []
        instruction_wants_code = bool(re.search(r"\b(write|implement|create|define)\b", instruction, re.I))
        if instruction_wants_code and not blocks and "def " not in output:
            reasons.append("code_prompt_missing_code")
        if syntax_ok is False:
            reasons.append("python_syntax_error")
        if re.search(r"\b(i cannot|unable to|as an ai)\b", output, re.I):
            reasons.append("code_refusal")

        item = dict(record)
        item["selection_reasons"] = reasons
        item["selection_python_blocks"] = len(blocks)
        item["selection_python_syntax_ok"] = syntax_ok
        if reasons:
            hard.append(item)
        else:
            keep_controls.append(item)
    return hard, keep_controls


def sample_items(items: list[dict[str, Any]], n: int, rng: random.Random, key_prefix: str) -> list[dict[str, Any]]:
    ranked = sorted(
        items,
        key=lambda r: (
            stable_hash(f"{key_prefix}:{r.get('id')}:{rng.random()}"),
            str(r.get("id")),
        ),
    )
    return ranked[:n]


def split_name(index: int) -> str:
    mod = index % 10
    if mod == 8:
        return "valid"
    if mod == 9:
        return "test"
    return "train"


def prepare_records(records: list[dict[str, Any]], batch_prefix: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        row = dict(record)
        row["teacher_sample_id"] = f"{batch_prefix}_{index:05d}"
        row["teacher_label"] = None
        row["raw_teacher_response"] = None
        row["validation_errors"] = []
        row["split"] = split_name(index)
        row["selection"] = {
            "batch_prefix": batch_prefix,
            "selection_rank": index,
            "selection_reason": "v5_math_code_hard_negative_or_balance",
            "selection_reasons": row.pop("selection_reasons", []),
            "expected_answer": row.pop("selection_expected_answer", None),
            "extracted_boxed": row.pop("selection_extracted_boxed", None),
            "python_blocks": row.pop("selection_python_blocks", None),
            "python_syntax_ok": row.pop("selection_python_syntax_ok", None),
            "policy": "teacher_label_before_training",
        }
        out.append(row)
    return out


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    excluded = load_excluded_ids(args.out_dir)

    openmath = read_jsonl(PROCESSED_DIR / "openmath_reasoning_clean.jsonl")
    finetome = read_jsonl(PROCESSED_DIR / "finetome_clean.jsonl")

    openmath_hard, openmath_keep = select_openmath(openmath, excluded)
    code_hard, code_keep = select_code(finetome, excluded)

    selected: list[dict[str, Any]] = []
    selected.extend(sample_items(openmath_hard, args.openmath_hard, rng, "openmath_hard"))
    selected.extend(sample_items(code_hard, args.code_hard, rng, "code_hard"))
    selected.extend(sample_items(openmath_keep, args.openmath_keep, rng, "openmath_keep"))
    selected.extend(sample_items(code_keep, args.code_keep, rng, "code_keep"))

    # Deduplicate in case a record appears in more than one bucket.
    by_id: dict[str, dict[str, Any]] = {}
    for record in selected:
        by_id.setdefault(record["id"], record)
    prepared = prepare_records(list(by_id.values()), args.batch_prefix)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    all_path = args.out_dir / f"{args.batch_prefix}_teacher_candidates_all.jsonl"
    write_jsonl(all_path, prepared)
    for split in ["train", "valid", "test"]:
        write_jsonl(
            args.out_dir / f"{args.batch_prefix}_teacher_candidates_{split}.jsonl",
            [record for record in prepared if record.get("split") == split],
        )

    reason_counts = Counter()
    bucket_counts = Counter()
    for record in prepared:
        reasons = record["selection"].get("selection_reasons") or ["balance_keep_control"]
        for reason in reasons:
            reason_counts[reason] += 1
        if record.get("source") == "openmath_reasoning":
            bucket_counts["openmath"] += 1
        elif code_like(record):
            bucket_counts["code"] += 1
        else:
            bucket_counts["other"] += 1

    report = [
        "# V5 Math/Code Hard-Negative Teacher Sampling Report",
        "",
        "This batch targets the math/code not_keep coverage gap found by the evergreen human audit.",
        "",
        f"- Batch prefix: `{args.batch_prefix}`",
        f"- Output: `{all_path.relative_to(PROJECT_ROOT)}`",
        f"- Records: {len(prepared)}",
        f"- Excluded ids: {len(excluded)}",
        f"- Seed: {args.seed}",
        "",
        "## Requested Quotas",
        "",
        f"- openmath hard: {args.openmath_hard}",
        f"- code hard: {args.code_hard}",
        f"- openmath keep controls: {args.openmath_keep}",
        f"- code keep controls: {args.code_keep}",
        "",
        "## Available Candidate Pools After Exclusion",
        "",
        f"- openmath hard candidates: {len(openmath_hard)}",
        f"- code hard candidates: {len(code_hard)}",
        f"- openmath keep controls: {len(openmath_keep)}",
        f"- code keep controls: {len(code_keep)}",
        "",
        "## Selected Distribution",
        "",
        f"- by bucket: `{dict(bucket_counts)}`",
        f"- by reason: `{dict(reason_counts)}`",
        "",
        "## Teacher Labeling Command",
        "",
        "```powershell",
        "python scripts/04_teacher_judge.py `",
        f"  --input {all_path.relative_to(PROJECT_ROOT)} `",
        f"  --output-dir data/labeled/teacher_judge/{args.batch_prefix} `",
        f"  --output-name {args.batch_prefix}_teacher_labels.jsonl `",
        "  --no-dry-run `",
        "  --resume",
        "```",
        "",
        "## Notes",
        "",
        "- These are candidate records only. They still need teacher labels before training.",
        "- The hard-negative heuristics are intentionally high-recall and may include false positives.",
        "- Keep-control slices are included so v5 does not learn `math/code -> not_keep`.",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(report), encoding="utf-8")

    print(f"wrote {len(prepared)} records")
    print(f"  candidates: {all_path.relative_to(PROJECT_ROOT)}")
    print(f"  report:     {args.report.relative_to(PROJECT_ROOT)}")
    print(f"  reasons:    {dict(reason_counts)}")


if __name__ == "__main__":
    main()
