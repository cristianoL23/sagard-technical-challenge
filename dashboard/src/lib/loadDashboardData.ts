import type { ExtractionErrorRecord, MetricRecord } from "@/types";

export async function loadDashboardData(): Promise<{
  metrics: MetricRecord[];
  errors: ExtractionErrorRecord[];
}> {
  const [metricsRes, errorsRes] = await Promise.all([
    fetch("/data/metrics.json"),
    fetch("/data/extraction_errors.json"),
  ]);

  const metrics = (await metricsRes.json()) as MetricRecord[];
  const errors = (await errorsRes.json()) as ExtractionErrorRecord[];

  return { metrics, errors };
}
