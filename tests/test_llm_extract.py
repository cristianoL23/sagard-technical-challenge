import json
from unittest.mock import patch

from src.llm_client import DEFAULT_LLM_MODEL
from src.llm_extract import extract_metrics_with_llm
from src.models import CompanyIdentity, ParsedDocument, ParsedPage


def _sample_identity() -> CompanyIdentity:
    return CompanyIdentity(
        company_short_name="NovaCloud",
        company_full_name="NovaCloud Analytics Inc.",
        year=2025,
        quarter="Q2",
        period_type="quarter",
        source_file="NovaCloud_Q2_2025.pdf",
    )


def test_default_llm_model_is_valid_openai_name():
    assert DEFAULT_LLM_MODEL == "gpt-4o-mini"


def test_extract_metrics_with_llm_parses_valid_items():
    parsed = ParsedDocument(
        source_file="NovaCloud_Q2_2025.pdf",
        pages=[
            ParsedPage(
                page_number=1,
                text="NovaCloud Analytics Inc.\nRecognized Revenue $8.4M",
                tables=[],
            )
        ],
        full_text="NovaCloud Analytics Inc.\nRecognized Revenue $8.4M",
    )
    identity = _sample_identity()

    llm_payload = [
        {
            "company_short_name": "NovaCloud",
            "company_full_name": "NovaCloud Analytics Inc.",
            "metric_name": "revenue",
            "metric_label": "Recognized Revenue",
            "value": 8.4,
            "unit": "currency",
            "scale": "millions",
            "currency": "USD",
            "confidence": 0.9,
            "raw_text": "Recognized Revenue $8.4M",
            "source_page": 1,
        },
        {
            "metric_name": "arr",
            "raw_value": "n/a",
            "confidence": 0.9,
            "raw_text": "ARR unavailable",
        },
    ]

    with patch("src.llm_extract.extract_with_llm", return_value=llm_payload):
        rows = extract_metrics_with_llm(parsed, identity)

    assert len(rows) == 1
    assert rows[0].metric_name == "revenue"
    assert rows[0].value == 8.4
    assert rows[0].scale == "millions"
    assert rows[0].company_full_name == "NovaCloud Analytics Inc."


def test_extract_metrics_with_llm_parses_cash_from_raw_text():
    parsed = ParsedDocument(
        source_file="ConstructIQ_Q2_2025.pdf",
        pages=[
            ParsedPage(
                page_number=1,
                text="ConstructIQ Solutions Inc.\nCash & Equivalents $11.2M $12.1M",
                tables=[],
            )
        ],
        full_text="ConstructIQ Solutions Inc.\nCash & Equivalents $11.2M $12.1M",
    )
    identity = CompanyIdentity(
        company_short_name="ConstructIQ",
        company_full_name="ConstructIQ Solutions Inc.",
        year=2025,
        quarter="Q2",
        period_type="quarter",
        source_file="ConstructIQ_Q2_2025.pdf",
    )

    llm_payload = [
        {
            "company_short_name": "ConstructIQ",
            "company_full_name": "ConstructIQ Solutions Inc.",
            "year": 2025,
            "quarter": "Q2",
            "period_type": "quarter",
            "metric_name": "cash_balance",
            "metric_label": "Cash & Equivalents",
            "value": 11_200_000,
            "unit": "currency",
            "scale": "millions",
            "confidence": 1.0,
            "raw_text": "$11.2M $12.1M",
            "source_page": 1,
        }
    ]

    with patch("src.llm_extract.extract_with_llm", return_value=llm_payload):
        rows = extract_metrics_with_llm(parsed, identity)

    assert len(rows) == 1
    assert rows[0].metric_name == "cash_balance"
    assert rows[0].metric_label == "Cash & Equivalents"
    assert rows[0].value == 11.2
    assert rows[0].scale == "millions"


def test_extract_metrics_with_llm_handles_invalid_json():
    parsed = ParsedDocument(
        source_file="NovaCloud_Q2_2025.pdf",
        pages=[ParsedPage(page_number=1, text="sample", tables=[])],
        full_text="sample",
    )
    identity = _sample_identity()

    with patch("src.llm_extract.extract_with_llm", side_effect=json.JSONDecodeError("err", "doc", 0)):
        rows = extract_metrics_with_llm(parsed, identity)

    assert rows == []
