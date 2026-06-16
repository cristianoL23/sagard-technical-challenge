import re
from typing import Optional

from src.config import COMPANY_ALIASES, CONFIDENCE_THRESHOLD, PERIOD_PATTERNS
from src.llm_identity import to_company_identity
from src.models import CompanyIdentity, IdentityCandidate, ParsedDocument, PeriodType


def _parse_period_from_text(text: str) -> Optional[tuple[int, str]]:
    for pattern in PERIOD_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        groups = match.groups()
        if len(groups) == 2:
            if groups[0].isdigit() and len(groups[0]) == 4:
                year, quarter_num = int(groups[0]), int(groups[1])
            else:
                quarter_num, year = int(groups[0]), int(groups[1])
            return year, f"Q{quarter_num}"
    return None


def normalize_company_short_name(short_name: str) -> str:
    """Map former portfolio names to the current canonical short name."""
    key = short_name.strip().lower()
    return COMPANY_ALIASES.get(key, short_name.strip())


def infer_period(
    filename: str,
    metadata_title: Optional[str],
    first_page_text: str,
) -> tuple[Optional[int], Optional[str], PeriodType]:
    for source in (filename, metadata_title or "", first_page_text):
        period = _parse_period_from_text(source)
        if period:
            return period[0], period[1], "quarter"
    return None, None, "unknown"


def _is_grounded(candidate: IdentityCandidate, full_text: str) -> bool:
    for text in (candidate.evidence_text, candidate.company_full_name):
        if text and text in full_text:
            return True
    return False


def _apply_period_cross_check(
    candidate: IdentityCandidate,
    filename: str,
    metadata_title: Optional[str],
    first_page_text: str,
) -> Optional[IdentityCandidate]:
    regex_year, regex_quarter, regex_period_type = infer_period(
        filename, metadata_title, first_page_text
    )
    if regex_year is None and regex_quarter is None:
        return candidate

    if candidate.year is not None and candidate.year != regex_year:
        return None
    if candidate.quarter is not None and candidate.quarter != regex_quarter:
        return None

    year = candidate.year if candidate.year is not None else regex_year
    quarter = candidate.quarter if candidate.quarter is not None else regex_quarter
    period_type = candidate.period_type
    if period_type == "unknown" and regex_period_type != "unknown":
        period_type = regex_period_type

    return IdentityCandidate(
        company_short_name=candidate.company_short_name,
        company_full_name=candidate.company_full_name,
        year=year,
        quarter=quarter,
        period_type=period_type,
        source_file=candidate.source_file,
        is_single_company_report=candidate.is_single_company_report,
        confidence=candidate.confidence,
        evidence_text=candidate.evidence_text,
    )


def validate_company_identity(
    candidate: IdentityCandidate,
    parsed: ParsedDocument,
    filename: str,
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
) -> Optional[CompanyIdentity]:
    """Validate LLM identity; return CompanyIdentity or None if checks fail."""
    if not candidate.is_single_company_report:
        return None
    if candidate.confidence < confidence_threshold:
        return None
    if not candidate.company_short_name or not candidate.company_full_name:
        return None
    if not _is_grounded(candidate, parsed.full_text):
        return None

    first_page_text = parsed.pages[0].text if parsed.pages else ""
    adjusted = _apply_period_cross_check(
        candidate,
        filename,
        parsed.metadata_title,
        first_page_text,
    )
    if adjusted is None:
        return None

    return to_company_identity(adjusted)


def detect_document_currency(full_text: str) -> Optional[str]:
    """Infer document-level reporting currency from text."""
    patterns = [
        r"Reporting Currency:\s*(USD|GBP|CAD|EUR)",
        r"\((GBP) unless noted\)",
        r"All figures in (USD|GBP|CAD|EUR)",
        r"figures in (USD|GBP|CAD|EUR) unless",
    ]
    for pattern in patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match and match.lastindex:
            return match.group(1).upper()
    return None
