import fs from "fs";
import path from "path";

import { buildRecordId, findRecordById } from "@/lib/recordId";
import type {
  ExtractionErrorRecord,
  HumanRejectedRecord,
  MetricRecord,
} from "@/types";

export type ReviewDataPaths = {
  metricsFile: string;
  pendingFile: string;
  humanRejectedFile: string;
};

export function getReviewDataPaths(dataDir?: string): ReviewDataPaths {
  const baseDir = dataDir ?? path.join(process.cwd(), "public", "data");
  return {
    metricsFile: path.join(baseDir, "metrics.json"),
    pendingFile: path.join(baseDir, "extraction_errors.json"),
    humanRejectedFile: path.join(baseDir, "human_rejected.json"),
  };
}

function readJsonFile<T>(filePath: string): T[] {
  if (!fs.existsSync(filePath)) {
    return [];
  }
  return JSON.parse(fs.readFileSync(filePath, "utf-8")) as T[];
}

function writeJsonFile<T>(filePath: string, data: T[]): void {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, "utf-8");
}

export type ReviewCounts = {
  metricsCount: number;
  pendingCount: number;
  humanRejectedCount: number;
};

function toAcceptedMetric(record: ExtractionErrorRecord): MetricRecord {
  const {
    status: _status,
    error_message: _errorMessage,
    review_decision: _reviewDecision,
    id: _id,
    ...metric
  } = record as ExtractionErrorRecord & {
    review_decision?: string;
    id?: string;
  };

  if (metric.value == null) {
    throw new Error("Cannot accept a record without a numeric value");
  }

  return metric as MetricRecord;
}

function counts(
  metrics: MetricRecord[],
  pending: ExtractionErrorRecord[],
  humanRejected: HumanRejectedRecord[]
): ReviewCounts {
  return {
    metricsCount: metrics.length,
    pendingCount: pending.length,
    humanRejectedCount: humanRejected.length,
  };
}

export function acceptPendingRecord(id: string, dataDir?: string): ReviewCounts {
  const paths = getReviewDataPaths(dataDir);
  const metrics = readJsonFile<MetricRecord>(paths.metricsFile);
  const pending = readJsonFile<ExtractionErrorRecord>(paths.pendingFile);
  const humanRejected = readJsonFile<HumanRejectedRecord>(paths.humanRejectedFile);

  const record = findRecordById(pending, id);
  if (!record) {
    throw new Error("Record not found in review queue");
  }

  const nextPending = pending.filter((row) => buildRecordId(row) !== id);
  const nextMetrics = [...metrics, toAcceptedMetric(record)];

  writeJsonFile(paths.metricsFile, nextMetrics);
  writeJsonFile(paths.pendingFile, nextPending);

  return counts(nextMetrics, nextPending, humanRejected);
}

export function rejectPendingRecord(id: string, dataDir?: string): ReviewCounts {
  const paths = getReviewDataPaths(dataDir);
  const metrics = readJsonFile<MetricRecord>(paths.metricsFile);
  const pending = readJsonFile<ExtractionErrorRecord>(paths.pendingFile);
  const humanRejected = readJsonFile<HumanRejectedRecord>(paths.humanRejectedFile);

  const record = findRecordById(pending, id);
  if (!record) {
    throw new Error("Record not found in review queue");
  }

  const nextPending = pending.filter((row) => buildRecordId(row) !== id);
  const rejectedRecord: HumanRejectedRecord = {
    ...record,
    review_decision: "human_rejected",
  };
  const nextHumanRejected = [...humanRejected, rejectedRecord];

  writeJsonFile(paths.pendingFile, nextPending);
  writeJsonFile(paths.humanRejectedFile, nextHumanRejected);

  return counts(metrics, nextPending, nextHumanRejected);
}
