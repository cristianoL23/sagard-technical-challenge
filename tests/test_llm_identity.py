from src.llm_identity import build_identity_candidate
from src.models import ParsedDocument, ParsedPage


def test_build_identity_candidate_maps_llm_payload():
    parsed = ParsedDocument(
        source_file="NovaCloud_Q2_2025.pdf",
        pages=[ParsedPage(page_number=1, text="NovaCloud Analytics Inc.", tables=[])],
        full_text="NovaCloud Analytics Inc.\nPeriod: Q2 2025",
    )
    payload = {
        "company_short_name": "NovaCloud",
        "company_full_name": "NovaCloud Analytics Inc.",
        "year": 2025,
        "quarter": "Q2",
        "period_type": "quarter",
        "is_single_company_report": True,
        "confidence": 0.95,
        "evidence_text": "NovaCloud Analytics Inc.",
    }
    candidate = build_identity_candidate(parsed, payload)
    assert candidate.company_short_name == "NovaCloud"
    assert candidate.company_full_name == "NovaCloud Analytics Inc."
    assert candidate.year == 2025
    assert candidate.quarter == "Q2"
    assert candidate.is_single_company_report is True
    assert candidate.confidence == 0.95
    assert candidate.evidence_text == "NovaCloud Analytics Inc."


def test_build_identity_candidate_handles_invalid_confidence():
    parsed = ParsedDocument(
        source_file="NovaCloud_Q2_2025.pdf",
        pages=[ParsedPage(page_number=1, text="sample", tables=[])],
        full_text="sample",
    )
    candidate = build_identity_candidate(
        parsed,
        {
            "company_short_name": "NovaCloud",
            "company_full_name": "NovaCloud Analytics Inc.",
            "confidence": "invalid",
            "is_single_company_report": True,
        },
    )
    assert candidate.confidence == 0.0
