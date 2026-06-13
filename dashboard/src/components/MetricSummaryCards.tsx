"use client";

import { selectPortfolioOverviewRows } from "@/lib/filters";
import { formatMetricValue } from "@/lib/formatMetricValue";
import { CARD_METRICS, type MetricRecord } from "@/types";

type Props = {
  metrics: MetricRecord[];
};

export function MetricSummaryCards({ metrics }: Props) {
  return (
    <section className="summary-cards">
      <h2>Portfolio overview</h2>
      <div className="cards-grid">
        {CARD_METRICS.map((metricName) => {
          const rows = selectPortfolioOverviewRows(metrics, metricName);
          return (
            <div key={metricName} className="card">
              <h3>{metricName.replace(/_/g, " ")}</h3>
              {rows.length === 0 ? (
                <p className="muted">No data</p>
              ) : (
                <ul>
                  {rows.slice(0, 6).map((row, i) => (
                    <li key={`${row.company_short_name}-${row.quarter}-${i}`}>
                      <strong>{row.company_short_name}</strong>{" "}
                      {row.quarter} {row.year}: {formatMetricValue(row)}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
