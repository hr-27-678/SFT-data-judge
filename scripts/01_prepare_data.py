"""Phase 1 data preparation for SFT-DataJudge.

This script unifies the three current data sources into one JSONL schema and
produces a lightweight data report for later teacher judging and scorer SFT.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import load_from_disk


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LLAMAF_DATA = PROJECT_ROOT.parent / "LLaMA-Factory" / "data"
DEFAULT_MODEL_SCOPE_DATA = DEFAULT_LLAMAF_DATA / "qwen3-finetune-test"


@dataclass(frozen=True)
class SourcePaths:
    cot_zh_csv: Path
    finetome_train: Path
    openmath_cot: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare unified SFT data for SFT-DataJudge.")
    parser.add_argument(
        "--cot-zh-csv",
        type=Path,
        default=DEFAULT_LLAMAF_DATA / "CoT_Chinese_data.csv",
        help="Path to CoT-ZH CSV file.",
    )
    parser.add_argument(
        "--finetome-train",
        type=Path,
        default=DEFAULT_MODEL_SCOPE_DATA / "FineTome" / "train",
        help="Path to FineTome Hugging Face dataset split saved on disk.",
    )
    parser.add_argument(
        "--openmath-cot",
        type=Path,
        default=DEFAULT_MODEL_SCOPE_DATA / "OpenMathReasoning" / "cot",
        help="Path to OpenMathReasoning Hugging Face dataset split saved on disk.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed",
        help="Output directory for unified data and summary artifacts.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=PROJECT_ROOT / "reports" / "data_report.md",
        help="Markdown report path.",
    )
    parser.add_argument(
        "--min-instruction-len",
        type=int,
        default=10,
        help="Minimum stripped instruction length for clean subset.",
    )
    parser.add_argument(
        "--min-output-len",
        type=int,
        default=20,
        help="Minimum stripped output length for clean subset.",
    )
    parser.add_argument(
        "--max-output-len",
        type=int,
        default=32000,
        help="Maximum stripped output length for clean subset.",
    )
    return parser.parse_args()


def stable_hash(text: str, length: int = 12) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def normalize_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""

    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_think_block(text: Any) -> tuple[str, bool, int]:
    """Remove hidden/internal <think>...</think> blocks from model outputs.

    OpenMathReasoning stores both a private reasoning trace and a polished
    solution. For SFT, we keep the user-visible solution after </think>.
    """
    raw = normalize_text(text)
    raw_len = len(raw)
    lowered = raw.lower()
    end_tag = "</think>"

    if end_tag in lowered:
        end_index = lowered.index(end_tag) + len(end_tag)
        return normalize_text(raw[end_index:]), True, raw_len

    return raw, False, raw_len


def looks_like_mojibake(text: str) -> bool:
    if not text:
        return False

    # Avoid flagging normal accents such as "Vigenère" or "Méliès".
    # These markers target common UTF-8/Latin-1 mojibake fragments.
    markers = (
        "�",
        "Ã",
        "Â",
        "â€",
        "â€™",
        "â€œ",
        "â€",
        "ðŸ",
        "ã€",
        "ï¼",
        "ä¸",
        "æˆ",
        "çš",
        "å¾",
        "è°",
    )
    marker_count = sum(text.count(marker) for marker in markers)
    return "�" in text or marker_count >= 2


def has_repeated_punctuation(text: str) -> bool:
    # Normal math/text data can contain ellipses like "......".
    # Flag only severe repetition that is likely to be data corruption.
    return bool(re.search(r"([!?。！？,.，])\1{19,}", text))


def quality_flags(
    instruction: str,
    output: str,
    min_instruction_len: int,
    min_output_len: int,
    max_output_len: int,
) -> list[str]:
    flags: list[str] = []
    if not instruction:
        flags.append("empty_instruction")
    if not output:
        flags.append("empty_output")
    if 0 < len(instruction) < min_instruction_len:
        flags.append("short_instruction")
    if 0 < len(output) < min_output_len:
        flags.append("short_output")
    if len(output) > max_output_len:
        flags.append("long_output")
    if looks_like_mojibake(instruction) or looks_like_mojibake(output):
        flags.append("possible_mojibake")
    if has_repeated_punctuation(instruction) or has_repeated_punctuation(output):
        flags.append("repeated_punctuation")
    return flags


def make_record(
    source: str,
    source_index: int,
    language: str,
    task_type: str,
    instruction: Any,
    output: Any,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clean_instruction = normalize_text(instruction)
    clean_output = normalize_text(output)
    pair_hash = stable_hash(f"{clean_instruction}\n<OUTPUT>\n{clean_output}", 16)

    return {
        "id": f"{source}_{source_index:08d}_{pair_hash}",
        "source": source,
        "source_index": source_index,
        "language": language,
        "task_type": task_type,
        "instruction": clean_instruction,
        "output": clean_output,
        "instruction_len": len(clean_instruction),
        "output_len": len(clean_output),
        "pair_hash": pair_hash,
        "meta": meta or {},
    }


def load_cot_zh(path: Path) -> list[dict[str, Any]]:
    df = pd.read_csv(path)
    records: list[dict[str, Any]] = []

    for idx, row in df.iterrows():
        records.append(
            make_record(
                source="cot_zh",
                source_index=int(idx),
                language="zh",
                task_type="math_reasoning",
                instruction=row.get("instruction", ""),
                output=row.get("output", ""),
                meta={"input": normalize_text(row.get("input", ""))},
            )
        )

    return records


def first_conversation_value(conversations: Any, speaker: str) -> str:
    if not isinstance(conversations, list):
        return ""

    for turn in conversations:
        if isinstance(turn, dict) and turn.get("from") == speaker:
            return normalize_text(turn.get("value", ""))

    return ""


def load_finetome(path: Path) -> list[dict[str, Any]]:
    dataset = load_from_disk(str(path))
    records: list[dict[str, Any]] = []

    for idx, example in enumerate(dataset):
        instruction = first_conversation_value(example.get("conversations"), "human")
        output = first_conversation_value(example.get("conversations"), "gpt")
        records.append(
            make_record(
                source="finetome",
                source_index=idx,
                language="en",
                task_type="general_instruction",
                instruction=instruction,
                output=output,
                meta={
                    "original_source": example.get("source"),
                    "original_score": example.get("score"),
                },
            )
        )

    return records


def load_openmath(path: Path) -> list[dict[str, Any]]:
    dataset = load_from_disk(str(path))
    records: list[dict[str, Any]] = []

    for idx, example in enumerate(dataset):
        output, had_think, raw_output_len = strip_think_block(example.get("generated_solution", ""))
        records.append(
            make_record(
                source="openmath_reasoning",
                source_index=idx,
                language="en",
                task_type="math_reasoning",
                instruction=example.get("problem", ""),
                output=output,
                meta={
                    "expected_answer": normalize_text(example.get("expected_answer", "")),
                    "problem_type": example.get("problem_type"),
                    "pass_rate_72b_tir": example.get("pass_rate_72b_tir"),
                    "raw_output_had_think": had_think,
                    "raw_output_len": raw_output_len,
                },
            )
        )

    return records


def add_cleaning_fields(
    records: list[dict[str, Any]],
    min_instruction_len: int,
    min_output_len: int,
    max_output_len: int,
) -> None:
    pair_counts = Counter(record["pair_hash"] for record in records)

    for record in records:
        flags = quality_flags(
            record["instruction"],
            record["output"],
            min_instruction_len,
            min_output_len,
            max_output_len,
        )
        if pair_counts[record["pair_hash"]] > 1:
            flags.append("duplicate_pair")

        record["flags"] = sorted(set(flags))
        record["is_clean"] = len(record["flags"]) == 0


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def percentile(values: list[int], ratio: float) -> int | None:
    if not values:
        return None

    sorted_values = sorted(values)
    index = round((len(sorted_values) - 1) * ratio)
    return sorted_values[index]


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_source: dict[str, dict[str, Any]] = {}
    flag_counter = Counter()

    for source in sorted({record["source"] for record in records}):
        source_records = [record for record in records if record["source"] == source]
        instruction_lens = [record["instruction_len"] for record in source_records]
        output_lens = [record["output_len"] for record in source_records]
        clean_count = sum(record["is_clean"] for record in source_records)

        by_source[source] = {
            "total": len(source_records),
            "clean": clean_count,
            "clean_ratio": round(clean_count / len(source_records), 4) if source_records else 0.0,
            "language": dict(Counter(record["language"] for record in source_records)),
            "task_type": dict(Counter(record["task_type"] for record in source_records)),
            "instruction_len": {
                "min": min(instruction_lens) if instruction_lens else None,
                "p50": percentile(instruction_lens, 0.5),
                "p95": percentile(instruction_lens, 0.95),
                "max": max(instruction_lens) if instruction_lens else None,
            },
            "output_len": {
                "min": min(output_lens) if output_lens else None,
                "p50": percentile(output_lens, 0.5),
                "p95": percentile(output_lens, 0.95),
                "max": max(output_lens) if output_lens else None,
            },
        }

        for record in source_records:
            for flag in record["flags"]:
                flag_counter[f"{source}:{flag}"] += 1

    total = len(records)
    clean_total = sum(record["is_clean"] for record in records)

    return {
        "total": total,
        "clean": clean_total,
        "clean_ratio": round(clean_total / total, 4) if total else 0.0,
        "by_source": by_source,
        "flags": dict(flag_counter),
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    table = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        table.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(table)


def write_report(path: Path, summary: dict[str, Any], output_paths: dict[str, Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    source_rows = []
    for source, item in summary["by_source"].items():
        source_rows.append(
            [
                source,
                item["total"],
                item["clean"],
                item["clean_ratio"],
                item["instruction_len"]["p50"],
                item["instruction_len"]["p95"],
                item["output_len"]["p50"],
                item["output_len"]["p95"],
            ]
        )

    flag_rows_by_source: dict[str, list[list[Any]]] = defaultdict(list)
    for key, count in sorted(summary["flags"].items()):
        source, flag = key.split(":", 1)
        flag_rows_by_source[source].append([flag, count])

    lines = [
        "# Phase 1 Data Report",
        "",
        "This report is generated by `scripts/01_prepare_data.py`.",
        "",
        "## Outputs",
        "",
        markdown_table(
            ["Artifact", "Path"],
            [[name, path.as_posix()] for name, path in output_paths.items()],
        ),
        "",
        "## Overall",
        "",
        markdown_table(
            ["Metric", "Value"],
            [
                ["total_records", summary["total"]],
                ["clean_records", summary["clean"]],
                ["clean_ratio", summary["clean_ratio"]],
            ],
        ),
        "",
        "## Source Summary",
        "",
        markdown_table(
            [
                "source",
                "total",
                "clean",
                "clean_ratio",
                "inst_p50",
                "inst_p95",
                "out_p50",
                "out_p95",
            ],
            source_rows,
        ),
        "",
        "## Cleaning Flags",
        "",
    ]

    if flag_rows_by_source:
        for source, rows in flag_rows_by_source.items():
            lines.extend([f"### {source}", "", markdown_table(["flag", "count"], rows), ""])
    else:
        lines.append("No cleaning flags were found.")

    lines.extend(
        [
            "## Unified Schema",
            "",
            markdown_table(
                ["Field", "Meaning"],
                [
                    ["id", "Stable sample id built from source, index, and pair hash."],
                    ["source", "One of cot_zh, finetome, openmath_reasoning."],
                    ["language", "Current coarse language label."],
                    ["task_type", "Current coarse task label."],
                    ["instruction/output", "Normalized SFT pair."],
                    ["meta", "Source-specific fields retained for later analysis."],
                    ["flags", "Basic data-quality warning flags."],
                    ["is_clean", "True if no phase-1 cleaning flags were triggered."],
                ],
            ),
            "",
        "## Notes",
        "",
            "- The unified files are a common schema view, not a recommendation to sample all sources together.",
            "- Teacher-label sampling should be stratified by `source`, `task_type`, length buckets, and clean/flagged status.",
            "- Per-source JSONL files are emitted under `data/processed/by_source/` for source-specific sampling.",
            "- `is_clean` is intentionally conservative and rule-based. It is not the final quality score.",
            "- Duplicate detection uses exact normalized instruction-output pairs.",
            "- OpenMathReasoning `<think>...</think>` blocks are removed; the retained output is the polished solution after `</think>`.",
            "- Very long reasoning traces are kept unless they exceed the phase-1 max output length. Context-window truncation is a later training decision.",
            "- The next phase should sample from both clean and flagged data so the teacher judge can learn boundaries.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    paths = SourcePaths(
        cot_zh_csv=args.cot_zh_csv,
        finetome_train=args.finetome_train,
        openmath_cot=args.openmath_cot,
    )

    for name, path in paths.__dict__.items():
        if not path.exists():
            raise FileNotFoundError(f"{name} not found: {path}")

    records = []
    records.extend(load_cot_zh(paths.cot_zh_csv))
    records.extend(load_finetome(paths.finetome_train))
    records.extend(load_openmath(paths.openmath_cot))

    add_cleaning_fields(
        records,
        min_instruction_len=args.min_instruction_len,
        min_output_len=args.min_output_len,
        max_output_len=args.max_output_len,
    )

    clean_records = [record for record in records if record["is_clean"]]
    summary = summarize(records)

    processed_dir = args.processed_dir
    by_source_dir = processed_dir / "by_source"
    output_paths = {
        "unified_all": processed_dir / "unified_sft.jsonl",
        "unified_clean": processed_dir / "unified_sft_clean.jsonl",
        "summary": processed_dir / "data_summary.json",
        "report": args.report_path,
    }

    write_jsonl(output_paths["unified_all"], records)
    write_jsonl(output_paths["unified_clean"], clean_records)

    for source in sorted({record["source"] for record in records}):
        source_records = [record for record in records if record["source"] == source]
        source_clean_records = [record for record in source_records if record["is_clean"]]
        all_path = by_source_dir / f"{source}.jsonl"
        clean_path = by_source_dir / f"{source}_clean.jsonl"

        write_jsonl(all_path, source_records)
        write_jsonl(clean_path, source_clean_records)
        output_paths[f"{source}_all"] = all_path
        output_paths[f"{source}_clean"] = clean_path

    output_paths["summary"].write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(args.report_path, summary, output_paths)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
