"use client";

import { formatMetricValue } from "@/lib/formatMetricValue";
import type { MetricRecord } from "@/types";

type Props = {
  metrics: MetricRecord[];
};

export function MetricsTable({ metrics }: Props) {
  return (
    <section className="table-section">
      <h2>Accepted metrics</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Company</th>
              <th>Year</th>
              <th>Quarter</th>
              <th>Period</th>
              <th>Metric</th>
              <th>Source label</th>
              <th>Value</th>
              <th>Unit</th>
              <th>Scale</th>
              <th>Confidence</th>
              <th>Source file</th>
              <th>Page</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((row, i) => (
              <tr key={`${row.source_file}-${row.metric_name}-${i}`}>
                <td>{row.company_short_name}</td>
                <td>{row.year ?? "—"}</td>
                <td>{row.quarter ?? "—"}</td>
                <td>{row.period_type}</td>
                <td>{row.metric_name}</td>
                <td>{row.metric_label}</td>
                <td>{formatMetricValue(row)}</td>
                <td>{row.unit}</td>
                <td>{row.scale ?? "—"}</td>
                <td>{row.confidence.toFixed(2)}</td>
                <td>{row.source_file}</td>
                <td>{row.source_page ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {metrics.length === 0 && <p className="muted">No metrics match the current filters.</p>}
    </section>
  );
}
