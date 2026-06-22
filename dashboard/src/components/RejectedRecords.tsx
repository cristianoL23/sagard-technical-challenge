"use client";

import { formatMetricValue } from "@/lib/formatMetricValue";
import { NO_HUMAN_REJECTED_MESSAGE, type HumanRejectedRecord } from "@/types";

type Props = {
  records: HumanRejectedRecord[];
};

export function RejectedRecords({ records }: Props) {
  return (
    <section className="table-section rejected-records">
      <h2>Rejected Records</h2>
      <p className="review-subtitle">
        Metrics explicitly rejected during human review.
      </p>

      {records.length === 0 ? (
        <p className="muted">{NO_HUMAN_REJECTED_MESSAGE}</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Company</th>
                <th>Period</th>
                <th>Metric</th>
                <th>Source label</th>
                <th>Value</th>
                <th>Confidence</th>
                <th>Pipeline status</th>
                <th>Source file</th>
                <th>Page</th>
                <th>Raw text</th>
              </tr>
            </thead>
            <tbody>
              {records.map((row, i) => (
                <tr key={row.id ?? `${row.source_file}-${i}`}>
                  <td>{row.company_short_name}</td>
                  <td>
                    {row.quarter} {row.year}
                  </td>
                  <td>{row.metric_name}</td>
                  <td>{row.metric_label}</td>
                  <td>{formatMetricValue(row)}</td>
                  <td>{row.confidence.toFixed(2)}</td>
                  <td>{row.status}</td>
                  <td>{row.source_file}</td>
                  <td>{row.source_page ?? "—"}</td>
                  <td className="raw-cell">{row.raw_text ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
