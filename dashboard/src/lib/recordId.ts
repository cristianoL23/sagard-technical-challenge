type RecordIdInput = {
  source_file: string;
  metric_name: string;
  metric_label: string;
  raw_text?: string | null;
  value?: number | null;
};

function fnv1aHash(input: string): string {
  let hash = 2166136261;
  for (let i = 0; i < input.length; i++) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

export function buildRecordId(record: RecordIdInput): string {
  const parts = [
    record.source_file ?? "",
    record.metric_name ?? "",
    record.metric_label ?? "",
    record.raw_text ?? "",
    String(record.value ?? ""),
  ].join("|");

  return fnv1aHash(parts);
}

export function findRecordById<T extends RecordIdInput>(
  records: T[],
  id: string
): T | undefined {
  return records.find((record) => buildRecordId(record) === id);
}

export function withRecordIds<T extends RecordIdInput>(
  records: T[]
): (T & { id: string })[] {
  return records.map((record) => ({
    ...record,
    id: buildRecordId(record),
  }));
}
