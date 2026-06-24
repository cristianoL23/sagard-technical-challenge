import { excludePendingReviewMetrics, meetsConfidenceThreshold, selectPortfolioOverviewRows } from "@/lib/filters";
import { CARD_METRICS } from "@/types";
import type { ExtractionErrorRecord, FilterState, MetricRecord } from "@/types";

export type OverviewMetricKey = (typeof CARD_METRICS)[number];

export const OVERVIEW_TABLE_METRICS: { key: OverviewMetricKey; label: string }[] = [
  { key: "revenue", label: "Revenue" },
  { key: "arr", label: "ARR" },
  { key: "gross_margin", label: "Gross Margin" },
  { key: "net_retention", label: "Net Retention" },
  { key: "headcount", label: "Headcount" },
  { key: "monthly_burn", label: "Monthly Burn" },
];

export type CompanyOverviewRow = {
  company: string;
  metrics: Partial<Record<OverviewMetricKey, MetricRecord>>;
};

export function getMetricRow(
  metrics: MetricRecord[],
  company: string,
  year: number,
  quarter: string,
  metricName: string
): MetricRecord | undefined {
  const periodRows = metrics.filter(
    (m) =>
      m.company_short_name === company &&
      m.year === year &&
      m.quarter === quarter &&
      m.period_type === "quarter"
  );
  if (metricName === "revenue") {
    return selectPortfolioOverviewRows(periodRows, "revenue")[0];
  }
  return periodRows.find((m) => m.metric_name === metricName);
}

export function buildCompanyOverviewRows(
  allMetrics: MetricRecord[],
  filters: FilterState,
  pendingReview: ExtractionErrorRecord[] = []
): CompanyOverviewRow[] {
  const year = filters.year ? Number(filters.year) : null;
  const quarter = filters.quarter || null;
  const overviewMetrics = excludePendingReviewMetrics(allMetrics, pendingReview).filter(
    meetsConfidenceThreshold
  );

  const companies = [
    ...new Set(
      overviewMetrics
        .filter((m) => {
          if (filters.company && m.company_short_name !== filters.company) return false;
          if (year != null && m.year !== year) return false;
          if (quarter && m.quarter !== quarter) return false;
          return m.period_type === "quarter";
        })
        .map((m) => m.company_short_name)
    ),
  ].sort();

  return companies.map((company) => {
    const metrics: Partial<Record<OverviewMetricKey, MetricRecord>> = {};

    if (year != null && quarter) {
      for (const { key } of OVERVIEW_TABLE_METRICS) {
        const current = getMetricRow(overviewMetrics, company, year, quarter, key);
        if (current) {
          metrics[key] = current;
        }
      }
    }

    return { company, metrics };
  });
}
