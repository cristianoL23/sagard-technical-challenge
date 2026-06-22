"use client";

import type { FilterState } from "@/types";

type Options = {
  companies: string[];
  years: string[];
  quarters: string[];
};

type Props = {
  filters: FilterState;
  options: Options;
  onChange: (filters: FilterState) => void;
  embedded?: boolean;
};

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <label className="filter-field">
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">All</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </label>
  );
}

export function Filters({ filters, options, onChange, embedded = false }: Props) {
  const set = (key: keyof FilterState, value: string) =>
    onChange({ ...filters, [key]: value });

  const fields = (
    <div className="filters-grid">
      <SelectField
        label="Company"
        value={filters.company}
        options={options.companies}
        onChange={(v) => set("company", v)}
      />
      <SelectField
        label="Year"
        value={filters.year}
        options={options.years}
        onChange={(v) => set("year", v)}
      />
      <SelectField
        label="Quarter"
        value={filters.quarter}
        options={options.quarters}
        onChange={(v) => set("quarter", v)}
      />
    </div>
  );

  if (embedded) {
    return <div className="filters-embedded">{fields}</div>;
  }

  return (
    <section className="filters">
      <h2>Filters</h2>
      {fields}
    </section>
  );
}
