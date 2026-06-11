"""LLM-assisted company identity extraction."""

from pathlib import Path
from typing import Any, Optional

from src.config import LLM_JSON_INSTRUCTIONS, PERIOD_TYPES_PROMPT
from src.llm_client import call_llm_json, truncate_text
from src.llm_parsing import map_period_type
from src.models import CompanyIdentity, IdentityCandidate, ParsedDocument

SYSTEM_PROMPT = f"""You are identifying the company and reporting period from a portfolio PDF.
{LLM_JSON_INSTRUCTIONS}
Read company names from the document text, not from assumptions."""

USER_PROMPT_TEMPLATE = """Identify the company and reporting period for this PDF.

The filename "{filename_hint}" is a hint only. Use the PDF text as the source of truth.
Set is_single_company_report to false if the document covers multiple companies or is a portfolio summary.

Return a JSON object with:
- company_short_name: concise portfolio name (e.g. NovaCloud, Apex Freight)
- company_full_name: exact legal name from the document heading
- year: integer or null
- quarter: e.g. Q1, Q2, or null
- period_type: {period_types}
- is_single_company_report: true or false
- confidence: 0 to 1
- evidence_text: exact substring from the PDF supporting company_full_name

PDF text:
{text}
"""


def extract_identity_with_llm(parsed: ParsedDocument, filename_hint: str) -> dict[str, Any]:
    text = truncate_text(parsed.full_text)
    payload = call_llm_json(
        SYSTEM_PROMPT,
        USER_PROMPT_TEMPLATE.format(
            filename_hint=filename_hint,
            period_types=PERIOD_TYPES_PROMPT,
            text=text,
        ),
    )
    if not isinstance(payload, dict):
        raise ValueError("Identity LLM response must be a JSON object")
    return payload


def build_identity_candidate(
    parsed: ParsedDocument,
    llm_payload: dict[str, Any],
) -> IdentityCandidate:
    confidence = llm_payload.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    year = llm_payload.get("year")
    if year is not None:
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = None

    return IdentityCandidate(
        company_short_name=str(llm_payload.get("company_short_name") or "").strip(),
        company_full_name=str(llm_payload.get("company_full_name") or "").strip(),
        year=year,
        quarter=llm_payload.get("quarter"),
        period_type=map_period_type(llm_payload.get("period_type")),
        source_file=parsed.source_file,
        is_single_company_report=bool(llm_payload.get("is_single_company_report", False)),
        confidence=confidence,
        evidence_text=str(llm_payload.get("evidence_text") or "").strip(),
    )


def to_company_identity(candidate: IdentityCandidate) -> CompanyIdentity:
    return CompanyIdentity(
        company_short_name=candidate.company_short_name,
        company_full_name=candidate.company_full_name,
        year=candidate.year,
        quarter=candidate.quarter,
        period_type=candidate.period_type,
        source_file=candidate.source_file,
    )


def extract_and_build_identity(
    parsed: ParsedDocument,
    pdf_path: Path,
) -> IdentityCandidate:
    llm_payload = extract_identity_with_llm(parsed, pdf_path.name)
    return build_identity_candidate(parsed, llm_payload)
