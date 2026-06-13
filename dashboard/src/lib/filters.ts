import type { FilterState, MetricRecord } from "@/types";

export const EMPTY_FILTERS: FilterState = {
  company: "",
  year: "",
  quarter: "",
};

export function applyFilters(metrics: MetricRecord[], filters: FilterState): MetricRecord[] {
  return metrics.filter((m) => {
    if (filters.company && m.company_short_name !== filters.company) return false;
    if (filters.year && String(m.year ?? "") !== filters.year) return false;
    if (filters.quarter && (m.quarter ?? "") !== filters.quarter) return false;
    return true;
  });
}

export function uniqueSorted(values: (string | number | null | undefined)[]): string[] {
  return [...new Set(values.filter((v) => v != null && v !== "").map(String))].sort();
}

export function filterOptions(metrics: MetricRecord[]) {
  return {
    companies: uniqueSorted(metrics.map((m) => m.company_short_name)),
    years: uniqueSorted(metrics.map((m) => m.year)),
    quarters: uniqueSorted(metrics.map((m) => m.quarter)),
  };
}

function portfolioPeriodKey(metric: MetricRecord): string {
  return `${metric.company_short_name}|${metric.year ?? ""}|${metric.quarter ?? ""}|${metric.period_type}`;
}

/** Prefer Total Recognized Revenue when a company has multiple revenue rows. */
export function selectPortfolioOverviewRows(
  metrics: MetricRecord[],
  metricName: string
): MetricRecord[] {
  const rows = metrics.filter((m) => m.metric_name === metricName);
  if (metricName !== "revenue") {
    return rows;
  }

  const byPeriod = new Map<string, MetricRecord[]>();
  for (const row of rows) {
    const key = portfolioPeriodKey(row);
    const group = byPeriod.get(key) ?? [];
    group.push(row);
    byPeriod.set(key, group);
  }

  const selected: MetricRecord[] = [];
  for (const group of byPeriod.values()) {
    const totalRevenue = group.find(
      (row) => row.metric_label.trim().toLowerCase() === "total recognized revenue"
    );
    selected.push(...(totalRevenue ? [totalRevenue] : group));
  }

  return selected;
}
