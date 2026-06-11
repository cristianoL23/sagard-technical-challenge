"""Configuration and canonical metrics."""

import os
from pathlib import Path

PERIOD_PATTERNS = [
    r"Q([1-4])[_\s-]+(20\d{2})",
    r"(20\d{2})[_\s-]+Q([1-4])",
    r"Period:\s*Q([1-4])\s*(20\d{2})",
    r"Period Ended:\s*Q([1-4])\s*(20\d{2})",
    r"Quarter Ended:\s*Q([1-4])\s*(20\d{2})",
]

CANONICAL_METRICS = [
    "revenue",
    "arr",
    "gross_margin",
    "net_retention",
    "gross_retention",
    "logo_churn",
    "cash_balance",
    "headcount",
    "monthly_burn",
    "enterprise_logos",
    "paying_entities",
    "other",
]

METRIC_ALIASES = {
    "recognized revenue": "revenue",
    "quarterly revenue": "revenue",
    "net revenue": "revenue",
    "annual recurring revenue": "arr",
    "contracted arr": "arr",
    "gross margin": "gross_margin",
    "net dollar retention": "net_retention",
    "net revenue retention": "net_retention",
    "ndr": "net_retention",
    "nrr": "net_retention",
    "gross revenue retention": "gross_retention",
    "grr": "gross_retention",
    "logo churn": "logo_churn",
    "churn": "logo_churn",
    "cash": "cash_balance",
    "cash balance": "cash_balance",
    "cash & equivalents": "cash_balance",
    "cash and equivalents": "cash_balance",
    "cash & restricted cash": "cash_balance",
    "cash and restricted cash": "cash_balance",
    "fte": "headcount",
    "total headcount": "headcount",
    "monthly cash burn": "monthly_burn",
    "net burn": "monthly_burn",
    "burn": "monthly_burn",
    "enterprise logos": "enterprise_logos",
    "paying entities": "paying_entities",
}

PERIOD_TYPE_VALUES = ("quarter", "ltm", "current", "ytd", "unknown")
UNIT_TYPE_VALUES = ("currency", "percentage", "count", "multiple", "unknown")
SCALE_TYPE_VALUES = ("ones", "thousands", "millions", "billions", "unknown")
CURRENCY_CODES = ("USD", "GBP", "CAD", "EUR")

LLM_JSON_INSTRUCTIONS = "Return only valid JSON. Do not include markdown."

PERIOD_TYPES_PROMPT = ", ".join(PERIOD_TYPE_VALUES)
UNIT_TYPES_PROMPT = ", ".join(UNIT_TYPE_VALUES)
SCALE_TYPES_PROMPT = ", ".join(SCALE_TYPE_VALUES)
CURRENCIES_PROMPT = ", ".join(CURRENCY_CODES)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", os.getenv("LLM_MODEL", "gpt-4o-mini"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
INPUT_PDF_DIR = Path("data/raw")
OUTPUT_DIR = Path("output")
