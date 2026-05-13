"""Compare Phase E downstream eval predictions across filtering policies.

This script joins the fixed downstream eval set with Phase E LLaMA-Factory
prediction outputs. The metrics here are reference-overlap and
surface-quality proxies; they are not a substitute for human or LLM judging.

Outputs:
- data/eval/phase_e_downstream_eval/phase_e_downstream_prediction_comparison_metrics.json
- data/eval/phase_e_downstream_eval/phase_e_downstream_prediction_comparison.jsonl
- data/eval/phase_e_downstream_eval/phase_e_downstream_review_queue.jsonl
- reports/phase_e_downstream_prediction_comparison_report.md
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_SAMPLE = PROJECT_ROOT / "data" / "eval" / "phase_e_downstream_eval" / "sample.jsonl"
EVAL_OUT_DIR = PROJECT_ROOT / "data" / "eval" / "phase_e_downstream_eval"
REPORT_PATH = PROJECT_ROOT / "reports" / "phase_e_downstream_prediction_comparison_report.md"
LF_OUTPUT_ROOT = Path("C:/Users/haoran27/llamafactory_outputs")

MODEL_RUNS = [
    (
        "unfiltered",
        "phase_e_unfiltered_clean_15k_qwen3_8b_lora_e1_predict_eval_200",
    ),
    (
        "v4_conservative_keep",
        "phase_e_v4_conservative_keep_clean_15k_qwen3_8b_lora_e1_predict_eval_200",
    ),
    (
        "v4_confident_keep",
        "phase_e_v4_confident_keep_clean_15k_qwen3_8b_lora_e1_predict_eval_200",
    ),
    (
        "v4_both_keep",
        "phase_e_v4_both_keep_clean_15k_qwen3_8b_lora_e1_predict_eval_200",
    ),
    (
        "v4_persource_keep",
        "phase_e_v4_persource_keep_clean_15k_qwen3_8b_lora_e1_predict_eval_200",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Phase E downstream predictions.")
    parser.add_argument("--eval-sample", type=Path, default=EVAL_SAMPLE)
    parser.add_argument(
        "--metrics-json",
        type=Path,
        default=EVAL_OUT_DIR / "phase_e_downstream_prediction_comparison_metrics.json",
    )
    parser.add_argument(
        "--comparison-jsonl",
        type=Path,
        default=EVAL_OUT_DIR / "phase_e_downstream_prediction_comparison.jsonl",
    )
    parser.add_argument(
        "--review-jsonl",
        type=Path,
        default=EVAL_OUT_DIR / "phase_e_downstream_review_queue.jsonl",
    )
    parser.add_argument("--report-md", type=Path, default=REPORT_PATH)
    parser.add_argument("--output-root", type=Path, default=LF_OUTPUT_ROOT)
    parser.add_argument("--review-limit", type=int, default=60)
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


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]|[^\s]", re.UNICODE)
BOXED_RE = re.compile(r"\\boxed\s*\{")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text or "")]


def extract_boxed(text: str) -> str | None:
    """Return the content of the last \\boxed{...}, handling nested braces."""
    if not text:
        return None
    last = None
    for match in BOXED_RE.finditer(text):
        index = match.end()
        depth = 1
        buf: list[str] = []
        while index < len(text) and depth > 0:
            char = text[index]
            if char == "{":
                depth += 1
                buf.append(char)
            elif char == "}":
                depth -= 1
                if depth == 0:
                    break
                buf.append(char)
            else:
                buf.append(char)
            index += 1
        if depth == 0:
            last = "".join(buf)
    return last


_MATH_NORMALIZE_PATTERNS = [
    (re.compile(r"\\!"), ""),
    (re.compile(r"\\,"), ""),
    (re.compile(r"\\;"), ""),
    (re.compile(r"\\:"), ""),
    (re.compile(r"\\ "), ""),
    (re.compile(r"\\left"), ""),
    (re.compile(r"\\right"), ""),
    (re.compile(r"\s+"), ""),
]


def normalize_math_answer(text: str | None) -> str | None:
    if text is None:
        return None
    normalized = text.strip()
    for pattern, repl in _MATH_NORMALIZE_PATTERNS:
        normalized = pattern.sub(repl, normalized)
    return normalized


def math_answers_match(reference: str | None, prediction: str | None) -> bool:
    ref = normalize_math_answer(reference)
    pred = normalize_math_answer(prediction)
    return bool(ref and pred and ref == pred)


def unigram_f1(prediction: str, reference: str) -> float:
    pred_tokens = tokenize(prediction)
    ref_tokens = tokenize(reference)
    if not pred_tokens and not ref_tokens:
        return 1.0
    if not pred_tokens or not ref_tokens:
        return 0.0
    pred_counts = Counter(pred_tokens)
    ref_counts = Counter(ref_tokens)
    overlap = sum((pred_counts & ref_counts).values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(pred_tokens)
    recall = overlap / len(ref_tokens)
    return 2 * precision * recall / (precision + recall)


def duplicate_ngram_ratio(tokens: list[str], n: int = 8) -> float:
    if len(tokens) < n:
        return 0.0
    ngrams = [tuple(tokens[index : index + n]) for index in range(len(tokens) - n + 1)]
    counts = Counter(ngrams)
    repeated = sum(count - 1 for count in counts.values() if count > 1)
    return repeated / len(ngrams)


def repeated_line_count(text: str) -> int:
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) >= 24]
    if not lines:
        return 0
    counts = Counter(lines)
    return max(counts.values(), default=0)


def looks_complete(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return False
    if stripped.endswith((".", "?", "!", "。", "？", "！", ")", "]", "}", "$")):
        return True
    if stripped.endswith("\\]") or stripped.endswith("\\)") or stripped.endswith("</s>"):
        return True
    return False


def surface_stats(prediction: str, reference: str) -> dict[str, Any]:
    pred_tokens = tokenize(prediction)
    pred_chars = len(prediction or "")
    ref_chars = len(reference or "")
    line_repeat_max = repeated_line_count(prediction)
    ngram_repeat = duplicate_ngram_ratio(pred_tokens)
    length_ratio = pred_chars / ref_chars if ref_chars else None
    return {
        "prediction_chars": pred_chars,
        "reference_chars": ref_chars,
        "prediction_tokens": len(pred_tokens),
        "length_ratio": length_ratio,
        "unigram_f1": unigram_f1(prediction, reference),
        "duplicate_8gram_ratio": ngram_repeat,
        "max_repeated_line_count": line_repeat_max,
        "empty": not bool((prediction or "").strip()),
        "too_short": ref_chars > 0 and pred_chars < 0.5 * ref_chars,
        "too_long": ref_chars > 0 and pred_chars > 2.0 * ref_chars,
        "repetition_suspect": line_repeat_max >= 3 or ngram_repeat >= 0.18,
        "truncation_suspect": pred_chars >= 3000 and not looks_complete(prediction),
    }


def pct(value: float) -> str:
    return f"{value * 100:.2f}"


def fmt_float(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    return f"{float(value):.{digits}f}"


def safe_mean(values: list[float]) -> float | None:
    return mean(values) if values else None


def load_predictions(output_root: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    predictions: dict[str, list[dict[str, Any]]] = {}
    lf_metrics: dict[str, dict[str, Any]] = {}
    for model_name, run_dir in MODEL_RUNS:
        out_dir = output_root / run_dir
        pred_path = out_dir / "generated_predictions.jsonl"
        result_path = out_dir / "predict_results.json"
        if not pred_path.exists():
            raise FileNotFoundError(f"Missing prediction file: {pred_path}")
        if not result_path.exists():
            raise FileNotFoundError(f"Missing predict metrics file: {result_path}")
        predictions[model_name] = read_jsonl(pred_path)
        lf_metrics[model_name] = json.loads(result_path.read_text(encoding="utf-8-sig"))
    return predictions, lf_metrics


def validate_alignment(eval_records: list[dict[str, Any]], predictions: dict[str, list[dict[str, Any]]]) -> None:
    expected = len(eval_records)
    for model_name, rows in predictions.items():
        if len(rows) != expected:
            raise ValueError(f"{model_name} has {len(rows)} predictions, expected {expected}")
        mismatches = 0
        for eval_record, pred_record in zip(eval_records, rows):
            ref = str(eval_record.get("reference_output", ""))
            label = str(pred_record.get("label", ""))
            if ref.strip() != label.strip():
                mismatches += 1
        if mismatches:
            raise ValueError(f"{model_name} has {mismatches} label alignment mismatch(es)")


def summarize_model(
    model_name: str,
    joined: list[dict[str, Any]],
    lf_metrics: dict[str, Any],
) -> dict[str, Any]:
    model_rows = [record["predictions"][model_name]["stats"] for record in joined]
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in joined:
        by_source[str(record["source"])].append(record["predictions"][model_name]["stats"])

    def count_flag(flag: str, rows: list[dict[str, Any]]) -> int:
        return sum(1 for row in rows if row.get(flag))

    summary = {
        "llamafactory": lf_metrics,
        "samples": len(model_rows),
        "avg_unigram_f1": safe_mean([row["unigram_f1"] for row in model_rows]),
        "median_unigram_f1": median(row["unigram_f1"] for row in model_rows),
        "avg_prediction_chars": safe_mean([row["prediction_chars"] for row in model_rows]),
        "median_prediction_chars": median(row["prediction_chars"] for row in model_rows),
        "avg_length_ratio": safe_mean(
            [row["length_ratio"] for row in model_rows if row["length_ratio"] is not None]
        ),
        "empty": count_flag("empty", model_rows),
        "too_short": count_flag("too_short", model_rows),
        "too_long": count_flag("too_long", model_rows),
        "repetition_suspect": count_flag("repetition_suspect", model_rows),
        "truncation_suspect": count_flag("truncation_suspect", model_rows),
        "by_source": {},
    }
    for source, rows in sorted(by_source.items()):
        summary["by_source"][source] = {
            "samples": len(rows),
            "avg_unigram_f1": safe_mean([row["unigram_f1"] for row in rows]),
            "avg_prediction_chars": safe_mean([row["prediction_chars"] for row in rows]),
            "avg_length_ratio": safe_mean(
                [row["length_ratio"] for row in rows if row["length_ratio"] is not None]
            ),
            "repetition_suspect": count_flag("repetition_suspect", rows),
            "truncation_suspect": count_flag("truncation_suspect", rows),
        }
    return summary


def compare_against_baseline(joined: list[dict[str, Any]], baseline: str = "unfiltered") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for model_name, _ in MODEL_RUNS:
        if model_name == baseline:
            continue
        deltas: list[float] = []
        wins = losses = ties = 0
        for record in joined:
            base_f1 = record["predictions"][baseline]["stats"]["unigram_f1"]
            model_f1 = record["predictions"][model_name]["stats"]["unigram_f1"]
            delta = model_f1 - base_f1
            deltas.append(delta)
            if delta > 0.01:
                wins += 1
            elif delta < -0.01:
                losses += 1
            else:
                ties += 1
        out[model_name] = {
            "avg_unigram_f1_delta": safe_mean(deltas),
            "wins": wins,
            "losses": losses,
            "ties": ties,
        }
    return out


def openmath_boxed_accuracy(joined: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    per_model = {
        model_name: {"extracted": 0, "correct": 0, "total": 0}
        for model_name, _ in MODEL_RUNS
    }

    for record in joined:
        if record.get("source") != "openmath_reasoning":
            continue
        ref_boxed = extract_boxed(str(record.get("reference_output", "")))
        if ref_boxed is None:
            continue
        rows.append(record)
        for model_name, _ in MODEL_RUNS:
            prediction = record["predictions"][model_name]["predict"]
            pred_boxed = extract_boxed(prediction)
            per_model[model_name]["total"] += 1
            if pred_boxed is not None:
                per_model[model_name]["extracted"] += 1
            if math_answers_match(ref_boxed, pred_boxed):
                per_model[model_name]["correct"] += 1

    return {
        "n_math": len(rows),
        "per_model": {
            model_name: {
                **counts,
                "accuracy": counts["correct"] / counts["total"] if counts["total"] else None,
                "extract_rate": counts["extracted"] / counts["total"] if counts["total"] else None,
            }
            for model_name, counts in per_model.items()
        },
    }


def build_joined_records(
    eval_records: list[dict[str, Any]],
    predictions: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    joined: list[dict[str, Any]] = []
    for index, eval_record in enumerate(eval_records):
        reference = str(eval_record.get("reference_output", ""))
        row = {
            "phase_e_eval_id": eval_record.get("phase_e_eval_id"),
            "id": eval_record.get("id"),
            "source": eval_record.get("source"),
            "language": eval_record.get("language"),
            "task_type": eval_record.get("task_type"),
            "instruction": eval_record.get("instruction", ""),
            "input": eval_record.get("input", ""),
            "reference_output": reference,
            "reference_chars": len(reference),
            "predictions": {},
        }
        for model_name, _ in MODEL_RUNS:
            prediction = str(predictions[model_name][index].get("predict", ""))
            row["predictions"][model_name] = {
                "predict": prediction,
                "stats": surface_stats(prediction, reference),
            }
        f1_values = [
            row["predictions"][model_name]["stats"]["unigram_f1"]
            for model_name, _ in MODEL_RUNS
        ]
        row["f1_spread"] = max(f1_values) - min(f1_values)
        joined.append(row)
    return joined


def build_review_queue(joined: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for record in joined:
        flags: list[str] = []
        for model_name, _ in MODEL_RUNS:
            stats = record["predictions"][model_name]["stats"]
            if stats["repetition_suspect"]:
                flags.append(f"{model_name}:repetition")
            if stats["truncation_suspect"]:
                flags.append(f"{model_name}:truncation")
            if stats["too_short"]:
                flags.append(f"{model_name}:too_short")
            if stats["too_long"]:
                flags.append(f"{model_name}:too_long")
        if record["f1_spread"] >= 0.08:
            flags.append("large_metric_spread")
        if not flags:
            continue
        compact = {
            "phase_e_eval_id": record["phase_e_eval_id"],
            "id": record["id"],
            "source": record["source"],
            "task_type": record["task_type"],
            "flags": flags,
            "f1_spread": record["f1_spread"],
            "instruction": record["instruction"],
            "reference_output": record["reference_output"],
            "model_stats": {
                model_name: record["predictions"][model_name]["stats"]
                for model_name, _ in MODEL_RUNS
            },
            "predictions": {
                model_name: record["predictions"][model_name]["predict"]
                for model_name, _ in MODEL_RUNS
            },
        }
        queue.append(compact)
    queue.sort(
        key=lambda item: (
            len(item["flags"]),
            item["f1_spread"],
            max(stats["prediction_chars"] for stats in item["model_stats"].values()),
        ),
        reverse=True,
    )
    return queue[:limit]


def md_table(headers: list[str], rows: list[list[Any]], aligns: list[str] | None = None) -> list[str]:
    if aligns is None:
        aligns = ["---"] + ["---:" for _ in headers[1:]]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(aligns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return lines


def write_report(
    path: Path,
    metrics: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    model_rows: list[list[Any]] = []
    for model_name, _ in MODEL_RUNS:
        summary = metrics["models"][model_name]
        lf = summary["llamafactory"]
        model_rows.append(
            [
                model_name,
                fmt_float(lf.get("predict_bleu-4"), 2),
                fmt_float(lf.get("predict_rouge-1"), 2),
                fmt_float(lf.get("predict_rouge-2"), 2),
                fmt_float(lf.get("predict_rouge-l"), 2),
                fmt_float(summary["avg_unigram_f1"], 3),
                fmt_float(summary["avg_length_ratio"], 2),
                int(round(summary["avg_prediction_chars"] or 0)),
                summary["repetition_suspect"],
                summary["truncation_suspect"],
                f"{float(lf.get('predict_runtime', 0)) / 60:.1f}m",
            ]
        )

    source_rows: list[list[Any]] = []
    for source in metrics["sources"]:
        for model_name, _ in MODEL_RUNS:
            source_summary = metrics["models"][model_name]["by_source"][source]
            source_rows.append(
                [
                    source,
                    model_name,
                    source_summary["samples"],
                    fmt_float(source_summary["avg_unigram_f1"], 3),
                    fmt_float(source_summary["avg_length_ratio"], 2),
                    int(round(source_summary["avg_prediction_chars"] or 0)),
                    source_summary["repetition_suspect"],
                    source_summary["truncation_suspect"],
                ]
            )

    delta_rows: list[list[Any]] = []
    for model_name, values in metrics["vs_unfiltered"].items():
        delta_rows.append(
            [
                model_name,
                fmt_float(values["avg_unigram_f1_delta"], 4),
                values["wins"],
                values["losses"],
                values["ties"],
            ]
        )

    math_rows: list[list[Any]] = []
    math_metrics = metrics["openmath_boxed_accuracy"]
    for model_name, _ in MODEL_RUNS:
        values = math_metrics["per_model"][model_name]
        math_rows.append(
            [
                model_name,
                values["extracted"],
                values["correct"],
                values["total"],
                fmt_float(values["accuracy"], 3),
                fmt_float(values["extract_rate"], 3),
            ]
        )

    best_bleu = max(MODEL_RUNS, key=lambda pair: metrics["models"][pair[0]]["llamafactory"]["predict_bleu-4"])[0]
    best_rouge_l = max(MODEL_RUNS, key=lambda pair: metrics["models"][pair[0]]["llamafactory"]["predict_rouge-l"])[0]
    best_f1 = max(MODEL_RUNS, key=lambda pair: metrics["models"][pair[0]]["avg_unigram_f1"])[0]
    best_math = max(
        MODEL_RUNS,
        key=lambda pair: metrics["openmath_boxed_accuracy"]["per_model"][pair[0]]["accuracy"] or 0.0,
    )[0]

    lines = [
        "# Phase E Downstream Prediction Comparison",
        "",
        "Generated by `scripts/30_compare_phase_e_downstream_predictions.py`.",
        "",
        "## Scope",
        "",
        f"- Eval sample: `{rel(args.eval_sample)}`",
        f"- Total prompts: {metrics['total_samples']}",
        f"- Side-by-side JSONL: `{rel(args.comparison_jsonl)}`",
        f"- Review queue JSONL: `{rel(args.review_jsonl)}`",
        "",
        "## Important Caveat",
        "",
        "These numbers are reference-overlap and surface-quality proxies. They can catch broad regressions, verbosity drift, repeated text, and truncation, but they do not prove factual or mathematical correctness.",
        "",
        "## Overall Metrics",
        "",
        *md_table(
            [
                "Model",
                "BLEU-4",
                "ROUGE-1",
                "ROUGE-2",
                "ROUGE-L",
                "Token F1",
                "Len ratio",
                "Avg chars",
                "Rep?",
                "Trunc?",
                "Runtime",
            ],
            model_rows,
            ["---", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:"],
        ),
        "",
        "## Source Breakdown",
        "",
        *md_table(
            ["Source", "Model", "N", "Token F1", "Len ratio", "Avg chars", "Rep?", "Trunc?"],
            source_rows,
            ["---", "---", "---:", "---:", "---:", "---:", "---:", "---:"],
        ),
        "",
        "## Versus Unfiltered",
        "",
        *md_table(
            ["Model", "Avg F1 delta", "Wins", "Losses", "Ties"],
            delta_rows,
            ["---", "---:", "---:", "---:", "---:"],
        ),
        "",
        "## OpenMath Boxed Accuracy",
        "",
        f"Records with reference `\\boxed{{}}`: {math_metrics['n_math']}",
        "",
        *md_table(
            ["Model", "Extracted", "Correct", "Total", "Accuracy", "Extract rate"],
            math_rows,
            ["---", "---:", "---:", "---:", "---:", "---:"],
        ),
        "",
        "## Readout",
        "",
        f"- Best BLEU-4 proxy: `{best_bleu}`.",
        f"- Best ROUGE-L proxy: `{best_rouge_l}`.",
        f"- Best simple token-F1 proxy: `{best_f1}`.",
        f"- Best openmath `\\boxed{{}}` exact match: `{best_math}`.",
        f"- Review queue size: {metrics['review_queue_size']} records.",
        "",
        "Current proxy read: use the reference-overlap numbers for triage only. The Phase E decision should be made by teacher pairwise ranking and task-specific objective checks. The openmath `\\boxed{}` table is the objective signal available without a teacher call.",
        "",
        "Recommended next step: manually or teacher-judge review the review queue, especially math/openmath cases and any repeated or truncated generations.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    eval_records = read_jsonl(args.eval_sample)
    predictions, lf_metrics = load_predictions(args.output_root)
    validate_alignment(eval_records, predictions)

    joined = build_joined_records(eval_records, predictions)
    review_queue = build_review_queue(joined, args.review_limit)
    sources = sorted({str(record.get("source")) for record in eval_records})
    metrics = {
        "total_samples": len(eval_records),
        "models": {
            model_name: summarize_model(model_name, joined, lf_metrics[model_name])
            for model_name, _ in MODEL_RUNS
        },
        "vs_unfiltered": compare_against_baseline(joined),
        "openmath_boxed_accuracy": openmath_boxed_accuracy(joined),
        "sources": sources,
        "outputs": {
            "metrics_json": rel(args.metrics_json),
            "comparison_jsonl": rel(args.comparison_jsonl),
            "review_jsonl": rel(args.review_jsonl),
            "report_md": rel(args.report_md),
        },
        "review_queue_size": len(review_queue),
    }

    write_json(args.metrics_json, metrics)
    write_jsonl(args.comparison_jsonl, joined)
    write_jsonl(args.review_jsonl, review_queue)
    write_report(args.report_md, metrics, args)

    print(f"Wrote {rel(args.metrics_json)}")
    print(f"Wrote {rel(args.comparison_jsonl)}")
    print(f"Wrote {rel(args.review_jsonl)}")
    print(f"Wrote {rel(args.report_md)}")


if __name__ == "__main__":
    main()
