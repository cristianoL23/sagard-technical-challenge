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
function toDisplayValue(value: number, scale?: string): number {
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
