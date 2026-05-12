"""Sample a small held-out Phase E downstream evaluation set.

This is not a scorer eval set. It is a prompt set for evaluating the four
downstream SFT models trained from different filtering policies.

Default design:
- 200 total held-out prompts
- source quotas: finetome 80, cot_zh 80, openmath_reasoning 40
- require rule-clean source records
- balance short/medium/long reference-output length within each source
- exclude ids used by scorer training/eval, teacher labeling, evergreen,
  human verification, and Phase E training datasets

Outputs:
- data/eval/phase_e_downstream_eval/sample.jsonl
- data/eval/phase_e_downstream_eval/metrics.json
- data/labeled/phase_e_downstream_eval_lf/phase_e_downstream_eval_200.jsonl
- data/labeled/phase_e_downstream_eval_lf/dataset_info.json
- reports/phase_e_downstream_eval_sampling_report.md
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "by_source"
OUT_DIR = PROJECT_ROOT / "data" / "eval" / "phase_e_downstream_eval"
LF_OUT_DIR = PROJECT_ROOT / "data" / "labeled" / "phase_e_downstream_eval_lf"
REPORT_PATH = PROJECT_ROOT / "reports" / "phase_e_downstream_eval_sampling_report.md"

DEFAULT_QUOTAS = {
    "finetome": 80,
    "cot_zh": 80,
    "openmath_reasoning": 40,
}
SOURCE_ORDER = ["finetome", "cot_zh", "openmath_reasoning"]

ID_KEYS = {
    "id",
    "sample_id",
    "original_id",
    "original_sample_id",
    "source_id",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sample Phase E downstream eval prompts.")
    parser.add_argument("--seed", type=int, default=20260510)
    parser.add_argument("--output", type=Path, default=OUT_DIR / "sample.jsonl")
    parser.add_argument("--metrics-json", type=Path, default=OUT_DIR / "metrics.json")
    parser.add_argument("--lf-output-dir", type=Path, default=LF_OUT_DIR)
    parser.add_argument("--report-md", type=Path, default=REPORT_PATH)
    parser.add_argument("--finetome", type=int, default=DEFAULT_QUOTAS["finetome"])
    parser.add_argument("--cot-zh", type=int, default=DEFAULT_QUOTAS["cot_zh"])
    parser.add_argument("--openmath-reasoning", type=int, default=DEFAULT_QUOTAS["openmath_reasoning"])
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
            if isinstance(obj, dict):
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


def source_id_like(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return any(value.startswith(prefix) for prefix in ("cot_zh_", "finetome_", "openmath_reasoning_"))


def collect_ids_from_obj(obj: Any, out: set[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in ID_KEYS and source_id_like(value):
                out.add(value)
            elif key == "ids" and isinstance(value, list):
                out.update(item for item in value if source_id_like(item))
            elif key == "meta" and isinstance(value, dict):
                meta_id = value.get("id")
                if source_id_like(meta_id):
                    out.add(meta_id)
                collect_ids_from_obj(value, out)
            elif isinstance(value, (dict, list)):
                collect_ids_from_obj(value, out)
    elif isinstance(obj, list):
        for item in obj:
            collect_ids_from_obj(item, out)


def collect_ids_from_json(path: Path) -> set[str]:
    ids: set[str] = set()
    try:
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return ids
    collect_ids_from_obj(obj, ids)
    return ids


def collect_ids_from_jsonl(path: Path) -> set[str]:
    ids: set[str] = set()
    with path.open("r", encoding="utf-8-sig") as file:
        for line_no, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
            collect_ids_from_obj(obj, ids)
    return ids


def should_skip_exclusion_path(path: Path, output_paths: set[Path], output_dirs: set[Path]) -> bool:
    resolved = path.resolve()
    if resolved in output_paths:
        return True
    return any(parent in resolved.parents or resolved == parent for parent in output_dirs)


def load_excluded_ids(output_paths: set[Path], output_dirs: set[Path]) -> tuple[set[str], dict[str, int]]:
    roots = [
        PROJECT_ROOT / "data" / "labeled",
        PROJECT_ROOT / "data" / "splits" / "teacher_judge",
        PROJECT_ROOT / "data" / "splits" / "phase_e",
        PROJECT_ROOT / "data" / "eval",
    ]
    excluded: set[str] = set()
    by_area: dict[str, int] = {}
    for root in roots:
        before = len(excluded)
        if not root.exists():
            by_area[rel(root)] = 0
            continue
        for path in root.rglob("*"):
            if not path.is_file() or should_skip_exclusion_path(path, output_paths, output_dirs):
                continue
            if path.suffix == ".jsonl":
                excluded.update(collect_ids_from_jsonl(path))
            elif path.suffix == ".json":
                excluded.update(collect_ids_from_json(path))
        by_area[rel(root)] = len(excluded) - before
    return excluded, by_area


def length_bucket(record: dict[str, Any], q33: int, q66: int) -> str:
    value = int(record.get("output_len", 0) or 0)
    if value <= q33:
        return "short"
    if value <= q66:
        return "medium"
    return "long"


def stratified_sample(records: list[dict[str, Any]], target: int, rng: random.Random) -> list[dict[str, Any]]:
    if target <= 0:
        return []
    output_lens = sorted(int(record.get("output_len", 0) or 0) for record in records)
    q33 = output_lens[len(output_lens) // 3]
    q66 = output_lens[(2 * len(output_lens)) // 3]

    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        buckets[length_bucket(record, q33, q66)].append(record)

    selected: list[dict[str, Any]] = []
    per_bucket = target // 3
    remainder = target - per_bucket * 3
    for index, bucket in enumerate(("short", "medium", "long")):
        want = per_bucket + (1 if index < remainder else 0)
        pool = buckets[bucket][:]
        rng.shuffle(pool)
        if len(pool) < want:
            raise ValueError(f"Not enough eligible {bucket} records: need {want}, found {len(pool)}")
        selected.extend(pool[:want])
    return selected


def compact_eval_record(record: dict[str, Any], index: int, seed: int) -> dict[str, Any]:
    meta = record.get("meta") if isinstance(record.get("meta"), dict) else {}
    flags = record.get("flags") if isinstance(record.get("flags"), list) else []
    return {
        "phase_e_eval_id": f"phase_e_eval_{index:04d}",
        "id": record.get("id"),
        "source": record.get("source"),
        "source_index": record.get("source_index"),
        "language": record.get("language"),
        "task_type": record.get("task_type"),
        "instruction": record.get("instruction", ""),
        "input": record.get("input", ""),
        "reference_output": record.get("output", ""),
        "instruction_len": record.get("instruction_len"),
        "output_len": record.get("output_len"),
        "pair_hash": record.get("pair_hash"),
        "is_clean": record.get("is_clean"),
        "flags": flags,
        "meta": meta,
        "selection": {
            "phase": "phase_e_downstream_eval",
            "selection_rank": index,
            "seed": seed,
            "selection_reason": "heldout_prompt_for_phase_e_downstream_model_comparison",
            "exclusion_policy": "exclude data/labeled, teacher_judge splits, phase_e training pool, and previous eval ids",
        },
    }


def write_lf_dataset(records: list[dict[str, Any]], out_dir: Path) -> None:
    dataset_name = "phase_e_downstream_eval_200"
    out_file = out_dir / f"{dataset_name}.jsonl"
    lf_records = []
    for record in records:
        lf_records.append({
            "instruction": record.get("instruction", ""),
            "input": record.get("input", ""),
            "output": record.get("reference_output", ""),
            "system": "",
            "_phase_e_eval_id": record.get("phase_e_eval_id"),
            "_source_id": record.get("id"),
        })
    write_jsonl(out_file, lf_records)
    info = {
        dataset_name: {
            "file_name": out_file.name,
            "columns": {
                "prompt": "instruction",
                "query": "input",
                "response": "output",
                "system": "system",
            },
        }
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "dataset_info.json").write_text(
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


def write_report(report_path: Path, metrics: dict[str, Any]) -> None:
    rows = [
        [
            source,
            metrics["by_source"].get(source, 0),
            metrics["eligible_counts"].get(source, 0),
            metrics["clean_counts"].get(source, 0),
        ]
        for source in SOURCE_ORDER
    ]
    lines = [
        "# Phase E Downstream Eval Sampling Report",
        "",
        "Generated by `scripts/29_sample_phase_e_downstream_eval.py`.",
        "",
        "## Purpose",
        "",
        "Build a small held-out prompt set for comparing the four Phase E downstream SFT models.",
        "",
        "## Outputs",
        "",
        f"- Sample JSONL: `{metrics['outputs']['sample']}`",
        f"- Metrics JSON: `{metrics['outputs']['metrics']}`",
        f"- LLaMA-Factory dataset dir: `{metrics['outputs']['lf_dataset_dir']}`",
        f"- Total: {metrics['total']}",
        f"- Seed: {metrics['seed']}",
        "",
        "## Exclusion Policy",
        "",
        "Excluded ids found under:",
        "",
        *[f"- `{area}`: +{count} ids" for area, count in metrics["excluded_by_area"].items()],
        "",
        f"Total unique excluded ids: {metrics['excluded_ids']}.",
        f"Selected/excluded overlap check: {metrics['excluded_overlap']}.",
        f"Duplicate selected ids: {metrics['duplicate_ids']}.",
        "",
        "## Source Distribution",
        "",
        *md_table(["Source", "Selected", "Eligible", "Clean pool"], rows),
        "",
        "## Notes",
        "",
        "- Keep this eval set small because the teacher comparison pass is the slow step.",
        "- Use one teacher call per prompt to compare all four model outputs anonymously.",
        "- The reference output is preserved for judge context, but final scoring should compare the generated answers for usefulness and correctness.",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    quotas = {
        "finetome": args.finetome,
        "cot_zh": args.cot_zh,
        "openmath_reasoning": args.openmath_reasoning,
    }
    rng = random.Random(args.seed)

    output_paths = {
        args.output.resolve(),
        args.metrics_json.resolve(),
        args.report_md.resolve(),
    }
    output_dirs = {
        OUT_DIR.resolve(),
        args.lf_output_dir.resolve(),
    }
    excluded, excluded_by_area = load_excluded_ids(output_paths, output_dirs)

    selected_raw: list[dict[str, Any]] = []
    raw_counts: dict[str, int] = {}
    clean_counts: dict[str, int] = {}
    eligible_counts: dict[str, int] = {}
    for source in SOURCE_ORDER:
        path = PROCESSED_DIR / f"{source}.jsonl"
        records = read_jsonl(path)
        raw_counts[source] = len(records)
        clean = [
            record
            for record in records
            if bool(record.get("is_clean")) and not (record.get("flags") if isinstance(record.get("flags"), list) else [])
        ]
        clean_counts[source] = len(clean)
        eligible = [record for record in clean if record.get("id") not in excluded]
        eligible_counts[source] = len(eligible)
        selected_raw.extend(stratified_sample(eligible, quotas[source], rng))
        print(f"{source}: sampled {quotas[source]} from {len(eligible)} eligible")

    rng.shuffle(selected_raw)
    selected_ids = [record.get("id") for record in selected_raw]
    duplicate_ids = len(selected_ids) - len(set(selected_ids))
    excluded_overlap = len(set(selected_ids) & excluded)
    if duplicate_ids:
        raise ValueError(f"Selected sample contains {duplicate_ids} duplicate id(s)")
    if excluded_overlap:
        raise ValueError(f"Selected sample overlaps excluded ids: {excluded_overlap}")

    out_records = [
        compact_eval_record(record, index=index, seed=args.seed)
        for index, record in enumerate(selected_raw)
    ]
    write_jsonl(args.output, out_records)
    write_lf_dataset(out_records, args.lf_output_dir)

    by_source = Counter(record["source"] for record in out_records)
    by_language = Counter(record.get("language") for record in out_records)
    by_task = Counter(record.get("task_type") for record in out_records)
    metrics = {
        "total": len(out_records),
        "seed": args.seed,
        "quotas": quotas,
        "outputs": {
            "sample": rel(args.output),
            "metrics": rel(args.metrics_json),
            "lf_dataset_dir": rel(args.lf_output_dir),
            "lf_dataset": "phase_e_downstream_eval_200",
            "report": rel(args.report_md),
        },
        "excluded_ids": len(excluded),
        "excluded_by_area": excluded_by_area,
        "raw_counts": raw_counts,
        "clean_counts": clean_counts,
        "eligible_counts": eligible_counts,
        "by_source": dict(by_source),
        "by_language": dict(by_language),
        "by_task_type": dict(by_task),
        "duplicate_ids": duplicate_ids,
        "excluded_overlap": excluded_overlap,
    }
    args.metrics_json.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_json.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(args.report_md, metrics)

    print(f"wrote sample: {rel(args.output)}")
    print(f"wrote metrics: {rel(args.metrics_json)}")
    print(f"wrote LF dataset: {rel(args.lf_output_dir)}")
    print(f"wrote report: {rel(args.report_md)}")


if __name__ == "__main__":
    main()
