from src.models import ExtractedMetric
from src.validate import classify_extraction, route_extractions


def _sample_metric(**kwargs) -> ExtractedMetric:
    defaults = {
        "company_short_name": "NovaCloud",
        "company_full_name": "NovaCloud Analytics Inc.",
        "year": 2025,
        "quarter": "Q2",
        "period_type": "quarter",
        "metric_name": "revenue",
        "metric_label": "Recognized Revenue",
        "value": 8.4,
        "unit": "currency",
        "scale": "millions",
        "currency": "USD",
        "source_file": "NovaCloud_Q2_2025.pdf",
        "source_page": 1,
        "confidence": 0.9,
        "raw_text": "Recognized Revenue $8.4M",
    }
    defaults.update(kwargs)
    return ExtractedMetric(**defaults)


def test_classify_accepts_valid_metric():
    assert classify_extraction(_sample_metric()) is None


def test_classify_rejects_low_confidence():
    assert classify_extraction(_sample_metric(confidence=0.3)) == "low_confidence"


def test_classify_rejects_unsupported_metric():
    assert classify_extraction(_sample_metric(metric_name="ebitda")) == "unsupported_metric"


def test_classify_rejects_missing_source_text():
    assert classify_extraction(_sample_metric(raw_text=None)) == "missing_source_text"


def test_classify_rejects_ungrounded_raw_text():
    assert (
        classify_extraction(
            _sample_metric(raw_text="Not in document"),
            source_text="Recognized Revenue $8.4M",
        )
        == "missing_source_text"
    )


def test_route_extractions_splits_accepted_and_rejected():
    metrics = [
        _sample_metric(),
        _sample_metric(confidence=0.2, metric_name="arr"),
        _sample_metric(metric_name="ebitda"),
    ]
    accepted, rejected = route_extractions(metrics, confidence_threshold=0.5)
    assert len(accepted) == 1
    assert len(rejected) == 2
