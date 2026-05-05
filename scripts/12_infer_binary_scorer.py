#!/usr/bin/env python3
"""Run a binary data-quality scorer on unlabeled candidate JSONL files.

The script uses the same binary scorer prompt as `09_build_binary_scorer_sft.py`
and writes one JSONL record per scored candidate. It supports resume-by-id so a
large pool can be scored over multiple sessions.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "processed" / "unified_sft_clean.jsonl"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "scored" / "binary_scorer_predictions.jsonl"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "binary_scorer_inference_report.md"
DEFAULT_METRICS = PROJECT_ROOT / "data" / "scored" / "binary_scorer_inference_metrics.json"
DEFAULT_MODEL = "Qwen/Qwen3-8B"
DEFAULT_ADAPTER = Path(r"C:\Users\haoran27\llamafactory_outputs\scorer_binary_v3_conservative_qwen3_8b_lora_e3")
DEFAULT_RUN_NAME = "scorer_binary_v3_conservative_qwen3_8b_lora_e3"
VERDICTS = ["keep", "not_keep"]

BINARY_SYSTEM = (
    "You are a binary data quality filter for supervised fine-tuning samples. "
    "Judge whether an instruction-output pair is usable training data for a small language model. "
    "Return only valid JSON with this schema: {\"verdict\": \"keep|not_keep\"}. "
    "Use keep only for samples that are clearly useful, correct, relevant, complete, and not corrupted. "
    "Use not_keep for incorrect, irrelevant, incomplete, corrupted, or ambiguous samples."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Infer binary scorer labels for unlabeled SFT candidate JSONL files.")
    parser.add_argument("--input", type=Path, nargs="+", default=[DEFAULT_INPUT], help="Candidate JSONL file(s).")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output scored JSONL path.")
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT, help="Markdown summary report path.")
    parser.add_argument("--metrics-json", type=Path, default=DEFAULT_METRICS, help="Machine-readable summary JSON path.")
    parser.add_argument("--run-name", type=str, default=DEFAULT_RUN_NAME)
    parser.add_argument("--model-name-or-path", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--adapter-name-or-path", type=Path, default=DEFAULT_ADAPTER)
    parser.add_argument("--max-samples", type=int, default=None, help="Optional cap after reading/skipping inputs.")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--device-map", type=str, default="auto")
    parser.add_argument("--torch-dtype", choices=["auto", "float16", "bfloat16", "float32"], default="auto")
    parser.add_argument("--trust-remote-code", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--resume-valid-only",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="When resuming, skip only existing rows with a valid keep/not_keep schema.",
    )
    parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Render scorer prompts and reports without loading or running the model.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as file:
        for line_no, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
        file.flush()


def console_safe(text: Any) -> str:
    return str(text).encode("ascii", errors="backslashreplace").decode("ascii")


def record_key(record: dict[str, Any]) -> str:
    return str(record.get("teacher_sample_id") or record.get("pilot_sample_id") or record.get("id"))


def compact_metadata(record: dict[str, Any]) -> dict[str, Any]:
    meta = record.get("meta") if isinstance(record.get("meta"), dict) else {}
    useful_meta: dict[str, Any] = {}
    for key in ["expected_answer", "problem_type", "pass_rate_72b_tir", "score", "input", "original_source", "original_score"]:
        if key in meta and meta[key] not in (None, ""):
            useful_meta[key] = meta[key]
    return useful_meta


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


def parse_json_object(value: Any) -> tuple[dict[str, Any] | None, bool]:
    if isinstance(value, dict):
        return value, True
    if value is None:
        return None, False
    text = str(value).strip()
    try:
        obj = json.loads(text)
        return (obj, isinstance(obj, dict))
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None, False
    try:
        obj = json.loads(match.group(0))
        return (obj, isinstance(obj, dict))
    except json.JSONDecodeError:
        return None, False


def is_schema_valid(obj: dict[str, Any] | None) -> bool:
    return isinstance(obj, dict) and obj.get("verdict") in VERDICTS


def existing_completed_keys(path: Path, valid_only: bool) -> set[str]:
    if not path.exists():
        return set()

    completed: set[str] = set()
    for record in read_jsonl(path):
        if record.get("prompt_only"):
            continue
        key = record_key(record)
        if not key:
            continue
        if not valid_only or record.get("prediction_schema_valid"):
            completed.add(key)
    return completed


def load_candidates(paths: list[Path], completed_keys: set[str], max_samples: int | None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        for record in read_jsonl(path):
            key = record_key(record)
            if not key or key in seen or key in completed_keys:
                continue
            seen.add(key)
            record["_input_path"] = str(path)
            records.append(record)
            if max_samples is not None and len(records) >= max_samples:
                return records
    return records


def render_chat_prompt(tokenizer: Any, user_prompt: str) -> str:
    messages = [
        {"role": "system", "content": BINARY_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def load_model_and_tokenizer(args: argparse.Namespace) -> tuple[Any, Any]:
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "Install/import `torch`, `transformers`, and `peft`, or run with `--prompt-only` to render prompts only."
        ) from exc

    dtype_map = {
        "auto": "auto",
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path, trust_remote_code=args.trust_remote_code)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name_or_path,
        device_map=args.device_map,
        torch_dtype=dtype_map[args.torch_dtype],
        trust_remote_code=args.trust_remote_code,
    )
    model = PeftModel.from_pretrained(model, str(args.adapter_name_or_path))
    model.eval()
    return model, tokenizer


def generate_batch(model: Any, tokenizer: Any, prompts: list[str], max_new_tokens: int) -> list[str]:
    import torch

    encoded = tokenizer(prompts, return_tensors="pt", padding=True)
    input_width = encoded["input_ids"].shape[1]
    device = next(model.parameters()).device
    encoded = {key: value.to(device) for key, value in encoded.items()}

    with torch.inference_mode():
        output_ids = model.generate(
            **encoded,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated: list[str] = []
    for ids in output_ids:
        new_ids = ids[input_width:]
        generated.append(tokenizer.decode(new_ids, skip_special_tokens=True).strip())
    return generated


def build_output_record(candidate: dict[str, Any], raw_prediction: str | None, prompt: str, args: argparse.Namespace) -> dict[str, Any]:
    pred_obj, pred_json_ok = parse_json_object(raw_prediction)
    schema_valid = is_schema_valid(pred_obj)
    flags = candidate.get("flags") if isinstance(candidate.get("flags"), list) else []
    sampling = candidate.get("sampling") if isinstance(candidate.get("sampling"), dict) else {}

    return {
        "id": candidate.get("id"),
        "teacher_sample_id": candidate.get("teacher_sample_id"),
        "pilot_sample_id": candidate.get("pilot_sample_id"),
        "source": candidate.get("source"),
        "language": candidate.get("language"),
        "task_type": candidate.get("task_type"),
        "split": candidate.get("split"),
        "is_clean": candidate.get("is_clean"),
        "flags": flags,
        "sampling": sampling,
        "instruction_len": candidate.get("instruction_len"),
        "output_len": candidate.get("output_len"),
        "input_path": candidate.get("_input_path"),
        "run_name": args.run_name,
        "model_name_or_path": args.model_name_or_path,
        "adapter_name_or_path": str(args.adapter_name_or_path),
        "prompt_only": bool(args.prompt_only),
        "prompt": prompt,
        "raw_prediction": raw_prediction,
        "prediction": pred_obj,
        "prediction_json_valid": pred_json_ok,
        "prediction_schema_valid": schema_valid,
        "verdict": pred_obj.get("verdict") if schema_valid and pred_obj else None,
        "scored_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def pct(num: int | float, den: int | float) -> str:
    return f"{100 * num / den:.2f}%" if den else "0.00%"


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def summarize_output(path: Path) -> dict[str, Any]:
    rows = read_jsonl(path) if path.exists() else []
    verdict_counts = Counter(row.get("verdict") or "invalid" for row in rows)
    source_counts: dict[str, Counter[str]] = defaultdict(Counter)
    flag_counts = Counter()
    conflict_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for row in rows:
        source = row.get("source") or "unknown"
        verdict = row.get("verdict") or "invalid"
        source_counts[source]["records"] += 1
        source_counts[source][verdict] += 1
        source_counts[source]["schema_valid"] += int(bool(row.get("prediction_schema_valid")))
        flags = row.get("flags") if isinstance(row.get("flags"), list) else []
        clean = bool(row.get("is_clean"))
        if flags:
            for flag in flags:
                flag_counts[str(flag)] += 1
        if verdict == "keep" and (not clean or flags):
            conflict_counts[source]["flagged_keep"] += 1
        if verdict == "not_keep" and clean and not flags:
            conflict_counts[source]["clean_not_keep"] += 1

    return {
        "records": len(rows),
        "verdict_counts": dict(verdict_counts),
        "source_counts": {source: dict(counter) for source, counter in source_counts.items()},
        "flag_counts": dict(flag_counts),
        "conflict_counts": {source: dict(counter) for source, counter in conflict_counts.items()},
    }


def write_summary(report_path: Path, metrics_path: Path, output_path: Path, args: argparse.Namespace) -> None:
    summary = summarize_output(output_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    records = int(summary["records"])
    verdict_counts = summary["verdict_counts"]
    source_rows = []
    for source, counts in sorted(summary["source_counts"].items()):
        source_records = int(counts.get("records", 0))
        source_rows.append(
            [
                source,
                source_records,
                counts.get("keep", 0),
                counts.get("not_keep", 0),
                counts.get("invalid", 0),
                pct(counts.get("schema_valid", 0), source_records),
            ]
        )

    conflict_rows = []
    for source, counts in sorted(summary["conflict_counts"].items()):
        conflict_rows.append([source, counts.get("flagged_keep", 0), counts.get("clean_not_keep", 0)])

    lines = [
        "# Binary Scorer Inference Report",
        "",
        "## Report Metadata",
        "",
        markdown_table(
            ["Field", "Value"],
            [
                ["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ["Report type", "Batch inference summary"],
                ["Project stage", "Scorer deployment / data pool triage"],
                ["Report status", "Generated"],
            ],
        ),
        "",
        "## Experiment Context",
        "",
        markdown_table(
            ["Field", "Value"],
            [
                ["Run name", f"`{args.run_name}`"],
                ["Model", f"`{args.model_name_or_path}`"],
                ["Adapter", f"`{args.adapter_name_or_path}`"],
                ["Output JSONL", f"`{output_path}`"],
                ["Prompt only", str(bool(args.prompt_only))],
            ],
        ),
        "",
        "## Summary",
        "",
        markdown_table(
            ["Metric", "Value"],
            [
                ["Records", records],
                ["keep", verdict_counts.get("keep", 0)],
                ["not_keep", verdict_counts.get("not_keep", 0)],
                ["invalid", verdict_counts.get("invalid", 0)],
                ["schema_valid_rate", pct(verdict_counts.get("keep", 0) + verdict_counts.get("not_keep", 0), records)],
            ],
        ),
        "",
        "## Source Breakdown",
        "",
        markdown_table(["Source", "Records", "Keep", "Not Keep", "Invalid", "Schema Valid"], source_rows),
        "",
        "## Rule/Model Triage Buckets",
        "",
        markdown_table(["Source", "Flagged But Predicted Keep", "Clean But Predicted Not Keep"], conflict_rows),
        "",
        "## Recommended Next Actions",
        "",
        "- Inspect `flagged_keep` examples as likely rule/model disagreements.",
        "- Inspect `clean_not_keep` examples as likely hard negatives or over-conservative predictions.",
        "- Send disagreement and high-impact examples to the teacher model before adding irreversible drop rules.",
        "",
    ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def batched(records: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [records[index : index + size] for index in range(0, len(records), size)]


def main() -> None:
    args = parse_args()
    if args.batch_size < 1:
        raise ValueError("--batch-size must be >= 1")

    completed = existing_completed_keys(args.output, args.resume_valid_only) if args.resume else set()
    candidates = load_candidates(args.input, completed, args.max_samples)
    print(
        json.dumps(
            {
                "input_files": [str(path) for path in args.input],
                "output": str(args.output),
                "resume": args.resume,
                "already_completed": len(completed),
                "to_score": len(candidates),
                "prompt_only": args.prompt_only,
            },
            ensure_ascii=True,
            indent=2,
        ),
        flush=True,
    )

    model = tokenizer = None
    if not args.prompt_only and candidates:
        model, tokenizer = load_model_and_tokenizer(args)

    batches = batched(candidates, args.batch_size)
    for batch_index, batch in enumerate(batches, start=1):
        user_prompts = [build_user_prompt(candidate) for candidate in batch]
        if args.prompt_only:
            chat_prompts = [f"{BINARY_SYSTEM}\n\n{prompt}" for prompt in user_prompts]
            raw_predictions = [None for _ in batch]
        else:
            assert model is not None and tokenizer is not None
            chat_prompts = [render_chat_prompt(tokenizer, prompt) for prompt in user_prompts]
            raw_predictions = generate_batch(model, tokenizer, chat_prompts, args.max_new_tokens)

        for candidate, prompt, raw_prediction in zip(batch, chat_prompts, raw_predictions):
            append_jsonl(args.output, build_output_record(candidate, raw_prediction, prompt, args))

        print(f"[{batch_index}/{len(batches)}] wrote {len(batch)} records", flush=True)

    write_summary(args.report_md, args.metrics_json, args.output, args)
    print(console_safe(f"Wrote scored JSONL: {args.output}"))
    print(console_safe(f"Wrote report: {args.report_md}"))
    print(console_safe(f"Wrote metrics: {args.metrics_json}"))


if __name__ == "__main__":
    main()
