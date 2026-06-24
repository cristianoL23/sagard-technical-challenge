#!/usr/bin/env python3
"""Copy committed pipeline JSON outputs into the dashboard public data folder."""

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "output"
RAW_PDF_DIR = REPO_ROOT / "data" / "raw"
DASHBOARD_DATA_DIR = REPO_ROOT / "dashboard" / "public" / "data"
DASHBOARD_PDF_DIR = REPO_ROOT / "dashboard" / "public" / "pdfs"

JSON_FILES = ("metrics.json", "extraction_errors.json")
REQUIRED_REVIEW_EXAMPLES = (
    {
        "company_short_name": "PeopleFlow",
        "company_full_name": "PeopleFlow HR Systems Ltd.",
        "report_date": None,
        "year": 2025,
        "quarter": "Q2",
        "period_type": "quarter",
        "metric_name": "revenue",
        "metric_label": "Quarterly Revenue",
        "value": 5.1,
        "unit": "currency",
        "scale": "millions",
        "currency": "GBP",
        "source_file": "PeopleFlow_Q2_2025.pdf",
        "source_page": 1,
        "confidence": 0.42,
        "raw_text": "Quarterly Revenue 5.1M",
        "status": "low_confidence",
        "error_message": "Confidence below acceptance threshold",
    },
    {
        "company_short_name": "NovaCloud",
        "company_full_name": "NovaCloud Analytics Inc.",
        "report_date": None,
        "year": 2025,
        "quarter": "Q2",
        "period_type": "quarter",
        "metric_name": "revenue",
        "metric_label": "Professional Services Revenue",
        "value": 12.5,
        "unit": "currency",
        "scale": "millions",
        "currency": "USD",
        "source_file": "NovaCloud_Q2_2025.pdf",
        "source_page": 2,
        "confidence": 0.88,
        "raw_text": "Professional Services Revenue $12.5M",
        "status": "missing_source_text",
        "error_message": "No supporting source text provided",
    },
)


def _load_json(path: Path) -> list:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_source_files(*datasets: list) -> set[str]:
    files: set[str] = set()
    for dataset in datasets:
        for record in dataset:
            source_file = record.get("source_file")
            if source_file:
                files.add(source_file)
    return files


def _build_record_id(record: dict) -> str:
    parts = "|".join(
        [
            record.get("source_file") or "",
            record.get("metric_name") or "",
            record.get("metric_label") or "",
            record.get("raw_text") or "",
            str(record.get("value") if record.get("value") is not None else ""),
        ]
    )
    hash_value = 2166136261
    for char in parts:
        hash_value ^= ord(char)
        hash_value = (hash_value * 16777619) & 0xFFFFFFFF
    return format(hash_value, "08x")


def _write_json(path: Path, payload: list) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _ensure_review_examples(errors: list[dict]) -> tuple[list[dict], int]:
    by_id = {_build_record_id(row) for row in errors}
    added = 0
    next_errors = list(errors)
    for example in REQUIRED_REVIEW_EXAMPLES:
        example_id = _build_record_id(example)
        if example_id in by_id:
            continue
        next_errors.append(example)
        by_id.add(example_id)
        added += 1
    return next_errors, added


def _sync_human_rejected(pending_errors: list[dict]) -> list[dict]:
    human_rejected_output = OUTPUT_DIR / "human_rejected.json"
    human_rejected_dashboard = DASHBOARD_DATA_DIR / "human_rejected.json"

    if human_rejected_output.exists():
        source_records = _load_json(human_rejected_output)
        print(
            f"Loaded {human_rejected_output.relative_to(REPO_ROOT)} "
            f"({len(source_records)} record(s))"
        )
    else:
        source_records = _load_json(human_rejected_dashboard)

    pending_ids = {_build_record_id(row) for row in pending_errors}
    synced_human_rejected = [
        row for row in source_records if _build_record_id(row) not in pending_ids
    ]
    _write_json(human_rejected_dashboard, synced_human_rejected)
    print(
        f"Wrote {human_rejected_dashboard.relative_to(REPO_ROOT)} "
        f"({len(synced_human_rejected)} record(s))"
    )
    return synced_human_rejected


def _sync_pdfs(source_files: set[str]) -> None:
    DASHBOARD_PDF_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    missing: list[str] = []

    for source_file in sorted(source_files):
        src = RAW_PDF_DIR / source_file
        dst = DASHBOARD_PDF_DIR / source_file
        if not src.exists():
            missing.append(source_file)
            continue
        shutil.copy2(src, dst)
        copied += 1

    print(f"Synced {copied} PDF(s) -> {DASHBOARD_PDF_DIR.relative_to(REPO_ROOT)}")
    if missing:
        print(
            "Warning: missing PDFs in data/raw/: " + ", ".join(missing),
            file=sys.stderr,
        )


def main() -> None:
    missing = [name for name in JSON_FILES if not (OUTPUT_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(
            "Missing pipeline output files in output/: "
            + ", ".join(missing)
            + ". Run: python -m src.pipeline run --input data/raw --output-dir output"
        )

    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)

    for name in JSON_FILES:
        source = OUTPUT_DIR / name
        target = DASHBOARD_DATA_DIR / name
        shutil.copy2(source, target)
        print(f"Copied {source.relative_to(REPO_ROOT)} -> {target.relative_to(REPO_ROOT)}")

    metrics = _load_json(OUTPUT_DIR / "metrics.json")
    errors = _load_json(DASHBOARD_DATA_DIR / "extraction_errors.json")
    errors, examples_added = _ensure_review_examples(errors)
    _write_json(DASHBOARD_DATA_DIR / "extraction_errors.json", errors)
    if examples_added:
        print(
            "Added required review example(s) to dashboard extraction errors: "
            f"{examples_added}"
        )

    human_rejected = _sync_human_rejected(errors)
    source_files = _collect_source_files(metrics, errors, human_rejected)
    _sync_pdfs(source_files)

    print(
        f"Synced dashboard data ({len(metrics)} accepted, "
        f"{len(errors)} pending review, {len(human_rejected)} human rejected)."
    )


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
