from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

PeriodType = Literal["quarter", "ltm", "current", "ytd", "unknown"]
UnitType = Literal["currency", "percentage", "count", "multiple", "unknown"]
ScaleType = Literal["ones", "thousands", "millions", "billions", "unknown"]
ErrorStatus = Literal[
    "low_confidence",
    "missing_source_text",
    "ambiguous_company",
    "unsupported_metric",
    "invalid_number",
    "llm_parse_error",
]


class AppModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ParsedPage(AppModel):
    page_number: int
    text: str
    tables: list[list[list[Optional[str]]]] = Field(default_factory=list)


class ParsedDocument(AppModel):
    source_file: str
    pages: list[ParsedPage]
    full_text: str
    metadata_title: Optional[str] = None


class CompanyIdentity(AppModel):
    company_short_name: str
    company_full_name: Optional[str] = None
    year: Optional[int] = None
    quarter: Optional[str] = None
    period_type: PeriodType = "unknown"
    source_file: str


class IdentityCandidate(AppModel):
    company_short_name: str
    company_full_name: str
    year: Optional[int] = None
    quarter: Optional[str] = None
    period_type: PeriodType = "unknown"
    source_file: str
    is_single_company_report: bool
    confidence: float = Field(ge=0, le=1)
    evidence_text: str


class ExtractedMetric(AppModel):
    company_short_name: str
    company_full_name: Optional[str] = None
    report_date: Optional[date] = None
    year: Optional[int] = None
    quarter: Optional[str] = None
    period_type: PeriodType = "unknown"
    metric_name: str
    metric_label: str
    value: Optional[float] = None
    unit: UnitType = "unknown"
    scale: ScaleType = "unknown"
    currency: Optional[str] = None
    source_file: str
    source_page: Optional[int] = None
    confidence: float = Field(ge=0, le=1)
    raw_text: Optional[str] = None


class ExtractionError(ExtractedMetric):
    status: ErrorStatus
    error_message: Optional[str] = None
