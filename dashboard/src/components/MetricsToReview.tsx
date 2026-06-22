"use client";

import { useState } from "react";

import { formatMetricValue } from "@/lib/formatMetricValue";
import { NO_PENDING_REVIEW_MESSAGE, type ReviewRecord } from "@/types";

type Props = {
  records: ReviewRecord[];
  onReviewComplete: () => Promise<void>;
};

function pdfHref(record: ReviewRecord): string {
  const base = `/pdfs/${encodeURIComponent(record.source_file)}`;
  if (record.source_page) {
    return `${base}#page=${record.source_page}`;
  }
  return base;
}

function ReviewCard({
  record,
  onReviewComplete,
}: {
  record: ReviewRecord;
  onReviewComplete: () => Promise<void>;
}) {
  const [loadingAction, setLoadingAction] = useState<"accept" | "reject" | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);

  async function submit(action: "accept" | "reject") {
    setLoadingAction(action);
    setError(null);

    try {
      const response = await fetch(`/api/review/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: record.id }),
      });

      if (!response.ok) {
        const payload = (await response.json()) as { error?: string };
        throw new Error(payload.error ?? `Failed to ${action} record`);
      }

      await onReviewComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action} record`);
    } finally {
      setLoadingAction(null);
    }
  }

  const lowConfidence = record.confidence < 0.5;

  return (
    <article className="review-card">
      <div className="review-card-header">
        <div>
          <h3>{record.company_short_name}</h3>
          <p className="review-meta">
            {record.quarter} {record.year} · {record.metric_name.replace(/_/g, " ")}
          </p>
        </div>
        <span className={`confidence-badge ${lowConfidence ? "low" : ""}`}>
          Confidence {record.confidence.toFixed(2)}
        </span>
      </div>

      <dl className="review-details">
        <div>
          <dt>Source label</dt>
          <dd>{record.metric_label}</dd>
        </div>
        <div>
          <dt>Value</dt>
          <dd>{formatMetricValue(record)}</dd>
        </div>
        <div>
          <dt>Pipeline status</dt>
          <dd>{record.status}</dd>
        </div>
        <div>
          <dt>Error message</dt>
          <dd>{record.error_message ?? "—"}</dd>
        </div>
        <div className="review-raw-text">
          <dt>Raw text</dt>
          <dd>{record.raw_text ?? "—"}</dd>
        </div>
      </dl>

      <div className="review-actions">
        <a
          className="pdf-link"
          href={pdfHref(record)}
          target="_blank"
          rel="noopener noreferrer"
        >
          View source PDF
          {record.source_page ? ` (page ${record.source_page})` : ""}
        </a>
        <div className="review-buttons">
          <button
            type="button"
            className="accept-button"
            disabled={loadingAction != null}
            onClick={() => submit("accept")}
          >
            {loadingAction === "accept" ? "Accepting…" : "Accept"}
          </button>
          <button
            type="button"
            className="reject-button"
            disabled={loadingAction != null}
            onClick={() => submit("reject")}
          >
            {loadingAction === "reject" ? "Rejecting…" : "Reject"}
          </button>
        </div>
      </div>

      {error && <p className="review-error">{error}</p>}
    </article>
  );
}

export function MetricsToReview({ records, onReviewComplete }: Props) {
  return (
    <section className="metrics-to-review">
      <h2>Metrics to Review</h2>
      <p className="review-subtitle">
        Pipeline-rejected metrics awaiting human approval. Accepted metrics appear in
        Portfolio Overview and Trend Analysis.
      </p>

      {records.length === 0 ? (
        <p className="muted">{NO_PENDING_REVIEW_MESSAGE}</p>
      ) : (
        <div className="review-list">
          {records.map((record) => (
            <ReviewCard
              key={record.id}
              record={record}
              onReviewComplete={onReviewComplete}
            />
          ))}
        </div>
      )}
    </section>
  );
}
