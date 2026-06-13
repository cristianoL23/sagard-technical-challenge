"use client";

import { useEffect, useMemo, useState } from "react";

import { CompanyMetricView } from "@/components/CompanyMetricView";
import { ErrorRowsTable } from "@/components/ErrorRowsTable";
import { Filters } from "@/components/Filters";
import { MetricSummaryCards } from "@/components/MetricSummaryCards";
import { MetricsTable } from "@/components/MetricsTable";
import { EMPTY_FILTERS, applyFilters, filterOptions } from "@/lib/filters";
import { loadDashboardData } from "@/lib/loadDashboardData";
import type { ExtractionErrorRecord, FilterState, MetricRecord } from "@/types";

export default function HomePage() {
  const [metrics, setMetrics] = useState<MetricRecord[]>([]);
  const [errors, setErrors] = useState<ExtractionErrorRecord[]>([]);
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData()
      .then(({ metrics: m, errors: e }) => {
        setMetrics(m);
        setErrors(e);
      })
      .finally(() => setLoading(false));
  }, []);

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
          {metrics.length} accepted metrics · {errors.length} rejected records
        </p>
      </header>

      <Filters filters={filters} options={options} onChange={setFilters} />
      <MetricSummaryCards metrics={filteredMetrics} />
      <MetricsTable metrics={filteredMetrics} />
      <CompanyMetricView
        metrics={filteredMetrics}
        selectedCompany={filters.company}
      />
      <ErrorRowsTable errors={errors} />
    </main>
  );
}
