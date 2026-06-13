"use client";

import { NO_EXTRACTION_ERRORS_MESSAGE, type ExtractionErrorRecord } from "@/types";

type Props = {
  errors: ExtractionErrorRecord[];
};

export function ErrorRowsTable({ errors }: Props) {
  return (
    <section className="table-section">
      <h2>Extraction errors</h2>
      {errors.length === 0 ? (
        <p className="muted">{NO_EXTRACTION_ERRORS_MESSAGE}</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Company</th>
                <th>Metric</th>
                <th>Source label</th>
                <th>Value</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Error message</th>
                <th>Source file</th>
                <th>Page</th>
                <th>Raw text</th>
              </tr>
            </thead>
            <tbody>
              {errors.map((row, i) => (
                <tr key={`${row.source_file}-${i}`}>
                  <td>{row.company_short_name}</td>
                  <td>{row.metric_name}</td>
                  <td>{row.metric_label}</td>
                  <td>{row.value ?? "—"}</td>
                  <td>{row.confidence.toFixed(2)}</td>
                  <td>{row.status}</td>
                  <td>{row.error_message ?? "—"}</td>
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
