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

    human_rejected_output = OUTPUT_DIR / "human_rejected.json"
    human_rejected_dashboard = DASHBOARD_DATA_DIR / "human_rejected.json"
    if human_rejected_output.exists():
        shutil.copy2(human_rejected_output, human_rejected_dashboard)
        print(
            f"Copied {human_rejected_output.relative_to(REPO_ROOT)} -> "
            f"{human_rejected_dashboard.relative_to(REPO_ROOT)}"
        )
    elif not human_rejected_dashboard.exists():
        human_rejected_dashboard.write_text("[]\n", encoding="utf-8")
        print(f"Initialized {human_rejected_dashboard.relative_to(REPO_ROOT)}")

    metrics = _load_json(OUTPUT_DIR / "metrics.json")
    errors = _load_json(OUTPUT_DIR / "extraction_errors.json")
    human_rejected = _load_json(human_rejected_dashboard)
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
