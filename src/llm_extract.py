"""LLM-assisted metric extraction."""

import json
from typing import Any, Optional

from src.config import (
    CANONICAL_METRICS,
    LLM_JSON_INSTRUCTIONS,
    PERIOD_TYPES_PROMPT,
    SCALE_TYPES_PROMPT,
    UNIT_TYPES_PROMPT,
)
from src.company_identity import detect_document_currency
from src.llm_client import call_llm_json, truncate_text
from src.llm_parsing import map_period_type, map_scale, map_unit
from src.models import CompanyIdentity, ExtractedMetric, ParsedDocument
from src.normalize import normalize_metric_name, normalize_value, to_display_scale

SYSTEM_PROMPT = f"""You are extracting portfolio company metrics from PDF text.
{LLM_JSON_INSTRUCTIONS}
Only extract metrics explicitly present in the text. Do not infer missing metrics."""

USER_PROMPT_TEMPLATE = """You are extracting portfolio company metrics from PDF text.

This PDF belongs to portfolio company "{company_short_name}" ({company_full_name}).
Use this validated identity for every record:
- company_short_name: {company_short_name}
- company_full_name: {company_full_name}
- year: {year}
- quarter: {quarter}
- period_type: {period_type}

Only extract metrics explicitly present in the text. Do not infer missing metrics.
Include cash metrics when present. Labels such as "Cash & Equivalents", "Cash Balance",
"Cash & Restricted Cash", or similar wording must use metric_name cash_balance.

Output format:
- Return only a raw JSON array. No markdown fences, no comments, no prose before or after.
- Return [] if no metrics are found.
- Each array element must be one JSON object with these keys:
  - company_short_name (string)
  - company_full_name (string)
  - year (integer or null)
  - quarter (string or null, e.g. "Q2")
  - period_type (one of: {period_types})
  - report_date (ISO date string "YYYY-MM-DD" or null)
  - metric_name (string; must be one of the allowed canonical names)
  - metric_label (string; exact label from the source)
  - value (number or null)
  - unit (one of: {unit_types})
  - scale (one of: {scale_types})
  - currency (string such as "USD" or null)
  - source_page (integer or null)
  - confidence (number from 0 to 1)
  - raw_text (string; exact supporting substring from the PDF)

Example output:
[
  {{
    "company_short_name": "NovaCloud",
    "company_full_name": "NovaCloud Analytics Inc.",
    "year": 2025,
    "quarter": "Q2",
    "period_type": "quarter",
    "report_date": null,
    "metric_name": "revenue",
    "metric_label": "Recognized Revenue",
    "value": 8.4,
    "unit": "currency",
    "scale": "millions",
    "currency": "USD",
    "source_page": 1,
    "confidence": 0.95,
    "raw_text": "Recognized Revenue $8.4M"
  }}
]

Allowed metric names:
{allowed_metrics}

PDF text:
{text}
"""


def extract_with_llm(
    text: str,
    identity: CompanyIdentity,
    allowed_metrics: list[str],
) -> list[dict[str, Any]]:
    result = call_llm_json(
        SYSTEM_PROMPT,
        USER_PROMPT_TEMPLATE.format(
            company_short_name=identity.company_short_name,
            company_full_name=identity.company_full_name or identity.company_short_name,
            year=identity.year,
            quarter=identity.quarter,
            period_type=identity.period_type,
            period_types=PERIOD_TYPES_PROMPT,
            unit_types=UNIT_TYPES_PROMPT,
            scale_types=SCALE_TYPES_PROMPT,
            allowed_metrics=", ".join(allowed_metrics),
            text=text,
        ),
    )
    if not isinstance(result, list):
        raise ValueError("Metrics LLM response must be a JSON array")
    return result


def _build_metric_from_llm_item(
    item: dict[str, Any],
    identity: CompanyIdentity,
    parsed: ParsedDocument,
    document_currency: Optional[str],
    default_page: Optional[int],
) -> Optional[ExtractedMetric]:
    metric_name_raw = item.get("metric_name") or item.get("metric")
    if not metric_name_raw:
        return None

    metric_name = normalize_metric_name(str(metric_name_raw))
    if metric_name not in CANONICAL_METRICS:
        metric_name = "other"

    raw_text = item.get("raw_text") or item.get("raw_context") or ""
    raw_value = item.get("raw_value")
    metric_label = item.get("metric_label") or item.get("raw_label") or str(metric_name_raw)

    value = item.get("value")
    unit = map_unit(item.get("unit"))
    scale = map_scale(item.get("scale"))
    currency = item.get("currency")

    if raw_value:
        parsed_value, parsed_unit, parsed_scale, parsed_currency = normalize_value(
            str(raw_value),
            unit_type=unit if unit != "unknown" else None,
            raw_context=raw_text,
            document_currency=document_currency,
        )
        if parsed_value is not None:
            value = parsed_value
            if parsed_unit:
                unit = parsed_unit  # type: ignore[assignment]
            if parsed_scale != "unknown":
                scale = parsed_scale  # type: ignore[assignment]
            if parsed_currency:
                currency = parsed_currency

    if value is None and item.get("value") is not None:
        try:
            value = float(item["value"])
        except (TypeError, ValueError):
            return None

    if raw_text and (value is None or unit in ("currency", "unknown")):
        parsed_value, parsed_unit, parsed_scale, parsed_currency = normalize_value(
            raw_text,
            unit_type=unit if unit != "unknown" else None,
            raw_context=raw_text,
            document_currency=document_currency,
        )
        if parsed_value is not None and parsed_unit == "currency":
            needs_raw_text_value = value is None or (
                scale in ("thousands", "millions", "billions")
                and abs(float(value)) >= 1_000
            )
            if needs_raw_text_value:
                value = parsed_value
                unit = parsed_unit  # type: ignore[assignment]
                if parsed_scale != "unknown":
                    scale = parsed_scale  # type: ignore[assignment]
                if parsed_currency:
                    currency = parsed_currency

    if value is None:
        return None

    if scale in ("thousands", "millions", "billions"):
        value = to_display_scale(float(value), scale)

    confidence = item.get("confidence", 0.7)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        return None
    if not (0 <= confidence <= 1):
        return None

    return ExtractedMetric(
        company_short_name=item.get("company_short_name") or identity.company_short_name,
        company_full_name=item.get("company_full_name") or identity.company_full_name,
        year=item.get("year") or identity.year,
        quarter=item.get("quarter") or identity.quarter,
        period_type=map_period_type(item.get("period_type") or identity.period_type),
        metric_name=metric_name,
        metric_label=metric_label,
        value=value,
        unit=unit,  # type: ignore[arg-type]
        scale=scale,  # type: ignore[arg-type]
        currency=currency or document_currency,
        source_file=parsed.source_file,
        source_page=item.get("source_page") or default_page,
        confidence=confidence,
        raw_text=raw_text or None,
    )


def extract_metrics_with_llm(
    parsed: ParsedDocument,
    identity: CompanyIdentity,
) -> list[ExtractedMetric]:
    document_currency = detect_document_currency(parsed.full_text)
    rows: list[ExtractedMetric] = []

    full_text = parsed.full_text
    if not full_text.strip():
        return rows

    text_chunk = truncate_text(full_text)

    try:
        llm_results = extract_with_llm(text_chunk, identity, CANONICAL_METRICS)
    except (json.JSONDecodeError, RuntimeError, ValueError):
        return rows

    for item in llm_results:
        if not isinstance(item, dict):
            continue
        metric = _build_metric_from_llm_item(
            item,
            identity,
            parsed,
            document_currency,
            default_page=1,
        )
        if metric is not None:
            rows.append(metric)

    return rows
