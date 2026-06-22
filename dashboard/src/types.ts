export type PeriodType = "quarter" | "ltm" | "current" | "ytd" | "unknown";
export type UnitType = "currency" | "percentage" | "count" | "multiple" | "unknown";
export type ScaleType = "ones" | "thousands" | "millions" | "billions" | "unknown";

export type MetricRecord = {
  id?: string;
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

export type HumanRejectedRecord = ExtractionErrorRecord & {
  review_decision: "human_rejected";
};

export const NO_PENDING_REVIEW_MESSAGE =
  "No metrics pending review. Pipeline-rejected records appear here for human approval.";

export const NO_HUMAN_REJECTED_MESSAGE =
  "No human-rejected records. Metrics explicitly rejected during review appear here.";

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

export type ReviewRecord = ExtractionErrorRecord & { id: string };
