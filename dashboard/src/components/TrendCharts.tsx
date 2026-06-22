"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  formatAxisTick,
  metricYAxisLabel,
} from "@/lib/formatMetricValue";
import { buildTimeSeriesCharts, type TimeSeriesChart } from "@/lib/timeSeriesData";
import type { MetricRecord } from "@/types";

type Props = {
  allMetrics: MetricRecord[];
  companyFilter: string;
};

const COMPANY_COLORS = [
  "#2563eb",
  "#059669",
  "#dc2626",
  "#d97706",
  "#7c3aed",
  "#0891b2",
  "#db2777",
  "#4d7c0f",
  "#9333ea",
];

function MetricTrendChart({ chart }: { chart: TimeSeriesChart }) {
  const yLabel = metricYAxisLabel(chart.metricKey, chart.axisInfo);

  return (
    <div className="trend-chart">
      <h3>{chart.label}</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chart.data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e8ecf0" />
          <XAxis
            dataKey="period"
            tick={{ fontSize: 12, fill: "#5a6270" }}
            tickLine={{ stroke: "#ccd2d8" }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: "#5a6270" }}
            tickLine={{ stroke: "#ccd2d8" }}
            tickFormatter={(value) => formatAxisTick(Number(value), chart.axisInfo)}
            label={{
              value: yLabel,
              angle: -90,
              position: "insideLeft",
              style: { fill: "#5a6270", fontSize: 12 },
            }}
          />
          <Tooltip
            formatter={(value) =>
              value == null ? "—" : formatAxisTick(Number(value), chart.axisInfo)
            }
            contentStyle={{
              background: "#fff",
              border: "1px solid #e2e6ea",
              borderRadius: 6,
              fontSize: 13,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
          {chart.companies.map((company, index) => (
            <Line
              key={company}
              type="monotone"
              dataKey={company}
              name={company}
              stroke={COMPANY_COLORS[index % COMPANY_COLORS.length]}
              strokeWidth={2}
              dot={{ r: 3 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function TrendCharts({ allMetrics, companyFilter }: Props) {
  const charts = buildTimeSeriesCharts(allMetrics, companyFilter);

  if (charts.length === 0) {
    return (
      <section className="trend-charts">
        <h2>Trend Analysis</h2>
        <p className="muted">No time-series data available for the selected filters.</p>
      </section>
    );
  }

  return (
    <section className="trend-charts">
      <h2>Trend Analysis</h2>
      <p className="trend-subtitle">
        Quarter-over-quarter trends by company
        {companyFilter ? ` · ${companyFilter}` : ""}
      </p>
      <div className="trend-charts-grid">
        {charts.map((chart) => (
          <MetricTrendChart key={chart.metricKey} chart={chart} />
        ))}
      </div>
    </section>
  );
}
