"""Map LLM response strings to canonical model types."""

from typing import Optional

from src.config import CURRENCY_CODES, PERIOD_TYPE_VALUES, SCALE_TYPE_VALUES, UNIT_TYPE_VALUES
from src.models import PeriodType, ScaleType, UnitType

_KNOWN_UNITS = frozenset(UNIT_TYPE_VALUES) - {"unknown"}
_KNOWN_SCALES = frozenset(SCALE_TYPE_VALUES)
_CURRENCY_CODES = frozenset(code.lower() for code in CURRENCY_CODES)


def map_period_type(period_type: Optional[str]) -> PeriodType:
    if not period_type:
        return "unknown"
    pt = period_type.lower()
    if pt in PERIOD_TYPE_VALUES:
        return pt  # type: ignore[return-value]
    return "unknown"


def map_unit(unit: Optional[str]) -> UnitType:
    if not unit:
        return "unknown"
    unit_lower = unit.lower()
    if unit_lower in _KNOWN_UNITS:
        return unit_lower  # type: ignore[return-value]
    if unit_lower in _CURRENCY_CODES:
        return "currency"
    if unit_lower == "%":
        return "percentage"
    return "unknown"


def map_scale(scale: Optional[str]) -> ScaleType:
    if not scale:
        return "unknown"
    scale_lower = scale.lower()
    if scale_lower in _KNOWN_SCALES:
        return scale_lower  # type: ignore[return-value]
    return "unknown"
