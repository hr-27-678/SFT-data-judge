"""Aggregate pairwise teacher labels into per-model win rates and a markdown report.

Reads:  data/eval/phase_e_downstream_eval/phase_e_downstream_pairwise_labels_5model.jsonl
        data/eval/phase_e_downstream_eval/phase_e_downstream_prediction_comparison.jsonl
Writes: data/eval/phase_e_downstream_eval/phase_e_downstream_pairwise_5model_metrics.json
        reports/phase_e_downstream_pairwise_5model_report.md

Additionally, for openmath_reasoning, extracts \\boxed{...} answers from each
model's prediction and compares against the reference, producing an objective
math accuracy alongside the teacher-judge results.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LABELS = PROJECT_ROOT / "data" / "eval" / "phase_e_downstream_eval" / "phase_e_downstream_pairwise_labels_5model.jsonl"
DEFAULT_COMPARISON = PROJECT_ROOT / "data" / "eval" / "phase_e_downstream_eval" / "phase_e_downstream_prediction_comparison.jsonl"
DEFAULT_METRICS = PROJECT_ROOT / "data" / "eval" / "phase_e_downstream_eval" / "phase_e_downstream_pairwise_5model_metrics.json"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "phase_e_downstream_pairwise_5model_report.md"

MODELS = ["unfiltered", "v4_conservative_keep", "v4_confident_keep", "v4_both_keep", "v4_persource_keep"]
LETTERS = ["A", "B", "C", "D", "E"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    p.add_argument("--comparison", type=Path, default=DEFAULT_COMPARISON)
    p.add_argument("--metrics-output", type=Path, default=DEFAULT_METRICS)
    p.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    return p.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


# --- math answer extraction ------------------------------------------------

BOXED_RE = re.compile(r"\\boxed\s*\{")


def extract_boxed(text: str) -> str | None:
    """Return the content of the LAST \\boxed{...} in text, handling nested braces."""
    if not text:
        return None
    last = None
    for m in BOXED_RE.finditer(text):
        i = m.end()
        depth = 1
        buf = []
        while i < len(text) and depth > 0:
            ch = text[i]
            if ch == "{":
                depth += 1
                buf.append(ch)
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
                buf.append(ch)
            else:
                buf.append(ch)
            i += 1
        if depth == 0:
            last = "".join(buf)
    return last


_NORMALIZE_PATTERNS = [
    (re.compile(r"\\!"), ""),
    (re.compile(r"\\,"), ""),
    (re.compile(r"\\;"), ""),
    (re.compile(r"\\:"), ""),
    (re.compile(r"\\ "), ""),
    (re.compile(r"\\left"), ""),
    (re.compile(r"\\right"), ""),
    (re.compile(r"\\text\s*\{[^}]*\}"), ""),
    (re.compile(r"\\mathrm\s*\{([^}]*)\}"), r"\1"),
    (re.compile(r"\s+"), ""),
]


def normalize_math(s: str) -> str:
    if s is None:
        return ""
    s = s.strip()
    for pat, repl in _NORMALIZE_PATTERNS:
        s = pat.sub(repl, s)
    return s.lower()


def math_answers_match(a: str | None, b: str | None) -> bool:
    if a is None or b is None:
        return False
    return normalize_math(a) == normalize_math(b) and normalize_math(a) != ""


# --- aggregation -----------------------------------------------------------

def aggregate(labels: list[dict[str, Any]], comparison_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    valid_labels = [r for r in labels if r.get("teacher_label") and not r.get("validation_errors")]

    rank_sums: dict[str, list[int]] = defaultdict(list)
    correctness_counts: dict[str, Counter] = defaultdict(Counter)
    first_place: Counter = Counter()
    last_place: Counter = Counter()
    pairwise_wins: dict[tuple[str, str], int] = defaultdict(int)
    pairwise_ties: dict[tuple[str, str], int] = defaultdict(int)
    by_source_rank: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))

    for r in valid_labels:
        label = r["teacher_label"]
        l2m = r["letter_to_model"]
        ranking = label["ranking"]
        correctness = label.get("correctness", {})
        source = r.get("source", "unknown")

        for pos, letter in enumerate(ranking, start=1):
            model = l2m[letter]
            rank_sums[model].append(pos)
            by_source_rank[source][model].append(pos)

        first_place[l2m[ranking[0]]] += 1
        last_place[l2m[ranking[-1]]] += 1

        for letter, verdict in correctness.items():
            model = l2m.get(letter)
            if model:
                correctness_counts[model][verdict] += 1

        for i in range(len(ranking)):
            for j in range(i + 1, len(ranking)):
                wi = l2m[ranking[i]]
                wj = l2m[ranking[j]]
                pairwise_wins[(wi, wj)] += 1

    n = len(valid_labels)

    per_model: dict[str, dict[str, Any]] = {}
    for m in MODELS:
        ranks = rank_sums.get(m, [])
        cc = correctness_counts.get(m, Counter())
        total_cc = sum(cc.values()) or 1
        per_model[m] = {
            "n_judged": len(ranks),
            "avg_rank": round(statistics.mean(ranks), 3) if ranks else None,
            "first_place": first_place.get(m, 0),
            "last_place": last_place.get(m, 0),
            "first_place_rate": round(first_place.get(m, 0) / n, 3) if n else None,
            "correctness_counts": dict(cc),
            "correctness_rate": round(cc.get("correct", 0) / total_cc, 3),
            "wrong_rate": round(cc.get("wrong", 0) / total_cc, 3),
        }

    pairwise_matrix: dict[str, dict[str, dict[str, Any]]] = {}
    for a in MODELS:
        pairwise_matrix[a] = {}
        for b in MODELS:
            if a == b:
                continue
            wins = pairwise_wins.get((a, b), 0)
            losses = pairwise_wins.get((b, a), 0)
            total = wins + losses
            pairwise_matrix[a][b] = {
                "wins": wins,
                "losses": losses,
                "win_rate": round(wins / total, 3) if total else None,
            }

    versus_unfiltered = {}
    for m in MODELS:
        if m == "unfiltered":
            continue
        wins = pairwise_wins.get((m, "unfiltered"), 0)
        losses = pairwise_wins.get(("unfiltered", m), 0)
        total = wins + losses
        versus_unfiltered[m] = {
            "wins": wins,
            "losses": losses,
            "win_rate_vs_unfiltered": round(wins / total, 3) if total else None,
        }

    by_source = {}
    for source, ranks_by_model in by_source_rank.items():
        by_source[source] = {
            m: {
                "n": len(ranks),
                "avg_rank": round(statistics.mean(ranks), 3) if ranks else None,
            }
            for m, ranks in ranks_by_model.items()
        }

    return {
        "n_total_labels": len(labels),
        "n_valid_labels": n,
        "per_model": per_model,
        "pairwise_matrix": pairwise_matrix,
        "versus_unfiltered": versus_unfiltered,
        "by_source": by_source,
    }


def math_accuracy(labels: list[dict[str, Any]], comparison_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    per_model_correct: dict[str, int] = defaultdict(int)
    per_model_extracted: dict[str, int] = defaultdict(int)
    per_model_total: dict[str, int] = defaultdict(int)
    examples: list[dict[str, Any]] = []

    label_ids = {str(r.get("phase_e_eval_id")) for r in labels}

    for eval_id, comp in comparison_by_id.items():
        if comp.get("source") != "openmath_reasoning":
            continue
        ref = comp.get("reference_output", "")
        ref_boxed = extract_boxed(ref)
        if ref_boxed is None:
            continue

        record_in_set = eval_id in label_ids
        if not record_in_set:
            continue

        per_example = {"phase_e_eval_id": eval_id, "ref": ref_boxed, "models": {}}
        for m in MODELS:
            pred = (comp.get("predictions", {}).get(m) or {}).get("predict", "")
            extracted = extract_boxed(pred)
            per_model_total[m] += 1
            if extracted is not None:
                per_model_extracted[m] += 1
            ok = math_answers_match(ref_boxed, extracted)
            if ok:
                per_model_correct[m] += 1
            per_example["models"][m] = {
                "extracted": extracted,
                "match": ok,
            }
        examples.append(per_example)

    return {
        "n_math": len(examples),
        "per_model": {
            m: {
                "extracted": per_model_extracted.get(m, 0),
                "correct": per_model_correct.get(m, 0),
                "total": per_model_total.get(m, 0),
                "accuracy": round(per_model_correct.get(m, 0) / per_model_total.get(m, 1), 3) if per_model_total.get(m) else None,
                "extract_rate": round(per_model_extracted.get(m, 0) / per_model_total.get(m, 1), 3) if per_model_total.get(m) else None,
            }
            for m in MODELS
        },
    }


def write_report(metrics: dict[str, Any], math: dict[str, Any], report_path: Path) -> None:
    lines: list[str] = []
    lines.append("# Phase E Downstream Pairwise Teacher Judge\n")
    lines.append(f"Total labels: {metrics['n_total_labels']} (valid: {metrics['n_valid_labels']})\n")
    lines.append("## Per-Model Aggregate\n")
    lines.append("| Model | N | Avg rank ↓ | 1st place | Last place | 1st rate | Correct rate | Wrong rate |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for m in MODELS:
        d = metrics["per_model"].get(m, {})
        lines.append(
            f"| {m} | {d.get('n_judged','-')} | {d.get('avg_rank','-')} | "
            f"{d.get('first_place','-')} | {d.get('last_place','-')} | "
            f"{d.get('first_place_rate','-')} | {d.get('correctness_rate','-')} | {d.get('wrong_rate','-')} |"
        )
    lines.append("")
    lines.append("Avg rank is lower-is-better (1 = best). 1st rate = fraction of prompts where this model placed first.\n")

    lines.append("## Versus Unfiltered\n")
    lines.append("| Model | Wins | Losses | Win rate vs unfiltered |")
    lines.append("| --- | ---: | ---: | ---: |")
    for m, d in metrics["versus_unfiltered"].items():
        lines.append(f"| {m} | {d['wins']} | {d['losses']} | {d['win_rate_vs_unfiltered']} |")
    lines.append("")

    lines.append("## Pairwise Win Rates (row beats column)\n")
    header = "| | " + " | ".join(MODELS) + " |"
    sep = "| --- | " + " | ".join(["---:"] * len(MODELS)) + " |"
    lines.append(header)
    lines.append(sep)
    for a in MODELS:
        row = [a]
        for b in MODELS:
            if a == b:
                row.append("—")
            else:
                d = metrics["pairwise_matrix"][a][b]
                row.append(f"{d['win_rate']} ({d['wins']}/{d['wins']+d['losses']})" if d['win_rate'] is not None else "-")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    lines.append("## By Source (Avg Rank)\n")
    for source, d in metrics["by_source"].items():
        lines.append(f"### {source}\n")
        lines.append("| Model | N | Avg rank |")
        lines.append("| --- | ---: | ---: |")
        for m in MODELS:
            md = d.get(m, {})
            lines.append(f"| {m} | {md.get('n','-')} | {md.get('avg_rank','-')} |")
        lines.append("")

    lines.append("## Math Accuracy (openmath_reasoning, \\boxed{} match)\n")
    lines.append(f"Records with reference \\boxed{{}}: {math['n_math']}\n")
    lines.append("| Model | Correct | Extracted | Total | Accuracy | Extract rate |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for m in MODELS:
        d = math["per_model"][m]
        lines.append(
            f"| {m} | {d['correct']} | {d['extracted']} | {d['total']} | {d['accuracy']} | {d['extract_rate']} |"
        )
    lines.append("")
    lines.append("Math accuracy is an **objective** signal: did the model produce the same final \\boxed{} answer as the reference?\n")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    labels = read_jsonl(args.labels)
    comparison = read_jsonl(args.comparison)
    comparison_by_id = {str(r.get("phase_e_eval_id")): r for r in comparison}

    metrics = aggregate(labels, comparison_by_id)
    math = math_accuracy(labels, comparison_by_id)

    args.metrics_output.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_output.write_text(
        json.dumps({"pairwise": metrics, "math": math}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    write_report(metrics, math, args.report_output)
    print(json.dumps({
        "metrics": str(args.metrics_output),
        "report": str(args.report_output),
        "n_valid_labels": metrics["n_valid_labels"],
        "n_math": math["n_math"],
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
