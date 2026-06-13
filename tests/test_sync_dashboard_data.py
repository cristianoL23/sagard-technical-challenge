import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "output"
DASHBOARD_DATA_DIR = REPO_ROOT / "dashboard" / "public" / "data"


def test_output_snapshot_exists():
    for name in ("metrics.json", "metrics.csv", "metrics_wide.csv", "extraction_errors.json"):
        assert (OUTPUT_DIR / name).exists(), f"missing output/{name}"


def test_sync_dashboard_data_copies_json():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync_dashboard_data.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Synced dashboard data" in result.stdout

    for name in ("metrics.json", "extraction_errors.json"):
        source = (OUTPUT_DIR / name).read_text(encoding="utf-8")
        target = (DASHBOARD_DATA_DIR / name).read_text(encoding="utf-8")
        assert source == target

    metrics = json.loads((DASHBOARD_DATA_DIR / "metrics.json").read_text(encoding="utf-8"))
    assert len(metrics) > 0
