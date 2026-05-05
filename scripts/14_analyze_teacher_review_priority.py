"""Analyze teacher labels for a scorer-generated priority review queue.

This joins a scorer priority JSONL with all available Teacher Judge labels by
the original sample `id`. It is meant to answer questions such as:

- Are both models' `not_keep` predictions truly bad data?
- Is the conservative scorer over-rejecting examples the teacher would keep?
- Which source/bucket should feed the next scorer training set?
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRIORITY = PROJECT_ROOT / "data" / "scored" / "teacher_candidates_all_v2_teacher_review_priority.jsonl"
DEFAULT_LABEL_FILES = [
    PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "teacher_labels_1000.jsonl",
    PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "targeted_1200_teacher_labels.jsonl",
    PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "v2active001" / "v2active001_teacher_labels.jsonl",
]
DEFAULT_JOINED = PROJECT_ROOT / "data" / "scored" / "teacher_candidates_all_v2_priority_teacher_joined.jsonl"
DEFAULT_METRICS = PROJECT_ROOT / "data" / "scored" / "teacher_candidates_all_v2_priority_teacher_analysis_metrics.json"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "teacher_candidates_all_v2_priority_teacher_analysis_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze teacher labels joined to a scorer priority queue.")
    parser.add_argument("--priority", type=Path, default=DEFAULT_PRIORITY)
    parser.add_argument("--label-file", type=Path, action="append", default=None)
    parser.add_argument("--joined-output", type=Path, default=DEFAULT_JOINED)
    parser.add_argument("--metrics-json", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def sample_id(record: dict[str, Any]) -> str:
    return str(record.get("id") or "")


def validation_errors(record: dict[str, Any]) -> list[str]:
    errors = record.get("validation_errors")
    if isinstance(errors, list):
        return [str(error) for error in errors]
    if errors:
        return [str(errors)]
    return []


def label_status(label_record: dict[str, Any] | None) -> str:
    if label_record is None:
        return "missing"
    if not isinstance(label_record.get("teacher_label"), dict):
        return "null_label"
    if validation_errors(label_record):
        return "validation_error"
    return "labeled"


def teacher_score(label_record: dict[str, Any] | None) -> int | None:
    if label_status(label_record) != "labeled":
        return None
    score = label_record["teacher_label"].get("overall_score")
    return int(score) if isinstance(score, int) else None


def teacher_verdict(label_record: dict[str, Any] | None) -> str:
    if label_status(label_record) != "labeled":
        return label_status(label_record)
    verdict = label_record["teacher_label"].get("verdict")
    return str(verdict) if verdict else "unknown"


def conservative_target(score: int | None) -> str | None:
    if score is None:
        return None
    return "keep" if score >= 4 else "not_keep"


def confident_target(score: int | None) -> str | None:
    if score is None or score == 3:
        return None
    return "keep" if score >= 4 else "not_keep"


def priority_reasons(record: dict[str, Any]) -> list[str]:
    reasons = record.get("priority_reasons")
    if isinstance(reasons, list):
        return [str(reason) for reason in reasons]
    reason = record.get("priority_reason")
    if reason:
        return [str(reason)]
    return []


def load_labels(label_files: list[Path]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    labels: dict[str, dict[str, Any]] = {}
    duplicate_ids: Counter[str] = Counter()
    file_counts: dict[str, int] = {}

    for path in label_files:
        if not path.exists():
            file_counts[str(path)] = 0
            continue

        records = read_jsonl(path)
        file_counts[str(path)] = len(records)
        for record in records:
            key = sample_id(record)
            if not key:
                continue
            if key in labels:
                duplicate_ids[key] += 1
            labels[key] = {**record, "_label_file": str(path)}

    metadata = {
        "label_files": file_counts,
        "duplicate_label_ids": sum(duplicate_ids.values()),
        "duplicate_label_id_examples": duplicate_ids.most_common(10),
    }
    return labels, metadata


def build_joined(priority_records: list[dict[str, Any]], labels: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    joined: list[dict[str, Any]] = []
    for record in priority_records:
        label_record = labels.get(sample_id(record))
        score = teacher_score(label_record)
        verdict = teacher_verdict(label_record)
        status = label_status(label_record)
        cons_target = conservative_target(score)
        conf_target = confident_target(score)
        cons_pred = record.get("conservative_verdict")
        conf_pred = record.get("confident_verdict")

        joined.append(
            {
                **record,
                "priority_reasons": priority_reasons(record),
                "teacher_label_status": status,
                "teacher_score": score,
                "teacher_verdict": verdict,
                "teacher_label": label_record.get("teacher_label") if label_record else None,
                "teacher_label_file": label_record.get("_label_file") if label_record else None,
                "teacher_validation_errors": validation_errors(label_record) if label_record else [],
                "conservative_teacher_target": cons_target,
                "confident_teacher_target": conf_target,
                "conservative_matches_teacher_policy": bool(cons_target and cons_pred == cons_target),
                "confident_matches_teacher_policy": bool(conf_target and conf_pred == conf_target),
                "is_teacher_keep": verdict == "keep",
                "is_teacher_maybe": verdict == "maybe",
                "is_teacher_drop": verdict == "drop",
                "conservative_false_reject_keep": cons_pred == "not_keep" and verdict == "keep",
                "conservative_missed_drop": cons_pred == "keep" and verdict == "drop",
                "conservative_missed_not_keep_policy": cons_pred == "keep" and score is not None and score <= 3,
                "confident_false_reject_keep": conf_pred == "not_keep" and verdict == "keep",
                "confident_missed_drop": conf_pred == "keep" and verdict == "drop",
            }
        )
    return joined


def count_by(records: list[dict[str, Any]], key: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for record in records:
        value = record.get(key)
        counter[str(value) if value not in (None, "") else "unknown"] += 1
    return counter


def cross_count(records: list[dict[str, Any]], key_a: str, key_b: str) -> dict[str, Counter[str]]:
    result: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        a = str(record.get(key_a) or "unknown")
        b = str(record.get(key_b) or "unknown")
        result[a][b] += 1
    return result


def reason_count(records: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for record in records:
        for reason in priority_reasons(record):
            counter[reason] += 1
    return counter


def reason_cross_verdict(records: list[dict[str, Any]]) -> dict[str, Counter[str]]:
    result: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        for reason in priority_reasons(record):
            result[reason][str(record.get("teacher_verdict") or "unknown")] += 1
    return result


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{100 * numerator / denominator:.1f}%"


def bucket_rows(records: list[dict[str, Any]]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    by_bucket = cross_count(records, "agreement_bucket", "teacher_verdict")
    for bucket, counts in sorted(by_bucket.items()):
        total = sum(counts.values())
        drop = counts.get("drop", 0)
        maybe = counts.get("maybe", 0)
        keep = counts.get("keep", 0)
        missing = total - drop - maybe - keep
        rows.append(
            [
                f"`{bucket}`",
                total,
                keep,
                maybe,
                drop,
                missing,
                pct(drop, total),
                pct(drop + maybe, total),
            ]
        )
    return rows


def source_rows(records: list[dict[str, Any]]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    by_source = cross_count(records, "source", "teacher_verdict")
    for source, counts in sorted(by_source.items()):
        total = sum(counts.values())
        rows.append(
            [
                f"`{source}`",
                total,
                counts.get("keep", 0),
                counts.get("maybe", 0),
                counts.get("drop", 0),
                total - counts.get("keep", 0) - counts.get("maybe", 0) - counts.get("drop", 0),
                pct(counts.get("drop", 0), total),
            ]
        )
    return rows


def reason_rows(records: list[dict[str, Any]]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    by_reason = reason_cross_verdict(records)
    for reason, counts in sorted(by_reason.items()):
        total = sum(counts.values())
        rows.append(
            [
                f"`{reason}`",
                total,
                counts.get("keep", 0),
                counts.get("maybe", 0),
                counts.get("drop", 0),
                total - counts.get("keep", 0) - counts.get("maybe", 0) - counts.get("drop", 0),
                pct(counts.get("drop", 0), total),
            ]
        )
    return rows


def model_policy_summary(records: list[dict[str, Any]], model_name: str) -> dict[str, Any]:
    if model_name == "conservative":
        target_key = "conservative_teacher_target"
        match_key = "conservative_matches_teacher_policy"
        pred_key = "conservative_verdict"
    elif model_name == "confident":
        target_key = "confident_teacher_target"
        match_key = "confident_matches_teacher_policy"
        pred_key = "confident_verdict"
    else:
        raise ValueError(model_name)

    scoped = [record for record in records if record.get(target_key)]
    correct = sum(1 for record in scoped if record.get(match_key))
    confusion = cross_count(scoped, target_key, pred_key)
    return {
        "records": len(scoped),
        "correct": correct,
        "accuracy": round(correct / len(scoped), 6) if scoped else None,
        "confusion": {target: dict(counts) for target, counts in confusion.items()},
    }


def build_metrics(joined: list[dict[str, Any]], label_metadata: dict[str, Any]) -> dict[str, Any]:
    labeled = [record for record in joined if record.get("teacher_label_status") == "labeled"]
    return {
        "records": len(joined),
        "labeled_records": len(labeled),
        "missing_or_invalid_records": len(joined) - len(labeled),
        "label_status_counts": dict(count_by(joined, "teacher_label_status")),
        "teacher_verdict_counts": dict(count_by(joined, "teacher_verdict")),
        "teacher_score_counts": dict(count_by(joined, "teacher_score")),
        "agreement_bucket_counts": dict(count_by(joined, "agreement_bucket")),
        "agreement_bucket_by_teacher_verdict": {key: dict(value) for key, value in cross_count(joined, "agreement_bucket", "teacher_verdict").items()},
        "source_by_teacher_verdict": {key: dict(value) for key, value in cross_count(joined, "source", "teacher_verdict").items()},
        "priority_reason_counts": dict(reason_count(joined)),
        "priority_reason_by_teacher_verdict": {key: dict(value) for key, value in reason_cross_verdict(joined).items()},
        "conservative_policy": model_policy_summary(joined, "conservative"),
        "confident_policy": model_policy_summary(joined, "confident"),
        "critical_error_counts": {
            "conservative_false_reject_keep": sum(1 for record in joined if record.get("conservative_false_reject_keep")),
            "conservative_missed_drop": sum(1 for record in joined if record.get("conservative_missed_drop")),
            "conservative_missed_not_keep_policy": sum(1 for record in joined if record.get("conservative_missed_not_keep_policy")),
            "confident_false_reject_keep": sum(1 for record in joined if record.get("confident_false_reject_keep")),
            "confident_missed_drop": sum(1 for record in joined if record.get("confident_missed_drop")),
        },
        "label_metadata": label_metadata,
    }


def write_report(path: Path, joined: list[dict[str, Any]], metrics: dict[str, Any], args: argparse.Namespace) -> None:
    labeled = [record for record in joined if record.get("teacher_label_status") == "labeled"]
    missing = [record for record in joined if record.get("teacher_label_status") != "labeled"]

    cons = metrics["conservative_policy"]
    conf = metrics["confident_policy"]
    critical = metrics["critical_error_counts"]
    if missing:
        recommended_next_actions = [
            "1. Retry missing/invalid teacher labels, then rerun this report.",
            "2. Build v3 confident and conservative datasets using starter, targeted, and `v2active001` labels.",
            "3. Add a small calibration slice from teacher-keep false rejects to avoid over-rejection.",
            "4. Keep evaluating by source, especially `cot_zh` and `finetome`.",
        ]
    else:
        recommended_next_actions = [
            "1. Build v3 confident and conservative datasets using starter, targeted, and `v2active001` labels.",
            "2. Prioritize teacher-confirmed hard negatives from `conf_not_keep__cons_not_keep` and model-disagreement buckets.",
            "3. Add a calibration slice from teacher-keep false rejects so the next scorer does not over-reject.",
            "4. After v3 training, rerun scorer inference on a larger unlabeled pool and create `v2active002` from newly surfaced hard cases.",
        ]

    lines = [
        "# Teacher Priority Queue Analysis Report",
        "",
        "## Report Metadata",
        "",
        markdown_table(
            ["Field", "Value"],
            [
                ["Report type", "Teacher-labeled priority queue analysis"],
                ["Project stage", "V2 active-learning analysis"],
                ["Report status", "Generated"],
            ],
        ),
        "",
        "## Experiment Context",
        "",
        markdown_table(
            ["Field", "Value"],
            [
                ["Priority queue", f"`{args.priority}`"],
                ["Records", len(joined)],
                ["Joined output", f"`{args.joined_output}`"],
                ["Metrics JSON", f"`{args.metrics_json}`"],
                ["Current use", "Decide v3 training mix and hard-case priorities"],
            ],
        ),
        "",
        "## Summary",
        "",
        markdown_table(
            ["Metric", "Count"],
            [
                ["Priority records", len(joined)],
                ["Teacher-labeled records", len(labeled)],
                ["Missing/invalid labels", len(missing)],
                ["Teacher keep", metrics["teacher_verdict_counts"].get("keep", 0)],
                ["Teacher maybe", metrics["teacher_verdict_counts"].get("maybe", 0)],
                ["Teacher drop", metrics["teacher_verdict_counts"].get("drop", 0)],
            ],
        ),
        "",
        "## Agreement Bucket By Teacher Verdict",
        "",
        markdown_table(
            ["Bucket", "Total", "Keep", "Maybe", "Drop", "Missing", "Drop rate", "Quality-first not_keep rate"],
            bucket_rows(joined),
        ),
        "",
        "## Source By Teacher Verdict",
        "",
        markdown_table(["Source", "Total", "Keep", "Maybe", "Drop", "Missing", "Drop rate"], source_rows(joined)),
        "",
        "## Priority Reason By Teacher Verdict",
        "",
        markdown_table(["Reason", "Total", "Keep", "Maybe", "Drop", "Missing", "Drop rate"], reason_rows(joined)),
        "",
        "## Model Policy Checks",
        "",
        markdown_table(
            ["Policy view", "Records", "Correct", "Accuracy"],
            [
                ["Conservative target: score 4/5 keep, 1/2/3 not_keep", cons["records"], cons["correct"], pct(cons["correct"], cons["records"])],
                ["Confident target: score 4/5 keep, 1/2 not_keep, score 3 skipped", conf["records"], conf["correct"], pct(conf["correct"], conf["records"])],
            ],
        ),
        "",
        "## Critical Error Counts",
        "",
        markdown_table(
            ["Error type", "Count", "Meaning"],
            [
                ["`conservative_false_reject_keep`", critical["conservative_false_reject_keep"], "Conservative predicted not_keep but teacher said keep"],
                ["`conservative_missed_drop`", critical["conservative_missed_drop"], "Conservative predicted keep but teacher said drop"],
                ["`conservative_missed_not_keep_policy`", critical["conservative_missed_not_keep_policy"], "Conservative predicted keep but teacher score was 1/2/3"],
                ["`confident_false_reject_keep`", critical["confident_false_reject_keep"], "Confident predicted not_keep but teacher said keep"],
                ["`confident_missed_drop`", critical["confident_missed_drop"], "Confident predicted keep but teacher said drop"],
            ],
        ),
        "",
        "## Missing Or Invalid Labels",
        "",
    ]

    if missing:
        rows = [
            [
                record.get("teacher_sample_id"),
                record.get("id"),
                record.get("source"),
                record.get("teacher_label_status"),
                "; ".join(record.get("teacher_validation_errors") or []),
            ]
            for record in missing[:20]
        ]
        lines.append(markdown_table(["teacher_sample_id", "id", "source", "status", "errors"], rows))
    else:
        lines.append("All priority records have valid teacher labels.")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Use `drop` rows from `conf_not_keep__cons_not_keep` as the strongest teacher-confirmed hard negatives.",
            "- Use teacher `keep` rows from conservative `not_keep` buckets as false-reject examples so v3 does not become too conservative.",
            "- Use scorer `keep` but teacher `drop` rows as the highest-risk missed-bad-data examples.",
            "- Keep score-3 / `maybe` rows separate in analysis; for conservative v3 they can map to `not_keep`, but they should not be treated as the same thing as severe `drop` examples.",
            "",
            "## Recommended Next Actions",
            "",
            *recommended_next_actions,
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    label_files = args.label_file or DEFAULT_LABEL_FILES
    priority_records = read_jsonl(args.priority)
    labels, label_metadata = load_labels(label_files)
    joined = build_joined(priority_records, labels)
    metrics = build_metrics(joined, label_metadata)

    write_jsonl(args.joined_output, joined)
    write_json(args.metrics_json, metrics)
    write_report(args.report_path, joined, metrics, args)

    print(
        json.dumps(
            {
                "priority_records": len(priority_records),
                "joined_output": str(args.joined_output),
                "metrics_json": str(args.metrics_json),
                "report": str(args.report_path),
                "labeled_records": metrics["labeled_records"],
                "missing_or_invalid_records": metrics["missing_or_invalid_records"],
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
