import { withRecordIds } from "@/lib/recordId";
import type {
  ExtractionErrorRecord,
  HumanRejectedRecord,
  MetricRecord,
  ReviewRecord,
} from "@/types";

export async function loadDashboardData(): Promise<{
  metrics: MetricRecord[];
  pendingReview: ReviewRecord[];
  humanRejected: HumanRejectedRecord[];
}> {
  const [metricsRes, pendingRes, rejectedRes] = await Promise.all([
    fetch("/data/metrics.json"),
    fetch("/data/extraction_errors.json"),
    fetch("/data/human_rejected.json"),
  ]);

  const metrics = (await metricsRes.json()) as MetricRecord[];
  const pendingReview = withRecordIds(
    (await pendingRes.json()) as ExtractionErrorRecord[]
  ) as ReviewRecord[];
  const humanRejected = withRecordIds(
    (await rejectedRes.json()) as HumanRejectedRecord[]
  ) as HumanRejectedRecord[];

  return { metrics, pendingReview, humanRejected };
}
