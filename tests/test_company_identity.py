import pytest

from src.company_identity import (
    detect_document_currency,
    infer_period,
    validate_company_identity,
)
from src.models import IdentityCandidate, ParsedDocument, ParsedPage


def _sample_candidate(**kwargs) -> IdentityCandidate:
    defaults = {
        "company_short_name": "NovaCloud",
        "company_full_name": "NovaCloud Analytics Inc.",
        "year": 2025,
        "quarter": "Q2",
        "period_type": "quarter",
        "source_file": "NovaCloud_Q2_2025.pdf",
        "is_single_company_report": True,
        "confidence": 0.9,
        "evidence_text": "NovaCloud Analytics Inc.",
    }
    defaults.update(kwargs)
    return IdentityCandidate(**defaults)


def test_infer_period_from_filename():
    year, quarter, period_type = infer_period(
        "NovaCloud_Q2_2025.pdf", None, ""
    )
    assert year == 2025
    assert quarter == "Q2"
    assert period_type == "quarter"


def test_validate_company_identity_accepts_valid_candidate():
    parsed = ParsedDocument(
        source_file="NovaCloud_Q2_2025.pdf",
        pages=[
            ParsedPage(
                page_number=1,
                text="NovaCloud Analytics Inc.\nPeriod: Q2 2025",
                tables=[],
            )
        ],
        full_text="NovaCloud Analytics Inc.\nPeriod: Q2 2025",
    )
    identity = validate_company_identity(
        _sample_candidate(),
        parsed,
        "NovaCloud_Q2_2025.pdf",
    )
    assert identity is not None
    assert identity.company_short_name == "NovaCloud"
    assert identity.company_full_name == "NovaCloud Analytics Inc."
    assert identity.year == 2025
    assert identity.quarter == "Q2"


def test_validate_company_identity_fills_period_from_regex():
    parsed = ParsedDocument(
        source_file="NovaCloud_Q2_2025.pdf",
        pages=[ParsedPage(page_number=1, text="NovaCloud Analytics Inc.", tables=[])],
        full_text="NovaCloud Analytics Inc.",
    )
    candidate = _sample_candidate(year=None, quarter=None, period_type="unknown")
    identity = validate_company_identity(
        candidate,
        parsed,
        "NovaCloud_Q2_2025.pdf",
    )
    assert identity is not None
    assert identity.year == 2025
    assert identity.quarter == "Q2"
    assert identity.period_type == "quarter"


def test_validate_company_identity_rejects_multi_company():
    parsed = ParsedDocument(
        source_file="Portfolio_Snapshot_Q2_2025.pdf",
        pages=[ParsedPage(page_number=1, text="Portfolio Summary", tables=[])],
        full_text="Portfolio Summary",
    )
    candidate = _sample_candidate(
        company_short_name="Portfolio",
        company_full_name="Portfolio Summary",
        is_single_company_report=False,
        evidence_text="Portfolio Summary",
    )
    assert validate_company_identity(candidate, parsed, "Portfolio_Snapshot_Q2_2025.pdf") is None


def test_validate_company_identity_rejects_low_confidence():
    parsed = ParsedDocument(
        source_file="NovaCloud_Q2_2025.pdf",
        pages=[ParsedPage(page_number=1, text="NovaCloud Analytics Inc.", tables=[])],
        full_text="NovaCloud Analytics Inc.",
    )
    candidate = _sample_candidate(confidence=0.2)
    assert validate_company_identity(candidate, parsed, "NovaCloud_Q2_2025.pdf") is None


def test_validate_company_identity_rejects_ungrounded_evidence():
    parsed = ParsedDocument(
        source_file="NovaCloud_Q2_2025.pdf",
        pages=[ParsedPage(page_number=1, text="Different Co Inc.", tables=[])],
        full_text="Different Co Inc.",
    )
    assert validate_company_identity(_sample_candidate(), parsed, "NovaCloud_Q2_2025.pdf") is None


def test_validate_company_identity_rejects_period_mismatch():
    parsed = ParsedDocument(
        source_file="NovaCloud_Q2_2025.pdf",
        pages=[ParsedPage(page_number=1, text="NovaCloud Analytics Inc.", tables=[])],
        full_text="NovaCloud Analytics Inc.",
    )
    candidate = _sample_candidate(year=2024, quarter="Q1")
    assert validate_company_identity(candidate, parsed, "NovaCloud_Q2_2025.pdf") is None


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Reporting Currency: GBP", "GBP"),
        ("Metric (GBP unless noted) Q2 2025", "GBP"),
        ("All figures in USD unless otherwise stated.", "USD"),
        ("figures in EUR unless noted", "EUR"),
        ("No currency hints here", None),
    ],
)
def test_detect_document_currency(text, expected):
    assert detect_document_currency(text) == expected
