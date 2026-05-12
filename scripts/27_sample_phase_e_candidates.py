"""Sample exclusion-safe clean candidates for Phase E downstream SFT.

This sampler prepares the unlabeled pool that will be scored by the local
v4 conservative and v4 confident binary scorers. The output is not teacher
training data. It is a fixed candidate pool for downstream filtering tests.

Policy:
- sample from `data/processed/by_source/*.jsonl`
- require `is_clean=True`
- match the production clean source distribution
- balance short/medium/long output-length buckets within each source
- exclude any original sample id already used in scorer training/eval,
  teacher labeling, evergreen evaluation, or human verification files
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
OUT_DIR = PROJECT_ROOT / "data" / "splits" / "phase_e"
REPORT_PATH = PROJECT_ROOT / "reports" / "phase_e_clean_candidate_sampling_report.md"

SOURCE_ORDER = ["cot_zh", "finetome", "openmath_reasoning"]
EXCLUDE_DIRS = [
    PROJECT_ROOT / "data" / "labeled",
    PROJECT_ROOT / "data" / "splits" / "teacher_judge",
    PROJECT_ROOT / "data" / "eval",
]

ID_KEYS = {
    "id",
    "sample_id",
    "original_id",
    "original_sample_id",
    "source_id",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--total", type=int, default=15000)
    parser.add_argument("--seed", type=int, default=20260508)
    parser.add_argument("--output", type=Path, default=None)
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
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


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


def load_excluded_ids() -> tuple[set[str], dict[str, int]]:
    excluded: set[str] = set()
    by_area: dict[str, int] = {}
    for root in EXCLUDE_DIRS:
        if not root.exists():
            by_area[str(root.relative_to(PROJECT_ROOT))] = 0
            continue

        before = len(excluded)
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix == ".jsonl":
                excluded.update(collect_ids_from_jsonl(path))
            elif path.suffix == ".json":
                excluded.update(collect_ids_from_json(path))
        by_area[str(root.relative_to(PROJECT_ROOT))] = len(excluded) - before
    return excluded, by_area


def length_bucket(record: dict[str, Any], q33: int, q66: int) -> str:
    value = int(record.get("output_len", 0) or 0)
    if value <= q33:
        return "short"
    if value <= q66:
        return "medium"
    return "long"


def stratified_sample(records: list[dict[str, Any]], target: int, rng: random.Random) -> list[dict[str, Any]]:
    if target <= 0 or not records:
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
            raise ValueError(f"Not enough eligible records in {bucket}: need {want}, found {len(pool)}")
        selected.extend(pool[:want])

    return selected


def compute_source_quotas(eligible_counts: dict[str, int], total: int) -> dict[str, int]:
    available = sum(eligible_counts.values())
    if total > available:
        raise ValueError(f"Requested {total} records but only {available} are eligible")

    quotas = {source: round(total * eligible_counts[source] / available) for source in SOURCE_ORDER}
    drift = total - sum(quotas.values())
    quotas["finetome"] += drift
    return quotas


def default_output_path(total: int) -> Path:
    suffix = f"{total // 1000}k" if total % 1000 == 0 else str(total)
    return OUT_DIR / f"phase_e_clean_candidate_{suffix}.jsonl"


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    output_path = args.output or default_output_path(args.total)
    metrics_path = args.metrics_json or OUT_DIR / f"{output_path.stem}_metrics.json"

    excluded, excluded_by_area = load_excluded_ids()
    print(f"excluded ids: {len(excluded)}")
    for area, count in excluded_by_area.items():
        print(f"  {area}: +{count}")

    source_records: dict[str, list[dict[str, Any]]] = {}
    eligible_counts: dict[str, int] = {}
    raw_counts: dict[str, int] = {}
    clean_counts: dict[str, int] = {}

    for source in SOURCE_ORDER:
        path = PROCESSED_DIR / f"{source}.jsonl"
        records = read_jsonl(path)
        raw_counts[source] = len(records)
        clean_records = [record for record in records if bool(record.get("is_clean"))]
        clean_counts[source] = len(clean_records)
        eligible = [record for record in clean_records if record.get("id") not in excluded]
        source_records[source] = eligible
        eligible_counts[source] = len(eligible)

    quotas = compute_source_quotas(eligible_counts, args.total)

    selected: list[dict[str, Any]] = []
    for source in SOURCE_ORDER:
        sampled = stratified_sample(source_records[source], quotas[source], rng)
        print(f"{source}: sampled {len(sampled)}/{quotas[source]} from {eligible_counts[source]} eligible")
        selected.extend(sampled)

    rng.shuffle(selected)
    selected_ids = [record.get("id") for record in selected]
    duplicate_count = len(selected_ids) - len(set(selected_ids))
    excluded_overlap = len(set(selected_ids) & excluded)
    if duplicate_count:
        raise ValueError(f"Sample contains {duplicate_count} duplicate ids")
    if excluded_overlap:
        raise ValueError(f"Sample contains {excluded_overlap} excluded ids")

    out_records: list[dict[str, Any]] = []
    for index, record in enumerate(selected):
        item = dict(record)
        item["phase_e_sample_id"] = f"phase_e_clean_{index:05d}"
        item["selection"] = {
            "phase": "phase_e_downstream_sft",
            "selection_rank": index,
            "seed": args.seed,
            "target_total": args.total,
            "selection_reason": "clean_candidate_for_v4_binary_scorer_filtering",
            "exclusion_policy": "exclude data/labeled, data/splits/teacher_judge, and data/eval ids",
        }
        out_records.append(item)

    write_jsonl(output_path, out_records)

    by_source = Counter(record["source"] for record in out_records)
    by_language = Counter(record.get("language") for record in out_records)
    by_task = Counter(record.get("task_type") for record in out_records)
    metrics = {
        "total": len(out_records),
        "seed": args.seed,
        "output": str(output_path.relative_to(PROJECT_ROOT)),
        "excluded_ids": len(excluded),
        "excluded_by_area": excluded_by_area,
        "raw_counts": raw_counts,
        "clean_counts": clean_counts,
        "eligible_counts": eligible_counts,
        "quotas": quotas,
        "by_source": dict(by_source),
        "by_language": dict(by_language),
        "by_task_type": dict(by_task),
        "duplicate_ids": duplicate_count,
        "excluded_overlap": excluded_overlap,
    }
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# Phase E Clean Candidate Sampling Report",
                "",
                "## Purpose",
                "",
                "Prepare an exclusion-safe clean candidate pool for local v4 scorer labeling.",
                "Both v4 conservative and v4 confident should score this same file.",
                "",
                "## Output",
                "",
                f"- Candidate JSONL: `{output_path.relative_to(PROJECT_ROOT)}`",
                f"- Metrics JSON: `{metrics_path.relative_to(PROJECT_ROOT)}`",
                f"- Total: {len(out_records)}",
                f"- Seed: {args.seed}",
                "",
                "## Exclusion Policy",
                "",
                "Excluded any source sample id found under:",
                "",
                *[f"- `{area}`: +{count} ids" for area, count in excluded_by_area.items()],
                "",
                f"Total unique excluded ids: {len(excluded)}.",
                f"Selected/excluded overlap check: {excluded_overlap}.",
                f"Duplicate selected ids: {duplicate_count}.",
                "",
                "## Source Distribution",
                "",
                "| Source | Selected | Eligible | Clean pool |",
                "| --- | ---: | ---: | ---: |",
                *[
                    f"| `{source}` | {by_source.get(source, 0)} | {eligible_counts[source]} | {clean_counts[source]} |"
                    for source in SOURCE_ORDER
                ],
                f"| **Total** | **{len(out_records)}** | **{sum(eligible_counts.values())}** | **{sum(clean_counts.values())}** |",
                "",
                "## Next Commands",
                "",
                "```powershell",
                "$PY = \"C:\\Users\\haoran27\\miniconda3\\envs\\llamafactory\\python.exe\"",
                "",
                "& $PY scripts/12_infer_binary_scorer.py `",
                f"  --input {output_path.relative_to(PROJECT_ROOT)} `",
                "  --output data/scored/phase_e_v4_conservative_clean_15k.jsonl `",
                "  --report-md reports/phase_e_v4_conservative_clean_15k_inference_report.md `",
                "  --metrics-json data/scored/phase_e_v4_conservative_clean_15k_metrics.json `",
                "  --run-name phase_e_v4_conservative_clean_15k `",
                "  --adapter-name-or-path \"C:\\Users\\haoran27\\llamafactory_outputs\\scorer_binary_v4_conservative_qwen3_8b_lora_e3\" `",
                "  --batch-size 1 `",
                "  --torch-dtype bfloat16",
                "",
                "& $PY scripts/12_infer_binary_scorer.py `",
                f"  --input {output_path.relative_to(PROJECT_ROOT)} `",
                "  --output data/scored/phase_e_v4_confident_clean_15k.jsonl `",
                "  --report-md reports/phase_e_v4_confident_clean_15k_inference_report.md `",
                "  --metrics-json data/scored/phase_e_v4_confident_clean_15k_metrics.json `",
                "  --run-name phase_e_v4_confident_clean_15k `",
                "  --adapter-name-or-path \"C:\\Users\\haoran27\\llamafactory_outputs\\scorer_binary_v4_confident_qwen3_8b_lora_e3\" `",
                "  --batch-size 1 `",
                "  --torch-dtype bfloat16",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"wrote candidates: {output_path.relative_to(PROJECT_ROOT)}")
    print(f"wrote metrics: {metrics_path.relative_to(PROJECT_ROOT)}")
    print(f"wrote report: {REPORT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
