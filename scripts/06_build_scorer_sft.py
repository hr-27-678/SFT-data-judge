"""Build scorer SFT data from Teacher Judge labels.

The output is an Alpaca-format dataset that LLaMA-Factory can read directly by
using this directory as `dataset_dir`.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "starter_1000" / "teacher_candidates_all.jsonl"
DEFAULT_LABELS_DIR = PROJECT_ROOT / "data" / "labeled" / "teacher_judge"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "labeled" / "scorer_sft"
DIMENSIONS = [
    "instruction_clarity",
    "response_relevance",
    "factual_or_answer_correctness",
    "reasoning_quality",
    "completeness",
    "data_integrity",
]
SPLITS = ["train", "valid", "test"]
SCORER_SYSTEM = (
    "You are a data quality scorer for supervised fine-tuning samples. "
    "Judge whether an instruction-output pair is useful training data for a small language model. "
    "Return only valid JSON with this schema: "
    '{"overall_score": int 1-5, "verdict": "keep|maybe|drop", '
    '"dimension_scores": {"instruction_clarity": int, "response_relevance": int, '
    '"factual_or_answer_correctness": int, "reasoning_quality": int, "completeness": int, '
    '"data_integrity": int}, "major_issues": list[str], "reason": string}. '
    "Use verdict keep for scores 5 or 4, maybe for score 3, and drop for scores 2 or 1."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build LLaMA-Factory scorer SFT data.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--labels-dir", type=Path, default=DEFAULT_LABELS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--label-prefix", type=str, default="teacher_labels_1000")
    parser.add_argument("--dataset-prefix", type=str, default="scorer_sft_1000")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
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


def record_key(record: dict[str, Any]) -> str:
    return str(record.get("teacher_sample_id") or record.get("pilot_sample_id") or record.get("id"))


def compact_metadata(record: dict[str, Any]) -> dict[str, Any]:
    meta = record.get("meta") if isinstance(record.get("meta"), dict) else {}
    useful_meta = {}
    for key in ["expected_answer", "problem_type", "pass_rate_72b_tir", "score", "input"]:
        if key in meta and meta[key] not in (None, ""):
            useful_meta[key] = meta[key]
    return useful_meta


def normalize_label(label: dict[str, Any]) -> dict[str, Any]:
    dimension_scores = label.get("dimension_scores") if isinstance(label.get("dimension_scores"), dict) else {}
    normalized = {
        "overall_score": int(label["overall_score"]),
        "dimension_scores": {dimension: int(dimension_scores[dimension]) for dimension in DIMENSIONS},
        "verdict": str(label["verdict"]),
        "reason": str(label.get("reason", "")).strip(),
        "major_issues": label.get("major_issues") if isinstance(label.get("major_issues"), list) else [],
    }
    return normalized


def validate_label_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if record.get("validation_errors"):
        errors.append("validation_errors is not empty")

    label = record.get("teacher_label")
    if not isinstance(label, dict):
        return errors + ["teacher_label is missing"]

    score = label.get("overall_score")
    if not isinstance(score, int) or not 1 <= score <= 5:
        errors.append("overall_score must be integer 1-5")

    verdict = label.get("verdict")
    expected_verdict = {1: "drop", 2: "drop", 3: "maybe", 4: "keep", 5: "keep"}.get(score)
    if verdict != expected_verdict:
        errors.append("verdict does not match overall_score")

    dims = label.get("dimension_scores")
    if not isinstance(dims, dict):
        errors.append("dimension_scores is missing")
    else:
        for dimension in DIMENSIONS:
            value = dims.get(dimension)
            if not isinstance(value, int) or not 1 <= value <= 5:
                errors.append(f"dimension_scores.{dimension} must be integer 1-5")

    if not isinstance(label.get("major_issues"), list):
        errors.append("major_issues must be a list")

    return errors


def build_user_prompt(candidate: dict[str, Any]) -> str:
    metadata = compact_metadata(candidate)
    metadata_text = json.dumps(metadata, ensure_ascii=False, sort_keys=True) if metadata else "{}"
    flags = candidate.get("flags") if isinstance(candidate.get("flags"), list) else []
    sampling = candidate.get("sampling") if isinstance(candidate.get("sampling"), dict) else {}

    return "\n".join(
        [
            "Evaluate this supervised fine-tuning data sample as training data for a small language model.",
            "Return only the JSON quality label. Do not include markdown or extra text.",
            "",
            f"source: {candidate.get('source', '')}",
            f"language: {candidate.get('language', '')}",
            f"task_type: {candidate.get('task_type', '')}",
            f"rule_clean: {bool(candidate.get('is_clean'))}",
            f"rule_flags: {json.dumps(flags, ensure_ascii=False)}",
            f"sampling: {json.dumps(sampling, ensure_ascii=False, sort_keys=True)}",
            f"metadata: {metadata_text}",
            "",
            "instruction:",
            str(candidate.get("instruction", "")),
            "",
            "output:",
            str(candidate.get("output", "")),
        ]
    )


def build_sft_record(candidate: dict[str, Any], label_record: dict[str, Any]) -> dict[str, Any]:
    label = normalize_label(label_record["teacher_label"])
    return {
        "instruction": build_user_prompt(candidate),
        "input": "",
        "output": json.dumps(label, ensure_ascii=False),
        "system": SCORER_SYSTEM,
        "meta": {
            "id": candidate.get("id"),
            "teacher_sample_id": candidate.get("teacher_sample_id"),
            "source": candidate.get("source"),
            "split": candidate.get("split"),
            "clean_status": candidate.get("sampling", {}).get("clean_status") if isinstance(candidate.get("sampling"), dict) else None,
            "overall_score": label["overall_score"],
            "verdict": label["verdict"],
        },
    }


def load_labels(labels_dir: Path, label_prefix: str) -> dict[str, dict[str, Any]]:
    labels: dict[str, dict[str, Any]] = {}
    for split in SPLITS:
        path = labels_dir / f"{label_prefix}_{split}.jsonl"
        for record in read_jsonl(path):
            labels[record_key(record)] = record
    return labels


def write_dataset_info(output_dir: Path, dataset_prefix: str) -> None:
    info = {}
    for split in ["all", *SPLITS]:
        name = f"{dataset_prefix}_{split}"
        info[name] = {
            "file_name": f"{name}.jsonl",
            "columns": {
                "prompt": "instruction",
                "query": "input",
                "response": "output",
                "system": "system",
            },
        }
    path = output_dir / "dataset_info.json"
    path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_report(output_dir: Path, dataset_prefix: str, records: list[dict[str, Any]]) -> None:
    split_counts = Counter(record["meta"]["split"] for record in records)
    score_counts = Counter(record["meta"]["overall_score"] for record in records)
    source_counts = Counter(record["meta"]["source"] for record in records)

    lines = [
        "# Scorer SFT Dataset Report",
        "",
        "This report is generated by `scripts/06_build_scorer_sft.py`.",
        "",
        "## Outputs",
        "",
        markdown_table(
            ["Dataset", "File", "Records"],
            [[f"{dataset_prefix}_{split}", f"{dataset_prefix}_{split}.jsonl", split_counts.get(split, len(records) if split == "all" else 0)] for split in ["all", *SPLITS]],
        ),
        "",
        "## Source Balance",
        "",
        markdown_table(["Source", "Records"], [[source, source_counts[source]] for source in sorted(source_counts)]),
        "",
        "## Score Distribution",
        "",
        markdown_table(["Score", "Records"], [[score, score_counts.get(score, 0)] for score in range(1, 6)]),
        "",
        "## LLaMA-Factory Usage",
        "",
        "Use this directory as `dataset_dir` and choose one of the dataset names from `dataset_info.json`.",
        "",
        "Example dataset names:",
        "",
        f"- `{dataset_prefix}_train`",
        f"- `{dataset_prefix}_valid`",
        f"- `{dataset_prefix}_test`",
        "",
    ]
    (output_dir / "scorer_sft_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    candidates = {record_key(record): record for record in read_jsonl(args.candidates)}
    labels = load_labels(args.labels_dir, args.label_prefix)

    sft_records: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for key, label_record in labels.items():
        candidate = candidates.get(key)
        if candidate is None:
            skipped.append({"key": key, "reason": "missing candidate"})
            continue

        errors = validate_label_record(label_record)
        if errors:
            skipped.append({"key": key, "reason": "; ".join(errors)})
            continue

        sft_records.append(build_sft_record(candidate, label_record))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        split_records = [record for record in sft_records if record["meta"]["split"] == split]
        write_jsonl(args.output_dir / f"{args.dataset_prefix}_{split}.jsonl", split_records)
    write_jsonl(args.output_dir / f"{args.dataset_prefix}_all.jsonl", sft_records)
    write_dataset_info(args.output_dir, args.dataset_prefix)
    write_report(args.output_dir, args.dataset_prefix, sft_records)

    if skipped:
        write_jsonl(args.output_dir / f"{args.dataset_prefix}_skipped.jsonl", skipped)

    print(
        json.dumps(
            {
                "records": len(sft_records),
                "skipped": len(skipped),
                "output_dir": str(args.output_dir),
                "dataset_prefix": args.dataset_prefix,
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
