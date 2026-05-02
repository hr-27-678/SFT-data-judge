"""Run or dry-run Teacher Judge labeling.

Default mode is dry-run: render prompts for inspection without calling an API.
For real labeling, use an OpenAI-compatible chat completions endpoint via:

  TEACHER_API_KEY=...
  TEACHER_BASE_URL=https://api.openai.com/v1
  TEACHER_MODEL=...
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "pilot" / "pilot_candidates_all.jsonl"
DEFAULT_PROMPT = PROJECT_ROOT / "prompts" / "teacher_judge_prompt.md"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "labeled" / "teacher_judge"
DIMENSIONS = [
    "instruction_clarity",
    "response_relevance",
    "factual_or_answer_correctness",
    "reasoning_quality",
    "completeness",
    "data_integrity",
]
VERDICT_BY_SCORE = {1: "drop", 2: "drop", 3: "maybe", 4: "keep", 5: "keep"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render or run Teacher Judge labels.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--prompt-template", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--output-name", type=str, default="pilot_teacher_labels.jsonl")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.2, help="Sleep seconds between real API calls.")
    parser.add_argument("--max-output-chars", type=int, default=12000, help="Trim rendered output text for teacher calls.")
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="For real labeling, skip records that already have a non-null teacher_label in the output file.",
    )
    parser.add_argument(
        "--response-format",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Request JSON-object response_format from compatible APIs.",
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


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
        file.flush()


def record_key(record: dict[str, Any]) -> str:
    return str(record.get("teacher_sample_id") or record.get("pilot_sample_id") or record.get("id"))


def completed_keys_from_output(path: Path) -> set[str]:
    if not path.exists():
        return set()

    completed: set[str] = set()
    for record in read_jsonl(path):
        if record.get("teacher_label") is not None and not record.get("validation_errors"):
            completed.add(record_key(record))
    return completed


def safe_metadata(record: dict[str, Any]) -> str:
    metadata = record.get("meta", {}).copy()
    if "raw_output_len" in metadata:
        metadata["raw_output_len"] = int(metadata["raw_output_len"])
    return json.dumps(metadata, ensure_ascii=False, sort_keys=True)


def render_prompt(template: str, record: dict[str, Any], max_output_chars: int) -> str:
    output = record.get("output", "")
    if len(output) > max_output_chars:
        output = output[:max_output_chars] + "\n\n[TRUNCATED_FOR_JUDGE_PROMPT]"

    replacements = {
        "{source}": record.get("source", ""),
        "{language}": record.get("language", ""),
        "{task_type}": record.get("task_type", ""),
        "{metadata}": safe_metadata(record),
        "{instruction}": record.get("instruction", ""),
        "{output}": output,
    }
    prompt = template
    for key, value in replacements.items():
        prompt = prompt.replace(key, value)
    return prompt


def extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def validate_label(label: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    score = label.get("overall_score")
    if not isinstance(score, int) or not 1 <= score <= 5:
        errors.append("overall_score must be an integer from 1 to 5")

    dims = label.get("dimension_scores")
    if not isinstance(dims, dict):
        errors.append("dimension_scores must be an object")
    else:
        for dim in DIMENSIONS:
            value = dims.get(dim)
            if not isinstance(value, int) or not 1 <= value <= 5:
                errors.append(f"dimension_scores.{dim} must be an integer from 1 to 5")

    verdict = label.get("verdict")
    if score in VERDICT_BY_SCORE and verdict != VERDICT_BY_SCORE[score]:
        errors.append(f"verdict must be {VERDICT_BY_SCORE[score]} for overall_score={score}")

    if not isinstance(label.get("reason"), str) or not label.get("reason", "").strip():
        errors.append("reason must be a non-empty string")

    if not isinstance(label.get("major_issues"), list):
        errors.append("major_issues must be a list")

    return errors


def call_openai_compatible(prompt: str, use_response_format: bool) -> str:
    api_key = os.getenv("TEACHER_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("TEACHER_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("TEACHER_MODEL")
    if not api_key:
        raise RuntimeError("Set TEACHER_API_KEY or OPENAI_API_KEY for real teacher labeling.")
    if not model:
        raise RuntimeError("Set TEACHER_MODEL for real teacher labeling.")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    if use_response_format:
        payload["response_format"] = {"type": "json_object"}
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def main() -> None:
    args = parse_args()
    template = args.prompt_template.read_text(encoding="utf-8")
    records = read_jsonl(args.input)
    if args.max_samples is not None:
        records = records[: args.max_samples]

    suffix = "prompts" if args.dry_run else "labels"
    output_name = args.output_name
    if args.dry_run and output_name == "pilot_teacher_labels.jsonl":
        output_name = "pilot_teacher_prompts.jsonl"
    output_path = args.output_dir / output_name
    if not args.dry_run and not args.resume:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("", encoding="utf-8")

    completed_keys = completed_keys_from_output(output_path) if args.resume and not args.dry_run else set()
    if completed_keys:
        print(f"Resuming from {output_path}: {len(completed_keys)} completed records will be skipped.", flush=True)

    outputs: list[dict[str, Any]] = []
    written = 0
    skipped = 0
    for index, record in enumerate(records):
        prompt = render_prompt(template, record, args.max_output_chars)
        base = {
            "teacher_sample_id": record.get("teacher_sample_id"),
            "pilot_sample_id": record.get("pilot_sample_id"),
            "id": record.get("id"),
            "source": record.get("source"),
            "split": record.get("split"),
            "sampling": record.get("sampling"),
        }

        if args.dry_run:
            outputs.append({**base, "prompt": prompt})
            print(f"[{index + 1}/{len(records)}] rendered {record.get('source')} {record.get('id')}", flush=True)
            continue

        key = record_key(base)
        if key in completed_keys:
            skipped += 1
            print(f"[{index + 1}/{len(records)}] skipped {record.get('source')} {record.get('id')} already_labeled", flush=True)
            continue

        try:
            raw = call_openai_compatible(prompt, args.response_format)
            label = extract_json_object(raw)
            errors = validate_label(label)
            output_record = {**base, "teacher_label": label, "raw_teacher_response": raw, "validation_errors": errors}
            status = "ok" if not errors else "schema_error"
            print(f"[{index + 1}/{len(records)}] labeled {record.get('source')} {record.get('id')} {status}", flush=True)
        except (RuntimeError, urllib.error.URLError, json.JSONDecodeError, KeyError) as exc:
            output_record = {**base, "teacher_label": None, "raw_teacher_response": None, "validation_errors": [str(exc)]}
            print(f"[{index + 1}/{len(records)}] failed {record.get('source')} {record.get('id')}: {exc}", flush=True)

        append_jsonl(output_path, output_record)
        written += 1

        if index < len(records) - 1:
            time.sleep(args.sleep)

    if args.dry_run:
        write_jsonl(output_path, outputs)
        written = len(outputs)

    print(
        json.dumps(
            {
                "output": str(output_path),
                "records": written,
                "skipped": skipped,
                "mode": suffix,
                "resume": args.resume,
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
