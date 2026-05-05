#!/usr/bin/env python3
"""Build binary scorer SFT data from Teacher Judge labels.

This is a simpler target than the 1-5 scorer:

- score 4/5 -> keep
- score 1/2 -> not_keep
- score 3 -> skipped in confident mode, or not_keep in all mode
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
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "labeled" / "scorer_binary_sft"
SPLITS = ["train", "valid", "test"]

BINARY_SYSTEM = (
    "You are a binary data quality filter for supervised fine-tuning samples. "
    "Judge whether an instruction-output pair is usable training data for a small language model. "
    "Return only valid JSON with this schema: {\"verdict\": \"keep|not_keep\"}. "
    "Use keep only for samples that are clearly useful, correct, relevant, complete, and not corrupted. "
    "Use not_keep for incorrect, irrelevant, incomplete, corrupted, or ambiguous samples."
)


DEFAULT_LOCKED_TEST_IDS = PROJECT_ROOT / "data" / "eval" / "locked_test_ids.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build binary LLaMA-Factory scorer SFT data.")
    parser.add_argument("--candidates", type=Path, nargs="+", default=[DEFAULT_CANDIDATES])
    parser.add_argument("--labels-dir", type=Path, default=DEFAULT_LABELS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--label-prefix",
        type=str,
        action="append",
        default=None,
        help="Teacher label split prefix. Repeat this option to merge multiple label sets.",
    )
    parser.add_argument("--dataset-prefix", type=str, default="scorer_binary_confident_1000")
    parser.add_argument(
        "--mode",
        choices=["confident", "all"],
        default="confident",
        help="confident skips score=3; all maps score=3 to not_keep.",
    )
    parser.add_argument(
        "--locked-test-ids",
        type=Path,
        default=None,
        help=(
            "JSON file with sample ids that must always land in the test split. "
            f"Defaults to {DEFAULT_LOCKED_TEST_IDS} if that file exists."
        ),
    )
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

    if not isinstance(label.get("major_issues"), list):
        errors.append("major_issues must be a list")

    return errors


def binary_verdict(score: int, mode: str) -> str | None:
    if score in (4, 5):
        return "keep"
    if score in (1, 2):
        return "not_keep"
    if score == 3 and mode == "all":
        return "not_keep"
    return None


def build_user_prompt(candidate: dict[str, Any]) -> str:
    metadata = compact_metadata(candidate)
    metadata_text = json.dumps(metadata, ensure_ascii=False, sort_keys=True) if metadata else "{}"
    flags = candidate.get("flags") if isinstance(candidate.get("flags"), list) else []
    sampling = candidate.get("sampling") if isinstance(candidate.get("sampling"), dict) else {}

    return "\n".join(
        [
            "Evaluate this supervised fine-tuning data sample as binary training data quality.",
            "Return only the JSON binary label. Do not include markdown, explanation, or extra text.",
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


def build_sft_record(candidate: dict[str, Any], label_record: dict[str, Any], mode: str) -> dict[str, Any] | None:
    label = label_record["teacher_label"]
    score = int(label["overall_score"])
    verdict = binary_verdict(score, mode)
    if verdict is None:
        return None

    return {
        "instruction": build_user_prompt(candidate),
        "input": "",
        "output": json.dumps({"verdict": verdict}, ensure_ascii=False),
        "system": BINARY_SYSTEM,
        "meta": {
            "id": candidate.get("id"),
            "teacher_sample_id": candidate.get("teacher_sample_id"),
            "source": candidate.get("source"),
            "split": candidate.get("split"),
            "clean_status": candidate.get("sampling", {}).get("clean_status") if isinstance(candidate.get("sampling"), dict) else None,
            "teacher_score": score,
            "teacher_verdict": label.get("verdict"),
            "binary_verdict": verdict,
        },
    }


def load_labels(labels_dir: Path, label_prefixes: list[str]) -> dict[str, dict[str, Any]]:
    labels: dict[str, dict[str, Any]] = {}
    for label_prefix in label_prefixes:
        for split in SPLITS:
            path = labels_dir / f"{label_prefix}_{split}.jsonl"
            for record in read_jsonl(path):
                labels[record_key(record)] = record
    return labels


def write_dataset_info(output_dir: Path, dataset_prefix: str) -> None:
    path = output_dir / "dataset_info.json"
    info = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
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
    path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_report(
    output_dir: Path,
    dataset_prefix: str,
    mode: str,
    records: list[dict[str, Any]],
    skipped: list[dict[str, Any]],
    candidate_paths: list[Path],
    label_prefixes: list[str],
    locked_test_ids_path: Path | None,
    locked_test_overridden: int,
) -> None:
    split_counts = Counter(record["meta"]["split"] for record in records)
    source_counts = Counter(record["meta"]["source"] for record in records)
    verdict_counts = Counter(record["meta"]["binary_verdict"] for record in records)
    score_counts = Counter(record["meta"]["teacher_score"] for record in records)
    source_verdict_counts = Counter((record["meta"]["source"], record["meta"]["binary_verdict"]) for record in records)

    locked_line = (
        f"- Locked test ids: `{locked_test_ids_path.as_posix()}` "
        f"(forced {locked_test_overridden} record(s) to test split)."
        if locked_test_ids_path
        else "- Locked test ids: not applied."
    )

    lines = [
        "# Binary Scorer SFT Dataset Report",
        "",
        "This report is generated by `scripts/09_build_binary_scorer_sft.py`.",
        "",
        f"- Mode: `{mode}`",
        "- Mapping: teacher score 4/5 -> `keep`; teacher score 1/2 -> `not_keep`."
        + (" Score 3 is skipped." if mode == "confident" else " Score 3 -> `not_keep`."),
        locked_line,
        "",
        "## Build Inputs",
        "",
        "Candidate files:",
        "",
        *[f"- `{path.as_posix()}`" for path in candidate_paths],
        "",
        "Label prefixes:",
        "",
        *[f"- `{prefix}`" for prefix in label_prefixes],
        "",
        "## Outputs",
        "",
        markdown_table(
            ["Dataset", "File", "Records"],
            [[f"{dataset_prefix}_{split}", f"{dataset_prefix}_{split}.jsonl", split_counts.get(split, len(records) if split == "all" else 0)] for split in ["all", *SPLITS]],
        ),
        "",
        "## Binary Verdict Distribution",
        "",
        markdown_table(["Verdict", "Records"], [[verdict, verdict_counts.get(verdict, 0)] for verdict in ["keep", "not_keep"]]),
        "",
        "## Teacher Score Distribution Used",
        "",
        markdown_table(["Score", "Records"], [[score, score_counts.get(score, 0)] for score in range(1, 6)]),
        "",
        "## Source Balance",
        "",
        markdown_table(["Source", "Records"], [[source, source_counts[source]] for source in sorted(source_counts)]),
        "",
        "## Source x Verdict",
        "",
        markdown_table(
            ["Source", "Keep", "Not Keep"],
            [
                [
                    source,
                    source_verdict_counts.get((source, "keep"), 0),
                    source_verdict_counts.get((source, "not_keep"), 0),
                ]
                for source in sorted(source_counts)
            ],
        ),
        "",
        "## Skipped",
        "",
        markdown_table(["Reason", "Records"], [[reason, count] for reason, count in sorted(Counter(item["reason"] for item in skipped).items())]),
        "",
        "## LLaMA-Factory Usage",
        "",
        "Use this directory as `dataset_dir` and choose one of the dataset names from `dataset_info.json`.",
        "",
        f"- `{dataset_prefix}_train`",
        f"- `{dataset_prefix}_valid`",
        f"- `{dataset_prefix}_test`",
        "",
    ]
    (output_dir / f"{dataset_prefix}_report.md").write_text("\n".join(lines), encoding="utf-8")


def load_locked_test_ids(args: argparse.Namespace) -> tuple[set[str], Path | None]:
    path = args.locked_test_ids
    if path is None and DEFAULT_LOCKED_TEST_IDS.exists():
        path = DEFAULT_LOCKED_TEST_IDS
    if path is None:
        return set(), None
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data["ids"]), path


def main() -> None:
    args = parse_args()
    candidates = {}
    for path in args.candidates:
        for record in read_jsonl(path):
            candidates[record_key(record)] = record

    label_prefixes = args.label_prefix or ["teacher_labels_1000"]
    labels = load_labels(args.labels_dir, label_prefixes)

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

        sft_record = build_sft_record(candidate, label_record, args.mode)
        if sft_record is None:
            skipped.append({"key": key, "reason": "score_3_skipped"})
            continue
        sft_records.append(sft_record)

    locked_test_ids, locked_test_ids_path = load_locked_test_ids(args)
    overridden = 0
    for record in sft_records:
        if record["meta"]["id"] in locked_test_ids and record["meta"]["split"] != "test":
            record["meta"]["split"] = "test"
            overridden += 1
    if overridden:
        print(f"[locked_test_ids] Forced {overridden} record(s) from train/valid to test split.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        split_records = [record for record in sft_records if record["meta"]["split"] == split]
        write_jsonl(args.output_dir / f"{args.dataset_prefix}_{split}.jsonl", split_records)
    write_jsonl(args.output_dir / f"{args.dataset_prefix}_all.jsonl", sft_records)
    write_jsonl(args.output_dir / f"{args.dataset_prefix}_skipped.jsonl", skipped)
    write_dataset_info(args.output_dir, args.dataset_prefix)
    write_report(
        args.output_dir,
        args.dataset_prefix,
        args.mode,
        sft_records,
        skipped,
        candidate_paths=list(args.candidates),
        label_prefixes=label_prefixes,
        locked_test_ids_path=locked_test_ids_path,
        locked_test_overridden=overridden,
    )

    print(
        json.dumps(
            {
                "records": len(sft_records),
                "skipped": len(skipped),
                "output_dir": str(args.output_dir),
                "dataset_prefix": args.dataset_prefix,
                "mode": args.mode,
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
