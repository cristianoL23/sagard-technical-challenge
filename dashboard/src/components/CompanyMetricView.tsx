"use client";

import { formatMetricValue } from "@/lib/formatMetricValue";
import type { MetricRecord } from "@/types";

type Props = {
  metrics: MetricRecord[];
  selectedCompany: string;
};

function quarterSortKey(row: MetricRecord): string {
  return `${row.year ?? 0}-${row.quarter ?? ""}`;
}

export function CompanyMetricView({ metrics, selectedCompany }: Props) {
  const companyMetrics = metrics
    .filter((m) => m.company_short_name === selectedCompany)
    .sort((a, b) => quarterSortKey(a).localeCompare(quarterSortKey(b)));

  const byMetric = companyMetrics.reduce<Record<string, MetricRecord[]>>((acc, row) => {
    acc[row.metric_name] = acc[row.metric_name] ?? [];
    acc[row.metric_name].push(row);
    return acc;
  }, {});

  if (!selectedCompany) {
    return (
      <section className="company-view">
        <h2>Company detail</h2>
        <p className="muted">Select a company filter to see detail.</p>
      </section>
    );
  }

  return (
    <section className="company-view">
      <h2>Company detail — {selectedCompany}</h2>
      {Object.keys(byMetric).length === 0 ? (
        <p className="muted">No metrics for this company.</p>
      ) : (
        Object.entries(byMetric).map(([metricName, rows]) => (
          <div key={metricName} className="company-metric-group">
            <h3>{metricName.replace(/_/g, " ")}</h3>
            <ul>
              {rows.map((row, i) => (
                <li key={`${metricName}-${i}`}>
                  {row.quarter} {row.year}: {formatMetricValue(row)}{" "}
                  <span className="muted">
                    ({row.metric_label}, conf {row.confidence.toFixed(2)}, {row.source_file})
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))
      )}
    </section>
  );
}
