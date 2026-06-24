import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "output"
DASHBOARD_DATA_DIR = REPO_ROOT / "dashboard" / "public" / "data"


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
        source = json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))
        target = json.loads((DASHBOARD_DATA_DIR / name).read_text(encoding="utf-8"))
        if name == "metrics.json":
            assert source == target

    assert (DASHBOARD_DATA_DIR / "human_rejected.json").exists()

    metrics = json.loads((DASHBOARD_DATA_DIR / "metrics.json").read_text(encoding="utf-8"))
    assert len(metrics) > 0
    pending = json.loads(
        (DASHBOARD_DATA_DIR / "extraction_errors.json").read_text(encoding="utf-8")
    )
    human_rejected = json.loads(
        (DASHBOARD_DATA_DIR / "human_rejected.json").read_text(encoding="utf-8")
    )

    required_examples = {
        ("PeopleFlow", "Quarterly Revenue", "low_confidence"),
        ("NovaCloud", "Professional Services Revenue", "missing_source_text"),
    }
    present_examples = {
        (row.get("company_short_name"), row.get("metric_label"), row.get("status"))
        for row in pending
    }
    assert required_examples.issubset(present_examples)

    pending_ids = {_build_record_id(row) for row in pending}
    human_rejected_ids = {_build_record_id(row) for row in human_rejected}
    assert pending_ids.isdisjoint(human_rejected_ids)

    pdfs_dir = REPO_ROOT / "dashboard" / "public" / "pdfs"
    assert pdfs_dir.exists()
    assert any(pdfs_dir.glob("*.pdf"))
