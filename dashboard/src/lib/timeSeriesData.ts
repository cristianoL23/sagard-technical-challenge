import { getMetricRow } from "@/lib/portfolioOverview";
import { getMetricAxisInfo, toChartValue, type MetricAxisInfo } from "@/lib/formatMetricValue";
import { OVERVIEW_TABLE_METRICS, type OverviewMetricKey } from "@/lib/portfolioOverview";
import type { MetricRecord } from "@/types";

const QUARTER_ORDER: Record<string, number> = { Q1: 1, Q2: 2, Q3: 3, Q4: 4 };

export type TimeSeriesPoint = {
  period: string;
  periodSort: number;
} & Record<string, string | number>;

export type TimeSeriesChart = {
  metricKey: OverviewMetricKey;
  label: string;
  axisInfo: MetricAxisInfo;
  companies: string[];
  data: TimeSeriesPoint[];
};

function periodSortKey(year: number, quarter: string): number {
  return year * 10 + (QUARTER_ORDER[quarter] ?? 0);
}

function formatPeriod(year: number, quarter: string): string {
  return `${year}-${quarter}`;
}

function getPeriods(metrics: MetricRecord[]): { year: number; quarter: string; periodSort: number }[] {
  const seen = new Map<string, { year: number; quarter: string; periodSort: number }>();

  for (const metric of metrics) {
    if (metric.period_type !== "quarter" || metric.year == null || !metric.quarter) {
      continue;
    }
    const key = `${metric.year}|${metric.quarter}`;
    if (!seen.has(key)) {
      seen.set(key, {
        year: metric.year,
        quarter: metric.quarter,
        periodSort: periodSortKey(metric.year, metric.quarter),
      });
    }
  }

  return [...seen.values()].sort((a, b) => a.periodSort - b.periodSort);
}

export function buildTimeSeriesCharts(
  allMetrics: MetricRecord[],
  companyFilter: string
): TimeSeriesChart[] {
  const quarterMetrics = allMetrics.filter(
    (m) => m.period_type === "quarter" && m.year != null && m.quarter
  );

  const periods = getPeriods(quarterMetrics);
  let companies = [...new Set(quarterMetrics.map((m) => m.company_short_name))].sort();

  if (companyFilter) {
    companies = companies.filter((company) => company === companyFilter);
  }

  return OVERVIEW_TABLE_METRICS.map(({ key, label }) => {
    const data: TimeSeriesPoint[] = periods.map(({ year, quarter, periodSort }) => {
      const point: TimeSeriesPoint = {
        period: formatPeriod(year, quarter),
        periodSort,
      };

      for (const company of companies) {
        const row = getMetricRow(allMetrics, company, year, quarter, key);
        if (row) {
          point[company] = toChartValue(row);
        }
      }

      return point;
    });

    const companiesWithData = companies.filter((company) =>
      data.some((point) => point[company] != null)
    );

    if (companiesWithData.length === 0) {
      return null;
    }

    const axisInfo = getMetricAxisInfo(key, quarterMetrics);

    return {
      metricKey: key,
      label,
      axisInfo,
      companies: companiesWithData,
      data,
    };
  }).filter((chart): chart is TimeSeriesChart => chart != null);
}
