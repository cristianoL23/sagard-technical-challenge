import re
from typing import Optional

from src.config import CURRENCY_CODES, METRIC_ALIASES

GBP_SYMBOL = "\u00a3"
EUR_SYMBOL = "\u20ac"

VALUE_PATTERN = re.compile(
    rf"""
    (?P<negative_paren>\()?
    (?P<prefix_currency>\$|{GBP_SYMBOL}|{EUR_SYMBOL}|USD|GBP|CAD|EUR)?
    \s*
    (?P<sign>[-+])?
    (?P<number>\d+(?:,\d{{3}})*(?:\.\d+)?|\d+(?:\.\d+)?)
    \s*
    (?P<suffix>bps|bp|months?|thousand|million|MM|k|K|%|x|B|b|M|)
    (?P<negative_paren_close>\))?
    """,
    re.IGNORECASE | re.VERBOSE,
)

CURRENCY_CODE_SET = set(CURRENCY_CODES)
ScaleType = Optional[str]


def _parse_number(number_str: str) -> float:
    return float(number_str.replace(",", ""))


def _suffix_to_scale(suffix: str) -> str:
    suffix_lower = suffix.lower()
    if suffix_lower in ("k", "thousand"):
        return "thousands"
    if suffix_lower in ("m", "mm", "million"):
        return "millions"
    if suffix_lower == "b":
        return "billions"
    return "ones"


def _detect_currency(
    prefix: str,
    raw: str,
    raw_context: Optional[str],
    document_currency: Optional[str],
) -> Optional[str]:
    prefix_upper = prefix.upper() if prefix else ""
    if prefix_upper in CURRENCY_CODE_SET:
        return prefix_upper
    if prefix == "$":
        return "USD"
    if prefix == GBP_SYMBOL:
        return "GBP"
    if prefix == EUR_SYMBOL:
        return "EUR"

    for source in (raw, raw_context or ""):
        for code in CURRENCY_CODES:
            if re.search(rf"\b{code}\b", source, re.IGNORECASE):
                return code
        if "$" in source:
            return "USD"
        if GBP_SYMBOL in source:
            return "GBP"

    return document_currency


def normalize_metric_name(label_or_name: str) -> str:
    key = label_or_name.strip().lower()
    if key in METRIC_ALIASES:
        return METRIC_ALIASES[key]
    for alias, canonical in sorted(METRIC_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if alias in key:
            return canonical
    return label_or_name.strip().lower().replace(" ", "_")


def normalize_value(
    raw: str,
    unit_type: Optional[str] = None,
    raw_context: Optional[str] = None,
    document_currency: Optional[str] = None,
) -> tuple[Optional[float], Optional[str], str, Optional[str]]:
    """
    Parse a raw value string into (value, unit, scale, currency).

    Values are stored in display scale: $8.4M -> 8.4 with scale=millions.
    Percentages stored as displayed: 78% -> 78.0 with unit=percentage.
    """
    text = raw.strip()
    if not text or re.fullmatch(r"n/?a", text, re.IGNORECASE):
        return None, None, "unknown", None

    match = VALUE_PATTERN.search(text)
    if not match:
        return None, None, "unknown", None

    groups = match.groupdict()
    number = _parse_number(groups["number"])
    suffix = (groups["suffix"] or "").strip()
    suffix_lower = suffix.lower()
    scale = _suffix_to_scale(suffix)

    is_negative = bool(groups["negative_paren"]) or groups["sign"] == "-"
    if is_negative:
        number = -abs(number)

    currency: Optional[str] = None
    normalized_unit: Optional[str] = None
    normalized_value: float

    if suffix_lower in ("bps", "bp"):
        normalized_unit = "percentage"
        normalized_value = number
        scale = "ones"
    elif suffix == "%":
        normalized_unit = "percentage"
        normalized_value = number
        scale = "ones"
    elif suffix_lower == "x":
        normalized_unit = "multiple"
        normalized_value = number
        scale = "ones"
    elif suffix_lower.startswith("month"):
        normalized_unit = "unknown"
        normalized_value = number
        scale = "ones"
    elif unit_type == "percentage" or (unit_type == "percentage_or_bps" and "%" in text):
        normalized_unit = "percentage"
        normalized_value = number if suffix == "%" or "%" in text else number
        scale = "ones"
    elif unit_type == "count":
        normalized_unit = "count"
        normalized_value = number
    elif unit_type == "currency":
        normalized_unit = "currency"
        normalized_value = number
        currency = _detect_currency(
            groups["prefix_currency"] or "",
            text,
            raw_context,
            document_currency,
        )
    else:
        currency_pattern = rf"[\$ {GBP_SYMBOL}{EUR_SYMBOL}]|USD|GBP|CAD|EUR"
        if groups["prefix_currency"] or re.search(currency_pattern, text, re.IGNORECASE):
            normalized_unit = "currency"
            normalized_value = number
            currency = _detect_currency(
                groups["prefix_currency"] or "",
                text,
                raw_context,
                document_currency,
            )
        elif suffix == "%" or "%" in text:
            normalized_unit = "percentage"
            normalized_value = number
            scale = "ones"
        elif suffix_lower in ("b", "m", "mm", "million", "k", "thousand"):
            normalized_unit = unit_type or "unknown"
            normalized_value = number
        else:
            normalized_unit = unit_type or "unknown"
            normalized_value = number
            scale = "ones"

    return normalized_value, normalized_unit, scale, currency


_SCALE_DIVISORS = {
    "thousands": 1_000,
    "millions": 1_000_000,
    "billions": 1_000_000_000,
}


def to_display_scale(value: float, scale: str) -> float:
    """Convert absolute values to display scale when scale is set (e.g. 11200000 -> 11.2M)."""
    divisor = _SCALE_DIVISORS.get(scale)
    if divisor and abs(value) >= 1_000:
        return value / divisor
    return value


def infer_scale_from_raw_value(raw_value: Optional[str]) -> str:
    if not raw_value:
        return "unknown"
    match = VALUE_PATTERN.search(raw_value.strip())
    if not match:
        return "unknown"
    suffix = (match.group("suffix") or "").strip()
    scale = _suffix_to_scale(suffix)
    return scale if scale != "ones" else "unknown"
