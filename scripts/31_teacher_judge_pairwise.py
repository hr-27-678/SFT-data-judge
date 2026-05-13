"""Pairwise Teacher Judge over the Phase E downstream models.

For each eval prompt, send the candidate model outputs to the teacher in a
randomized A/B/C/D/E order and ask for a full ranking. Output JSONL records
include the letter->model mapping so downstream aggregation can recover which
real model placed where.

Reads:  data/eval/phase_e_downstream_eval/phase_e_downstream_prediction_comparison.jsonl
Writes: data/eval/phase_e_downstream_eval/phase_e_downstream_pairwise_labels_5model.jsonl

Environment variables required for real runs (set them before running):
  TEACHER_API_KEY
  TEACHER_BASE_URL  (e.g. https://api.openai.com/v1)
  TEACHER_MODEL
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "eval" / "phase_e_downstream_eval" / "phase_e_downstream_prediction_comparison.jsonl"
DEFAULT_PROMPT = PROJECT_ROOT / "prompts" / "teacher_judge_pairwise_prompt.md"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "eval" / "phase_e_downstream_eval" / "phase_e_downstream_pairwise_labels_5model.jsonl"

LETTERS = ["A", "B", "C", "D", "E"]
MODELS = ["unfiltered", "v4_conservative_keep", "v4_confident_keep", "v4_both_keep", "v4_persource_keep"]
VALID_CORRECTNESS = {"correct", "partial", "wrong", "unparseable"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pairwise teacher judge over Phase E downstream models.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--prompt-template", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.3)
    parser.add_argument("--max-candidate-chars", type=int, default=6000,
                        help="Trim each candidate output before sending to the teacher.")
    parser.add_argument("--max-reference-chars", type=int, default=6000)
    parser.add_argument("--seed", type=int, default=20260511,
                        help="Seed for per-record A/B/C/D shuffle; deterministic given (seed, eval_id).")
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--response-format", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--concurrency", type=int, default=1,
                        help="Number of parallel API calls. >1 enables a thread pool.")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8-sig") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))
    return records


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
        file.flush()


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done: set[str] = set()
    for r in read_jsonl(path):
        if r.get("teacher_label") is not None and not r.get("validation_errors"):
            done.add(str(r.get("phase_e_eval_id")))
    return done


def trim(text: str, limit: int) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[TRUNCATED]"


def per_record_seed(base_seed: int, eval_id: str) -> int:
    h = hashlib.sha256(f"{base_seed}:{eval_id}".encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def assign_letters(eval_id: str, base_seed: int) -> dict[str, str]:
    """Return {letter: model_name} with a deterministic per-record shuffle."""
    rng = random.Random(per_record_seed(base_seed, eval_id))
    shuffled = MODELS.copy()
    rng.shuffle(shuffled)
    return dict(zip(LETTERS, shuffled))


def render_prompt(template: str, record: dict[str, Any], letter_to_model: dict[str, str],
                  max_candidate_chars: int, max_reference_chars: int) -> str:
    predictions = record.get("predictions", {})

    def get_pred(model_name: str) -> str:
        entry = predictions.get(model_name, {})
        if not isinstance(entry, dict):
            return ""
        return entry.get("predict") or ""

    replacements = {
        "{source}": record.get("source", ""),
        "{language}": record.get("language", ""),
        "{task_type}": record.get("task_type", ""),
        "{metadata}": json.dumps({"phase_e_eval_id": record.get("phase_e_eval_id")}, ensure_ascii=False),
        "{instruction}": record.get("instruction", ""),
        "{reference_output}": trim(record.get("reference_output", ""), max_reference_chars),
        "{candidate_a}": trim(get_pred(letter_to_model["A"]), max_candidate_chars),
        "{candidate_b}": trim(get_pred(letter_to_model["B"]), max_candidate_chars),
        "{candidate_c}": trim(get_pred(letter_to_model["C"]), max_candidate_chars),
        "{candidate_d}": trim(get_pred(letter_to_model["D"]), max_candidate_chars),
        "{candidate_e}": trim(get_pred(letter_to_model["E"]), max_candidate_chars),
    }
    prompt = template
    for k, v in replacements.items():
        prompt = prompt.replace(k, v)
    return prompt


def extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    if start == -1:
        raise json.JSONDecodeError("no JSON object found", text, 0)
    decoder = json.JSONDecoder()
    try:
        obj, _ = decoder.raw_decode(text[start:])
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    end = text.rfind("}")
    if end <= start:
        raise json.JSONDecodeError("could not isolate JSON object", text, start)
    return json.loads(text[start:end + 1])


def validate_label(label: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ranking = label.get("ranking")
    if not isinstance(ranking, list) or len(ranking) != len(LETTERS) or sorted(ranking) != LETTERS:
        errors.append(f"ranking must be a permutation of {LETTERS}")
    best = label.get("best")
    worst = label.get("worst")
    if isinstance(ranking, list) and len(ranking) == 4:
        if best != ranking[0]:
            errors.append("best must equal ranking[0]")
        if worst != ranking[-1]:
            errors.append("worst must equal ranking[-1]")
    correctness = label.get("correctness")
    if not isinstance(correctness, dict):
        errors.append("correctness must be an object")
    else:
        for letter in LETTERS:
            v = correctness.get(letter)
            if v not in VALID_CORRECTNESS:
                errors.append(f"correctness.{letter} must be one of {sorted(VALID_CORRECTNESS)}")
    reason = label.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append("reason must be a non-empty string")
    return errors


def call_openai_compatible(prompt: str, use_response_format: bool) -> str:
    api_key = os.getenv("TEACHER_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("TEACHER_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("TEACHER_MODEL")
    if not api_key:
        raise RuntimeError("Set TEACHER_API_KEY or OPENAI_API_KEY.")
    if not model:
        raise RuntimeError("Set TEACHER_MODEL.")
    payload: dict[str, Any] = {
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
    with urllib.request.urlopen(request, timeout=180) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def validate_runtime_config(dry_run: bool) -> None:
    if dry_run:
        return
    missing = []
    if not (os.getenv("TEACHER_API_KEY") or os.getenv("OPENAI_API_KEY")):
        missing.append("TEACHER_API_KEY or OPENAI_API_KEY")
    if not os.getenv("TEACHER_MODEL"):
        missing.append("TEACHER_MODEL")
    if missing:
        raise RuntimeError("Missing environment variables: " + ", ".join(missing))


def main() -> None:
    args = parse_args()
    validate_runtime_config(args.dry_run)
    template = args.prompt_template.read_text(encoding="utf-8")
    records = read_jsonl(args.input)
    if args.max_samples is not None:
        records = records[: args.max_samples]

    output_path = args.output
    if args.dry_run:
        output_path = output_path.with_name(output_path.stem + "_dryrun.jsonl")

    if not args.dry_run and not args.resume:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("", encoding="utf-8")

    done = completed_ids(output_path) if (args.resume and not args.dry_run) else set()
    if done:
        print(f"Resuming from {output_path}: {len(done)} records already labeled, will be skipped.", flush=True)

    dryrun_outputs: list[dict[str, Any]] = []
    written = 0
    skipped = 0

    def build_unit(idx: int, record: dict[str, Any]) -> dict[str, Any]:
        eval_id = str(record.get("phase_e_eval_id"))
        letter_to_model = assign_letters(eval_id, args.seed)
        model_to_letter = {m: l for l, m in letter_to_model.items()}
        prompt = render_prompt(template, record, letter_to_model,
                               args.max_candidate_chars, args.max_reference_chars)
        base = {
            "phase_e_eval_id": eval_id,
            "id": record.get("id"),
            "source": record.get("source"),
            "language": record.get("language"),
            "task_type": record.get("task_type"),
            "letter_to_model": letter_to_model,
            "model_to_letter": model_to_letter,
        }
        return {"idx": idx, "record": record, "eval_id": eval_id, "base": base, "prompt": prompt}

    if args.dry_run:
        for idx, record in enumerate(records):
            unit = build_unit(idx, record)
            dryrun_outputs.append({**unit["base"], "prompt": unit["prompt"]})
            print(f"[{idx + 1}/{len(records)}] rendered {record.get('source')} {unit['eval_id']}", flush=True)
        write_jsonl(output_path, dryrun_outputs)
        written = len(dryrun_outputs)
    else:
        write_lock = threading.Lock()
        units = [build_unit(idx, rec) for idx, rec in enumerate(records)]
        pending = []
        for u in units:
            if u["eval_id"] in done:
                skipped += 1
                print(f"[{u['idx'] + 1}/{len(records)}] skipped {u['eval_id']} already_labeled", flush=True)
            else:
                pending.append(u)

        def worker(u: dict[str, Any]) -> None:
            nonlocal written
            try:
                raw = call_openai_compatible(u["prompt"], args.response_format)
                label = extract_json_object(raw)
                errors = validate_label(label)
                out_record = {**u["base"], "teacher_label": label, "raw_teacher_response": raw,
                              "validation_errors": errors}
                status = "ok" if not errors else "schema_error"
                msg = f"[{u['idx'] + 1}/{len(records)}] labeled {u['eval_id']} {status}"
            except Exception as exc:
                out_record = {**u["base"], "teacher_label": None, "raw_teacher_response": None,
                              "validation_errors": [f"{type(exc).__name__}: {exc}"]}
                msg = f"[{u['idx'] + 1}/{len(records)}] failed {u['eval_id']}: {type(exc).__name__}: {exc}"
            with write_lock:
                append_jsonl(output_path, out_record)
                written += 1
            print(msg, flush=True)

        concurrency = max(1, int(args.concurrency))
        if concurrency == 1:
            for i, u in enumerate(pending):
                worker(u)
                if i < len(pending) - 1:
                    time.sleep(args.sleep)
        else:
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = [pool.submit(worker, u) for u in pending]
                for _ in as_completed(futures):
                    pass

    print(json.dumps({
        "output": str(output_path),
        "records": written,
        "skipped": skipped,
        "mode": "dry-run" if args.dry_run else "real",
        "resume": args.resume,
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
