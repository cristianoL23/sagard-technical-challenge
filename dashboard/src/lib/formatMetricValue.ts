import type { MetricRecord } from "@/types";

const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: "$",
  GBP: "£",
  EUR: "€",
  CAD: "C$",
};

function scaleSuffix(scale?: string): string {
  switch (scale) {
    case "thousands":
      return "K";
    case "millions":
      return "M";
    case "billions":
      return "B";
    default:
      return "";
  }
}

function formatNumber(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1000 && Number.isInteger(value)) {
    return abs.toLocaleString("en-US");
  }
  if (Number.isInteger(value)) {
    return String(value);
  }
  return abs.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

const SCALE_DIVISORS: Partial<Record<string, number>> = {
  thousands: 1_000,
  millions: 1_000_000,
  billions: 1_000_000_000,
};

/** Values should be stored in display scale (e.g. 4.5 with scale=millions). */
export function toDisplayValue(value: number, scale?: string): number {
  const divisor = scale ? SCALE_DIVISORS[scale] : undefined;
  if (!divisor || Math.abs(value) < 1_000) {
    return value;
  }
  return value / divisor;
}

export function formatMetricValue(record: MetricRecord): string {
  const { unit, scale, currency } = record;
  const value = toDisplayValue(record.value, scale);
  const suffix = scaleSuffix(scale);
  const symbol = currency ? CURRENCY_SYMBOLS[currency] ?? "" : "$";

  if (unit === "percentage") {
    const pct = value <= 1 && value >= -1 ? value * 100 : value;
    return `${pct.toLocaleString("en-US", { maximumFractionDigits: 1 })}%`;
  }

  if (unit === "count") {
    const formatted = formatNumber(value);
    return suffix ? `${formatted}${suffix}` : formatted;
  }

  if (unit === "currency") {
    const formatted = formatNumber(value);
    const core = suffix ? `${symbol}${formatted}${suffix}` : `${symbol}${formatted}`;
    return value < 0 ? `(${core.replace("-", "")})` : core;
  }

  if (unit === "multiple") {
    return `${formatNumber(value)}x`;
  }

  return formatNumber(value);
}

export function toChartValue(record: MetricRecord): number {
  const value = toDisplayValue(record.value, record.scale);
  if (record.unit === "percentage") {
    return value <= 1 && value >= -1 ? value * 100 : value;
  }
  return value;
}

export type MetricAxisInfo = {
  unit: string;
  scale?: string;
  currency?: string | null;
};

export function getMetricAxisInfo(
  metricName: string,
  metrics: MetricRecord[]
): MetricAxisInfo {
  const subset = metrics.filter((m) => m.metric_name === metricName);
  if (subset.length === 0) {
    return { unit: "unknown" };
  }

  const mode = <T,>(values: (T | null | undefined)[]): T | undefined => {
    const counts = new Map<string, number>();
    let best: T | undefined;
    let bestCount = 0;
    for (const value of values) {
      if (value == null || value === "") continue;
      const key = String(value);
      const count = (counts.get(key) ?? 0) + 1;
      counts.set(key, count);
      if (count > bestCount) {
        bestCount = count;
        best = value as T;
      }
    }
    return best;
  };

  return {
    unit: mode(subset.map((m) => m.unit)) ?? "unknown",
    scale: mode(subset.map((m) => m.scale)),
    currency: mode(subset.map((m) => m.currency)),
  };
}

export function metricYAxisLabel(metricName: string, info: MetricAxisInfo): string {
  if (info.unit === "percentage") return "%";
  if (info.unit === "currency") {
    const currencyCode = info.currency ?? "USD";
    if (info.scale && info.scale !== "ones" && info.scale !== "unknown") {
      return `${currencyCode} (${info.scale})`;
    }
    return currencyCode;
  }
  if (info.unit === "count") {
    if (info.scale && info.scale !== "ones" && info.scale !== "unknown") {
      return `count (${info.scale})`;
    }
    return "count";
  }
  return metricName.replace(/_/g, " ");
}

export function formatAxisTick(value: number, info: MetricAxisInfo): string {
  const symbol = info.currency ? CURRENCY_SYMBOLS[info.currency] ?? "$" : "$";
  const suffix = scaleSuffix(info.scale);

  if (info.unit === "percentage") {
    return `${value.toLocaleString("en-US", { maximumFractionDigits: 1 })}%`;
  }
  if (info.unit === "currency") {
    const formatted = value.toLocaleString("en-US", { maximumFractionDigits: 2 });
    return suffix ? `${symbol}${formatted}${suffix}` : `${symbol}${formatted}`;
  }
  if (info.unit === "count") {
    if (suffix) {
      return `${value.toLocaleString("en-US", { maximumFractionDigits: 2 })}${suffix}`;
    }
    if (Number.isInteger(value)) {
      return value.toLocaleString("en-US");
    }
    return value.toLocaleString("en-US", { maximumFractionDigits: 2 });
  }
  return value.toLocaleString("en-US", { maximumFractionDigits: 2 });
}
