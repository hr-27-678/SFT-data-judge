"""Build Phase E downstream SFT datasets from the fixed 15k candidate pool.

The input pool was sampled as clean production-like SFT data and then scored by
both v4 binary scorers. This script turns that pool into policy-specific
LLaMA-Factory datasets for downstream SFT validation.

Default training policies:
- phase_e_unfiltered_clean_15k: all candidate records
- phase_e_v4_conservative_keep_clean_15k: records kept by v4_conservative
- phase_e_v4_confident_keep_clean_15k: records kept by v4_confident
- phase_e_v4_both_keep_clean_15k: records kept by both v4 models

The rule-clean baseline is intentionally not emitted here: the default Phase E
pool was already sampled with `is_clean=True` and no rule flags, so it would be
identical to the unfiltered baseline.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = PROJECT_ROOT / "data" / "splits" / "phase_e" / "phase_e_clean_candidate_15k.jsonl"
DEFAULT_CONSERVATIVE = PROJECT_ROOT / "data" / "scored" / "phase_e_v4_conservative_clean_15k.jsonl"
DEFAULT_CONFIDENT = PROJECT_ROOT / "data" / "scored" / "phase_e_v4_confident_clean_15k.jsonl"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "labeled" / "phase_e_sft"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "phase_e_downstream_dataset_report.md"


PolicyFn = Callable[[dict[str, Any], dict[str, dict[str, Any]]], bool]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Phase E downstream SFT policy datasets.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--conservative-scored", type=Path, default=DEFAULT_CONSERVATIVE)
    parser.add_argument("--confident-scored", type=Path, default=DEFAULT_CONFIDENT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metrics-json", type=Path, default=None)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as file:
        for line_no, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"Expected object at {path}:{line_no}")
            rows.append(obj)
    return rows


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def index_by_id(records: list[dict[str, Any]], *, label: str) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    duplicates = 0
    for record in records:
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            raise ValueError(f"{label} contains a record without string id")
        if record_id in by_id:
            duplicates += 1
        by_id[record_id] = record
    if duplicates:
        raise ValueError(f"{label} contains {duplicates} duplicate id(s)")
    return by_id


def validate_scored(
    candidates: list[dict[str, Any]],
    scored_by_model: dict[str, dict[str, dict[str, Any]]],
) -> None:
    candidate_ids = {record["id"] for record in candidates}
    for model_name, scored in scored_by_model.items():
        scored_ids = set(scored)
        missing = candidate_ids - scored_ids
        extra = scored_ids - candidate_ids
        invalid = [
            record_id
            for record_id, record in scored.items()
            if not record.get("prediction_schema_valid") or record.get("verdict") not in {"keep", "not_keep"}
        ]
        if missing:
            raise ValueError(f"{model_name} scored output is missing {len(missing)} candidate id(s)")
        if extra:
            raise ValueError(f"{model_name} scored output has {len(extra)} extra id(s)")
        if invalid:
            raise ValueError(f"{model_name} scored output has {len(invalid)} invalid prediction row(s)")


def verdict(record_id: str, model_name: str, scored_by_model: dict[str, dict[str, dict[str, Any]]]) -> str:
    return str(scored_by_model[model_name][record_id].get("verdict"))


def build_sft_record(
    candidate: dict[str, Any],
    policy_name: str,
    scored_by_model: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    record_id = str(candidate["id"])
    meta = candidate.get("meta") if isinstance(candidate.get("meta"), dict) else {}
    flags = candidate.get("flags") if isinstance(candidate.get("flags"), list) else []
    return {
        "instruction": str(candidate.get("instruction", "")),
        "input": str(candidate.get("input", "")),
        "output": str(candidate.get("output", "")),
        "system": str(candidate.get("system", "")),
        "meta": {
            "id": record_id,
            "phase_e_sample_id": candidate.get("phase_e_sample_id"),
            "source": candidate.get("source"),
            "language": candidate.get("language"),
            "task_type": candidate.get("task_type"),
            "instruction_len": candidate.get("instruction_len"),
            "output_len": candidate.get("output_len"),
            "is_clean": candidate.get("is_clean"),
            "flags": flags,
            "original_source": meta.get("original_source"),
            "original_score": meta.get("original_score"),
            "phase_e_policy": policy_name,
            "v4_conservative_verdict": verdict(record_id, "v4_conservative", scored_by_model),
            "v4_confident_verdict": verdict(record_id, "v4_confident", scored_by_model),
        },
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_source = Counter(record.get("meta", {}).get("source") for record in records)
    by_language = Counter(record.get("meta", {}).get("language") for record in records)
    by_task = Counter(record.get("meta", {}).get("task_type") for record in records)
    return {
        "records": len(records),
        "by_source": dict(sorted(by_source.items())),
        "by_language": dict(sorted(by_language.items())),
        "by_task_type": dict(sorted(by_task.items())),
    }


def write_dataset_info(output_dir: Path, policy_names: list[str]) -> None:
    info = {}
    for name in policy_names:
        info[name] = {
            "file_name": f"{name}.jsonl",
            "columns": {
                "prompt": "instruction",
                "query": "input",
                "response": "output",
                "system": "system",
            },
        }
    (output_dir / "dataset_info.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] + ["---:" for _ in headers[1:]]) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return lines


def write_report(
    report_path: Path,
    metrics: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    policies = metrics["policies"]
    summary_rows = [
        [
            name,
            stats["records"],
            stats["by_source"].get("cot_zh", 0),
            stats["by_source"].get("finetome", 0),
            stats["by_source"].get("openmath_reasoning", 0),
        ]
        for name, stats in policies.items()
    ]
    overlap = metrics["scorer_overlap"]
    overlap_rows = [
        ["both_keep", overlap["both_keep"]],
        ["conservative_keep_confident_not_keep", overlap["conservative_keep_confident_not_keep"]],
        ["conservative_not_keep_confident_keep", overlap["conservative_not_keep_confident_keep"]],
        ["both_not_keep", overlap["both_not_keep"]],
    ]

    lines = [
        "# Phase E Downstream Dataset Report",
        "",
        "Generated by `scripts/28_build_phase_e_downstream_datasets.py`.",
        "",
        "## Inputs",
        "",
        f"- Candidate pool: `{rel(args.candidates)}`",
        f"- v4 conservative scored: `{rel(args.conservative_scored)}`",
        f"- v4 confident scored: `{rel(args.confident_scored)}`",
        "",
        "## Outputs",
        "",
        f"- Dataset dir: `{rel(args.output_dir)}`",
        f"- Dataset info: `{rel(args.output_dir / 'dataset_info.json')}`",
        f"- Metrics JSON: `{rel(Path(metrics['metrics_path']))}`",
        "",
        "## Dataset Sizes",
        "",
        *md_table(
            ["Dataset", "Records", "cot_zh", "finetome", "openmath_reasoning"],
            summary_rows,
        ),
        "",
        "## Scorer Agreement",
        "",
        *md_table(["Bucket", "Records"], overlap_rows),
        "",
        "## Notes",
        "",
        "- The rule-clean baseline is omitted because this Phase E pool was already sampled with `is_clean=True` and no rule flags.",
        "- `phase_e_v4_both_keep_clean_15k` is the safest high-precision policy: the intersection of the two v4 keep sets.",
        "- Use this directory as `dataset_dir` in LLaMA-Factory and choose one dataset name from `dataset_info.json`.",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    metrics_path = args.metrics_json or args.output_dir / "phase_e_downstream_dataset_metrics.json"

    candidates = read_jsonl(args.candidates)
    candidate_by_id = index_by_id(candidates, label="candidate pool")
    conservative = index_by_id(read_jsonl(args.conservative_scored), label="v4_conservative scored output")
    confident = index_by_id(read_jsonl(args.confident_scored), label="v4_confident scored output")
    scored_by_model = {
        "v4_conservative": conservative,
        "v4_confident": confident,
    }
    validate_scored(candidates, scored_by_model)

    policies: list[tuple[str, PolicyFn]] = [
        ("phase_e_unfiltered_clean_15k", lambda record, _: True),
        (
            "phase_e_v4_conservative_keep_clean_15k",
            lambda record, scored: verdict(record["id"], "v4_conservative", scored) == "keep",
        ),
        (
            "phase_e_v4_confident_keep_clean_15k",
            lambda record, scored: verdict(record["id"], "v4_confident", scored) == "keep",
        ),
        (
            "phase_e_v4_both_keep_clean_15k",
            lambda record, scored: (
                verdict(record["id"], "v4_conservative", scored) == "keep"
                and verdict(record["id"], "v4_confident", scored) == "keep"
            ),
        ),
    ]

    output_metrics: dict[str, Any] = {
        "candidate_records": len(candidates),
        "candidate_ids": len(candidate_by_id),
        "inputs": {
            "candidates": rel(args.candidates),
            "v4_conservative": rel(args.conservative_scored),
            "v4_confident": rel(args.confident_scored),
        },
        "outputs": {
            "dataset_dir": rel(args.output_dir),
            "dataset_info": rel(args.output_dir / "dataset_info.json"),
        },
        "policies": {},
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for policy_name, include in policies:
        records = [
            build_sft_record(candidate, policy_name, scored_by_model)
            for candidate in candidates
            if include(candidate, scored_by_model)
        ]
        write_jsonl(args.output_dir / f"{policy_name}.jsonl", records)
        output_metrics["policies"][policy_name] = {
            "file": rel(args.output_dir / f"{policy_name}.jsonl"),
            **summarize(records),
        }
        print(f"{policy_name}: {len(records)} records")

    overlap = Counter()
    for record in candidates:
        record_id = str(record["id"])
        cons = verdict(record_id, "v4_conservative", scored_by_model)
        conf = verdict(record_id, "v4_confident", scored_by_model)
        if cons == "keep" and conf == "keep":
            overlap["both_keep"] += 1
        elif cons == "keep" and conf == "not_keep":
            overlap["conservative_keep_confident_not_keep"] += 1
        elif cons == "not_keep" and conf == "keep":
            overlap["conservative_not_keep_confident_keep"] += 1
        elif cons == "not_keep" and conf == "not_keep":
            overlap["both_not_keep"] += 1
    output_metrics["scorer_overlap"] = dict(overlap)

    write_dataset_info(args.output_dir, [name for name, _ in policies])
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    output_metrics["metrics_path"] = str(metrics_path)
    metrics_path.write_text(json.dumps(output_metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(args.report_md, output_metrics, args)

    print(f"wrote dataset_info: {rel(args.output_dir / 'dataset_info.json')}")
    print(f"wrote metrics: {rel(metrics_path)}")
    print(f"wrote report: {rel(args.report_md)}")


if __name__ == "__main__":
    main()
