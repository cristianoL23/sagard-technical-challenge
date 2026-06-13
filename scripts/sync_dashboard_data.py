#!/usr/bin/env python3
"""Copy committed pipeline JSON outputs into the dashboard public data folder."""

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "output"
DASHBOARD_DATA_DIR = REPO_ROOT / "dashboard" / "public" / "data"

FILES = ("metrics.json", "extraction_errors.json")


def main() -> None:
    missing = [name for name in FILES if not (OUTPUT_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(
            "Missing pipeline output files in output/: "
            + ", ".join(missing)
            + ". Run: python -m src.pipeline run --input data/raw --output-dir output"
        )

    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)

    for name in FILES:
        source = OUTPUT_DIR / name
        target = DASHBOARD_DATA_DIR / name
        shutil.copy2(source, target)
        print(f"Copied {source.relative_to(REPO_ROOT)} -> {target.relative_to(REPO_ROOT)}")

    metrics = json.loads((OUTPUT_DIR / "metrics.json").read_text(encoding="utf-8"))
    print(f"Synced dashboard data ({len(metrics)} metric records).")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
