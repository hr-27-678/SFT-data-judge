"""Evaluate all current scorer adapters on the 600-record evergreen test set.

Reads the merged evergreen labels (teacher ground truth) and one prediction
JSONL per adapter, joins by `id`, and produces a single markdown report with:

- Conservative GT (600 records, score 3 -> not_keep)
- Confident GT (556 records, score 3 skipped)
- Each GT split into clean stratum (500) and flagged stratum (100)
- Per source breakdown for the clean stratum

Predictions are produced by `scripts/12_infer_binary_scorer.py`. This script
only does the aggregation; it does not load any model.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LABELS_PATH = PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_test_merged_teacher_labels.jsonl"
LOCK_PATH = PROJECT_ROOT / "data" / "eval" / "evergreen_test_ids.json"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "evergreen_cross_version_eval_report.md"
DEFAULT_METRICS = PROJECT_ROOT / "data" / "eval" / "evergreen_cross_version_eval_metrics.json"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--predictions",
        action="append",
        required=True,
        help="Repeatable. Format: <display_name>:<path>. e.g. v3_conservative:data/scored/evergreen_v3_conservative_predictions.jsonl",
    )
    p.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    p.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    p.add_argument(
        "--lf-source-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "labeled" / "evergreen_lf",
        help=(
            "Directory containing the LF-format evergreen source jsonl. "
            "Use data/labeled/evergreen_lf_noflag for prompt-ablation eval, "
            "or data/labeled/evergreen_lf_v2{,_noflag} for evergreen v2."
        ),
    )
    p.add_argument(
        "--candidates",
        type=Path,
        default=PROJECT_ROOT / "data" / "splits" / "teacher_judge" / "evergreen_test_merged_candidates.jsonl",
        help="Merged candidates file (default: evergreen v1 600).",
    )
    p.add_argument(
        "--labels",
        type=Path,
        default=PROJECT_ROOT / "data" / "labeled" / "teacher_judge" / "evergreen_test_merged_teacher_labels.jsonl",
        help="Merged teacher labels file (default: evergreen v1 600).",
    )
    return p.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def fmt_pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x*100:.2f}%"


def fmt_num(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def map_conservative(score: int | None) -> str | None:
    if score in (1, 2, 3):
        return "not_keep"
    if score in (4, 5):
        return "keep"
    return None


def map_confident(score: int | None) -> str | None:
    if score in (1, 2):
        return "not_keep"
    if score in (4, 5):
        return "keep"
    return None  # score 3 -> skipped


def compute_metrics(pairs: list[tuple[str, str]]) -> dict[str, Any]:
    """pairs: list of (gt, pred) where each is keep/not_keep/None.
    None gt means the record is excluded (e.g. score 3 under confident GT).
    Records with None pred (no scorer prediction) count toward total but as wrong.
    """
    valid = [(g, p) for g, p in pairs if g is not None]
    n = len(valid)
    if n == 0:
        return {"n": 0}

    correct = sum(1 for g, p in valid if p == g)
    json_valid = sum(1 for g, p in valid if p in ("keep", "not_keep"))

    def per_class(cls: str) -> dict[str, float]:
        tp = sum(1 for g, p in valid if g == cls and p == cls)
        fp = sum(1 for g, p in valid if g != cls and p == cls)
        fn = sum(1 for g, p in valid if g == cls and p != cls)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}

    return {
        "n": n,
        "accuracy": correct / n,
        "json_valid_rate": json_valid / n,
        "keep": per_class("keep"),
        "not_keep": per_class("not_keep"),
    }


def main() -> None:
    args = parse_args()
    labels = {r["id"]: r for r in read_jsonl(args.labels)}

    # Derive strata directly from candidates (clean = is_clean True, flagged
    # = is_clean False). This is robust against lock-file schema changes and
    # works for any evergreen version. The merged candidates file is the
    # canonical source of which records are in this eval.
    candidates = {r["id"]: r for r in read_jsonl(args.candidates)}
    clean_ids: set[str] = {sid for sid, rec in candidates.items() if rec.get("is_clean")}
    flagged_ids: set[str] = {sid for sid, rec in candidates.items() if not rec.get("is_clean")}

    # Build per-id ground truth scores. Source taken from candidates if
    # missing on the label record (some legacy label files do not carry it).
    score_by_id: dict[str, int] = {}
    source_by_id: dict[str, str] = {}
    for sid in candidates:
        rec = labels.get(sid, {})
        teacher_label = rec.get("teacher_label") or {}
        score_by_id[sid] = teacher_label.get("overall_score")
        source_by_id[sid] = rec.get("source") or candidates[sid].get("source", "")

    # Parse --predictions args. Two supported formats:
    #   1. name:path_to_script12_jsonl (each line has 'id' and 'verdict')
    #   2. name:path_to_llamafactory_generated_predictions.jsonl (each line
    #      has 'predict' but no id; we join by line index against the LF
    #      evergreen dataset that preserves _evergreen_id in source order)
    lf_source_path = args.lf_source_dir / "evergreen_test.jsonl"
    lf_source_ids: list[str] = []
    lf_source_signatures: list[str] = []
    if lf_source_path.exists():
        for r in read_jsonl(lf_source_path):
            sid = r.get("_evergreen_id") or r.get("id")
            if sid:
                lf_source_ids.append(sid)
                # Use a short distinctive substring of the instruction as
                # an order-verification signature.
                instr = (r.get("instruction") or "")
                # take chars 100-300 (skips the boilerplate header that's
                # identical across records, captures the actual content)
                lf_source_signatures.append(instr[100:300])

    def parse_verdict_text(text: str | None) -> str | None:
        if not text:
            return None
        text = text.strip()
        try:
            obj = json.loads(text)
            v = obj.get("verdict") if isinstance(obj, dict) else None
            if v in ("keep", "not_keep"):
                return v
        except Exception:
            pass
        # Permissive substring fallback
        if '"not_keep"' in text:
            return "not_keep"
        if '"keep"' in text:
            return "keep"
        return None

    model_predictions: dict[str, dict[str, str | None]] = {}
    for spec in args.predictions:
        if ":" not in spec:
            raise SystemExit(f"--predictions value must be name:path, got {spec!r}")
        name, path_s = spec.split(":", 1)
        path = Path(path_s)
        preds = read_jsonl(path)
        per_id: dict[str, str | None] = {}

        # Detect LLaMA-Factory format (rows have 'predict' key but no 'id')
        is_lf = bool(preds) and "predict" in preds[0] and "id" not in preds[0]

        if is_lf:
            if not lf_source_ids:
                raise SystemExit(
                    f"LF-format predictions detected for {name} but evergreen_lf source is missing: {lf_source_path}"
                )
            if len(preds) != len(lf_source_ids):
                raise SystemExit(
                    f"LF predictions count {len(preds)} != LF source ids count {len(lf_source_ids)} for {name}"
                )

            # Verify LF preserved input order by spot-checking first / middle
            # / last record signatures. If order is shuffled, this fails.
            sample_indices = [0, len(preds) // 2, len(preds) - 1]
            for idx in sample_indices:
                sig = lf_source_signatures[idx]
                lf_prompt = preds[idx].get("prompt", "")
                if sig and sig not in lf_prompt:
                    raise SystemExit(
                        f"LF predictions appear reordered for {name} at index {idx}: "
                        f"source signature not found in LF prompt. "
                        f"sig[:60]={sig[:60]!r} ; lf_prompt[:120]={lf_prompt[:120]!r}"
                    )

            for sid, r in zip(lf_source_ids, preds):
                per_id[sid] = parse_verdict_text(r.get("predict"))
        else:
            for r in preds:
                sid = r.get("id")
                if not sid:
                    continue
                verdict = r.get("verdict")
                if verdict is None:
                    pred = r.get("prediction") or {}
                    if isinstance(pred, dict):
                        verdict = pred.get("verdict")
                per_id[sid] = verdict if verdict in ("keep", "not_keep") else None

        model_predictions[name] = per_id

    # Compute metrics for each model x GT x stratum
    gt_specs = [
        ("conservative", map_conservative),
        ("confident", map_confident),
    ]
    stratum_specs = [
        ("clean", clean_ids),
        ("flagged", flagged_ids),
    ]

    results: dict[str, dict[str, dict[str, dict[str, Any]]]] = defaultdict(lambda: defaultdict(dict))

    for model_name, preds in model_predictions.items():
        for gt_name, gt_fn in gt_specs:
            for stratum_name, sids in stratum_specs:
                pairs: list[tuple[str | None, str | None]] = []
                for sid in sids:
                    gt = gt_fn(score_by_id.get(sid))
                    pred = preds.get(sid)
                    pairs.append((gt, pred))
                results[model_name][gt_name][stratum_name] = compute_metrics(pairs)

            # per-source clean breakdown
            per_source = {}
            for src in ("cot_zh", "finetome", "openmath_reasoning"):
                src_ids = {sid for sid in clean_ids if source_by_id.get(sid) == src}
                pairs = [(gt_fn(score_by_id.get(sid)), preds.get(sid)) for sid in src_ids]
                per_source[src] = compute_metrics(pairs)
            results[model_name][gt_name]["clean_by_source"] = per_source

    # ------- Render report -------
    def model_row(model_name: str, m: dict[str, Any]) -> list[Any]:
        return [
            model_name,
            m.get("n"),
            fmt_pct(m.get("accuracy")),
            fmt_num(m.get("keep", {}).get("f1")),
            fmt_num(m.get("not_keep", {}).get("f1")),
            fmt_pct(m.get("not_keep", {}).get("recall")),
            fmt_pct(m.get("json_valid_rate")),
        ]

    headers = ["Model", "N", "Accuracy", "Keep F1", "Not-keep F1", "Not-keep recall", "JSON valid"]
    lines = [
        "# Evergreen v1 Cross-Version Scorer Comparison",
        "",
        "## Report Metadata",
        "",
        md_table(["Field", "Value"], [
            ["Generated", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Test set", f"`{args.labels.relative_to(PROJECT_ROOT) if args.labels.is_relative_to(PROJECT_ROOT) else args.labels}`"],
            ["Records", f"{len(candidates)} (clean {len(clean_ids)} + flagged {len(flagged_ids)})"],
            ["LF source dir", f"`{args.lf_source_dir.relative_to(PROJECT_ROOT) if args.lf_source_dir.is_relative_to(PROJECT_ROOT) else args.lf_source_dir}`"],
            ["Models compared", ", ".join(model_predictions.keys())],
        ]),
        "",
        "## Ground Truth Mapping",
        "",
        "Two ground-truth mappings are reported. Each scorer was originally trained",
        "with one of these mappings; both are reported here so cross-mapping",
        "comparisons are also possible.",
        "",
        "- **Conservative GT** (600 records): teacher score 1-2-3 -> not_keep, 4-5 -> keep.",
        "- **Confident GT** (556 records): teacher score 1-2 -> not_keep, 4-5 -> keep, score 3 (44 records) skipped.",
        "",
        "## Stratum Definition",
        "",
        "- **Clean stratum** (500 records): cot_zh 300, finetome 125, openmath_reasoning 75.",
        "- **Flagged stratum** (100 records): cot_zh 40, finetome 60. duplicate_pair flag excluded.",
        "",
        "Primary metric: **Not-keep recall**. Higher = scorer correctly rejects more poor samples.",
    ]

    for gt_name, _ in gt_specs:
        lines.append("")
        lines.append(f"## {gt_name.title()} GT")
        for stratum_name, _ in stratum_specs:
            rows = []
            for model_name in model_predictions:
                m = results[model_name][gt_name][stratum_name]
                rows.append(model_row(model_name, m))
            lines.append("")
            lines.append(f"### {gt_name.title()} GT x {stratum_name} stratum")
            lines.append("")
            lines.append(md_table(headers, rows))

        # per-source clean
        lines.append("")
        lines.append(f"### {gt_name.title()} GT x clean stratum, by source")
        for src in ("cot_zh", "finetome", "openmath_reasoning"):
            rows = []
            for model_name in model_predictions:
                m = results[model_name][gt_name]["clean_by_source"][src]
                rows.append(model_row(model_name, m))
            lines.append("")
            lines.append(f"#### source: {src}")
            lines.append("")
            lines.append(md_table(headers, rows))

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")

    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    with args.metrics.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    out_str = str(args.report).encode("ascii", errors="replace").decode("ascii")
    print(f"wrote report: {out_str}")


if __name__ == "__main__":
    main()
