import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ERRORS_PATH = REPO_ROOT / "output" / "extraction_errors.json"


def build_record_id(record: dict) -> str:
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


def accept_pending_record(data_dir: Path, record_id: str) -> None:
    metrics = json.loads((data_dir / "metrics.json").read_text(encoding="utf-8"))
    pending = json.loads((data_dir / "extraction_errors.json").read_text(encoding="utf-8"))

    record = next((row for row in pending if build_record_id(row) == record_id), None)
    if record is None:
        raise ValueError("Record not found in review queue")

    accepted = {k: v for k, v in record.items() if k not in {"status", "error_message", "review_decision", "id"}}
    next_pending = [row for row in pending if build_record_id(row) != record_id]
    next_metrics = [*metrics, accepted]

    (data_dir / "metrics.json").write_text(json.dumps(next_metrics, indent=2) + "\n", encoding="utf-8")
    (data_dir / "extraction_errors.json").write_text(
        json.dumps(next_pending, indent=2) + "\n", encoding="utf-8"
    )


def reject_pending_record(data_dir: Path, record_id: str) -> None:
    pending = json.loads((data_dir / "extraction_errors.json").read_text(encoding="utf-8"))
    rejected = json.loads((data_dir / "human_rejected.json").read_text(encoding="utf-8"))

    record = next((row for row in pending if build_record_id(row) == record_id), None)
    if record is None:
        raise ValueError("Record not found in review queue")

    next_pending = [row for row in pending if build_record_id(row) != record_id]
    next_rejected = [*rejected, {**record, "review_decision": "human_rejected"}]

    (data_dir / "extraction_errors.json").write_text(
        json.dumps(next_pending, indent=2) + "\n", encoding="utf-8"
    )
    (data_dir / "human_rejected.json").write_text(
        json.dumps(next_rejected, indent=2) + "\n", encoding="utf-8"
    )


class ReviewDemoDataTest(unittest.TestCase):
    def test_extraction_errors_contains_fabricated_review_examples(self):
        errors = json.loads(ERRORS_PATH.read_text(encoding="utf-8"))
        low_confidence = [
            row
            for row in errors
            if row.get("status") == "low_confidence" and row.get("confidence", 1) < 0.5
        ]
        missing_source_text = [
            row for row in errors if row.get("status") == "missing_source_text"
        ]

        self.assertGreaterEqual(len(low_confidence), 1)
        self.assertGreaterEqual(len(missing_source_text), 1)

        peopleflow = next(
            (row for row in low_confidence if row["company_short_name"] == "PeopleFlow"),
            None,
        )
        self.assertIsNotNone(peopleflow)
        self.assertEqual(peopleflow["metric_name"], "revenue")
        self.assertEqual(peopleflow["year"], 2025)
        self.assertEqual(peopleflow["quarter"], "Q2")


class ReviewStoreTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.pending_record = {
            "company_short_name": "PeopleFlow",
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
        }
        (self.temp_dir / "metrics.json").write_text("[]\n", encoding="utf-8")
        (self.temp_dir / "extraction_errors.json").write_text(
            json.dumps([self.pending_record], indent=2) + "\n", encoding="utf-8"
        )
        (self.temp_dir / "human_rejected.json").write_text("[]\n", encoding="utf-8")

    def test_build_record_id_is_stable(self):
        self.assertEqual(
            build_record_id(self.pending_record),
            build_record_id(self.pending_record),
        )

    def test_accept_moves_record_into_metrics(self):
        record_id = build_record_id(self.pending_record)
        accept_pending_record(self.temp_dir, record_id)

        metrics = json.loads((self.temp_dir / "metrics.json").read_text(encoding="utf-8"))
        pending = json.loads((self.temp_dir / "extraction_errors.json").read_text(encoding="utf-8"))

        self.assertEqual(len(metrics), 1)
        self.assertEqual(len(pending), 0)
        self.assertEqual(metrics[0]["company_short_name"], "PeopleFlow")
        self.assertNotIn("status", metrics[0])

    def test_reject_moves_record_into_human_rejected(self):
        record_id = build_record_id(self.pending_record)
        reject_pending_record(self.temp_dir, record_id)

        pending = json.loads((self.temp_dir / "extraction_errors.json").read_text(encoding="utf-8"))
        rejected = json.loads((self.temp_dir / "human_rejected.json").read_text(encoding="utf-8"))

        self.assertEqual(len(pending), 0)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["review_decision"], "human_rejected")


if __name__ == "__main__":
    unittest.main()
