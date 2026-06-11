import json
from pathlib import Path

import pandas as pd

from src.models import ExtractedMetric, ExtractionError

METRIC_COLUMNS = list(ExtractedMetric.model_fields.keys())
ERROR_COLUMNS = list(ExtractionError.model_fields.keys())
WIDE_INDEX_COLUMNS = ["company_short_name", "year", "quarter", "period_type"]


def _metric_to_dict(row: ExtractedMetric) -> dict:
    data = row.model_dump()
    if data.get("report_date") is not None:
        data["report_date"] = str(data["report_date"])
    return {col: data.get(col) for col in METRIC_COLUMNS}


def _error_to_dict(row: ExtractionError) -> dict:
    data = row.model_dump()
    if data.get("report_date") is not None:
        data["report_date"] = str(data["report_date"])
    return {col: data.get(col) for col in ERROR_COLUMNS}


def _build_wide_dataframe(accepted: list[ExtractedMetric]) -> pd.DataFrame:
    if not accepted:
        return pd.DataFrame(columns=WIDE_INDEX_COLUMNS)

    records: dict[tuple, dict] = {}
    for row in accepted:
        key = tuple(getattr(row, col) for col in WIDE_INDEX_COLUMNS)
        if key not in records:
            records[key] = {col: getattr(row, col) for col in WIDE_INDEX_COLUMNS}
        records[key][row.metric_name] = row.value

    wide_df = pd.DataFrame(records.values())
    wide_df = wide_df.sort_values(WIDE_INDEX_COLUMNS, na_position="last")
    return wide_df.reset_index(drop=True)


def write_raw_metrics(metrics: list[ExtractedMetric], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "raw_metrics.json"
    records = [_metric_to_dict(m) for m in metrics]
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")


def write_outputs(
    accepted: list[ExtractedMetric],
    rejected: list[ExtractionError],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    accepted_records = [_metric_to_dict(r) for r in accepted]
    rejected_records = [_error_to_dict(r) for r in rejected]

    metrics_df = pd.DataFrame(accepted_records, columns=METRIC_COLUMNS)
    errors_df = pd.DataFrame(rejected_records, columns=ERROR_COLUMNS)
    wide_df = _build_wide_dataframe(accepted)

    metrics_df.to_csv(output_dir / "metrics.csv", index=False, encoding="utf-8")
    errors_df.to_csv(output_dir / "extraction_errors.csv", index=False, encoding="utf-8")
    wide_df.to_csv(output_dir / "metrics_wide.csv", index=False, encoding="utf-8")

    (output_dir / "metrics.json").write_text(
        json.dumps(accepted_records, indent=2), encoding="utf-8"
    )
    (output_dir / "extraction_errors.json").write_text(
        json.dumps(rejected_records, indent=2), encoding="utf-8"
    )
