from typing import Optional

from src.config import CANONICAL_METRICS, CONFIDENCE_THRESHOLD
from src.models import ErrorStatus, ExtractedMetric, ExtractionError


def classify_extraction(
    metric: ExtractedMetric,
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
    source_text: Optional[str] = None,
) -> Optional[ErrorStatus]:
    if not metric.company_short_name:
        return "ambiguous_company"
    if metric.confidence < confidence_threshold:
        return "low_confidence"
    if not metric.raw_text:
        return "missing_source_text"
    if source_text is not None and metric.raw_text not in source_text:
        return "missing_source_text"
    if metric.metric_name not in CANONICAL_METRICS:
        return "unsupported_metric"
    if metric.value is None:
        return "invalid_number"
    return None


def route_extractions(
    metrics: list[ExtractedMetric],
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
    source_text: Optional[str] = None,
) -> tuple[list[ExtractedMetric], list[ExtractionError]]:
    accepted: list[ExtractedMetric] = []
    rejected: list[ExtractionError] = []

    for metric in metrics:
        status = classify_extraction(metric, confidence_threshold, source_text)
        if status is None:
            accepted.append(metric)
        else:
            rejected.append(
                ExtractionError(
                    **metric.model_dump(),
                    status=status,
                    error_message=_error_message(status),
                )
            )

    return accepted, rejected


def _error_message(status: ErrorStatus) -> str:
    messages = {
        "low_confidence": "Confidence below acceptance threshold",
        "missing_source_text": "No supporting source text provided",
        "ambiguous_company": "Company identity could not be determined",
        "unsupported_metric": "Metric name is not in the supported dictionary",
        "invalid_number": "Value could not be parsed as a valid number",
        "llm_parse_error": "LLM response could not be parsed",
    }
    return messages.get(status, "Extraction rejected")
