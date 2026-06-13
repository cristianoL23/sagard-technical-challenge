export type PeriodType = "quarter" | "ltm" | "current" | "ytd" | "unknown";
export type UnitType = "currency" | "percentage" | "count" | "multiple" | "unknown";
export type ScaleType = "ones" | "thousands" | "millions" | "billions" | "unknown";

export type MetricRecord = {
  company_short_name: string;
  company_full_name?: string | null;
  report_date?: string | null;
  year?: number | null;
  quarter?: string | null;
  period_type: PeriodType;
  metric_name: string;
  metric_label: string;
  value: number;
  unit: UnitType;
  scale?: ScaleType;
  currency?: string | null;
  source_file: string;
  source_page?: number | null;
  confidence: number;
  raw_text?: string | null;
};

export type ExtractionErrorRecord = MetricRecord & {
  status:
    | "low_confidence"
    | "missing_source_text"
    | "ambiguous_company"
    | "unsupported_metric"
    | "invalid_number"
    | "llm_parse_error";
  error_message?: string | null;
};

export const NO_EXTRACTION_ERRORS_MESSAGE =
  "No rejected records. Dashboard data was seeded from legacy regex extraction output, which did not produce an errors file.";

export const CARD_METRICS = [
  "revenue",
  "arr",
  "gross_margin",
  "net_retention",
  "headcount",
  "monthly_burn",
];

export type FilterState = {
  company: string;
  year: string;
  quarter: string;
};
