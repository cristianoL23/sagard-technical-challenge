"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { MetricsToReview } from "@/components/MetricsToReview";
import { PortfolioOverview } from "@/components/PortfolioOverview";
import { RejectedRecords } from "@/components/RejectedRecords";
import { TrendCharts } from "@/components/TrendCharts";
import { MetricsTable } from "@/components/MetricsTable";
import { DEFAULT_FILTERS, applyFilters, filterOptions } from "@/lib/filters";
import { loadDashboardData } from "@/lib/loadDashboardData";
import type {
  FilterState,
  HumanRejectedRecord,
  MetricRecord,
  ReviewRecord,
} from "@/types";

export default function HomePage() {
  const [metrics, setMetrics] = useState<MetricRecord[]>([]);
  const [pendingReview, setPendingReview] = useState<ReviewRecord[]>([]);
  const [humanRejected, setHumanRejected] = useState<HumanRejectedRecord[]>([]);
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [loading, setLoading] = useState(true);

  const reloadData = useCallback(async () => {
    const data = await loadDashboardData();
    setMetrics(data.metrics);
    setPendingReview(data.pendingReview);
    setHumanRejected(data.humanRejected);
  }, []);

  useEffect(() => {
    reloadData().finally(() => setLoading(false));
  }, [reloadData]);

  const filteredMetrics = useMemo(
    () => applyFilters(metrics, filters),
    [metrics, filters]
  );

  const options = useMemo(() => filterOptions(metrics), [metrics]);

  if (loading) {
    return <main className="loading">Loading dashboard data…</main>;
  }

  return (
    <main>
      <header>
        <h1>Portfolio Metrics Dashboard</h1>
        <p>
          {metrics.length} accepted · {pendingReview.length} to review ·{" "}
          {humanRejected.length} rejected
        </p>
      </header>

      <PortfolioOverview
        allMetrics={metrics}
        pendingReview={pendingReview}
        filters={filters}
        filterOptions={options}
        onFiltersChange={setFilters}
      />
      <MetricsToReview records={pendingReview} onReviewComplete={reloadData} />
      <TrendCharts allMetrics={metrics} companyFilter={filters.company} />
      <MetricsTable metrics={filteredMetrics} />
      <RejectedRecords records={humanRejected} />
    </main>
  );
}
