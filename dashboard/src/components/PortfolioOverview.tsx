"use client";

import { Filters } from "@/components/Filters";
import {
  OVERVIEW_TABLE_METRICS,
  buildCompanyOverviewRows,
  type CompanyOverviewRow,
  type OverviewMetricKey,
} from "@/lib/portfolioOverview";
import { formatMetricValue } from "@/lib/formatMetricValue";
import type { FilterState, MetricRecord } from "@/types";

type FilterOptions = {
  companies: string[];
  years: string[];
  quarters: string[];
};

type Props = {
  allMetrics: MetricRecord[];
  filters: FilterState;
  filterOptions: FilterOptions;
  onFiltersChange: (filters: FilterState) => void;
};

function MetricCell({
  row,
  metricKey,
}: {
  row: CompanyOverviewRow;
  metricKey: OverviewMetricKey;
}) {
  const record = row.metrics[metricKey];
  if (!record) {
    return <span className="muted-dash">—</span>;
  }
  return <span className="metric-value">{formatMetricValue(record)}</span>;
}

export function PortfolioOverview({
  allMetrics,
  filters,
  filterOptions,
  onFiltersChange,
}: Props) {
  const period =
    filters.quarter && filters.year
      ? `${filters.quarter} ${filters.year}`
      : filters.year || "All periods";

  const rows = buildCompanyOverviewRows(allMetrics, filters);

  return (
    <section className="portfolio-overview">
      <h2>Portfolio Overview</h2>
      <Filters
        embedded
        filters={filters}
        options={filterOptions}
        onChange={onFiltersChange}
      />

      <div className="company-metrics-panel">
        <div className="panel-header">
          <h3>{period} Company Metrics</h3>
        </div>
        <div className="table-wrap">
          <table className="company-metrics-table">
            <thead>
              <tr>
                <th>Company</th>
                {OVERVIEW_TABLE_METRICS.map(({ key, label }) => (
                  <th key={key}>{label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={OVERVIEW_TABLE_METRICS.length + 1} className="empty-row">
                    No companies match the current filters.
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={row.company}>
                    <td className="company-cell">
                      <span className="company-name">{row.company}</span>
                    </td>
                    {OVERVIEW_TABLE_METRICS.map(({ key }) => (
                      <td key={key}>
                        <MetricCell row={row} metricKey={key} />
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
