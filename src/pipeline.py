from pathlib import Path
from typing import TypeVar

import typer
from rich import print

from src.company_identity import normalize_company_short_name, validate_company_identity
from src.config import CONFIDENCE_THRESHOLD, INPUT_PDF_DIR, OPENAI_API_KEY, OUTPUT_DIR
from src.llm_extract import extract_metrics_with_llm
from src.llm_identity import build_identity_candidate, extract_identity_with_llm
from src.models import ExtractionError, ExtractedMetric
from src.output import write_outputs, write_raw_metrics
from src.parse_pdf import parse_pdf_local
from src.validate import route_extractions

app = typer.Typer()

RecordWithCompany = TypeVar("RecordWithCompany", ExtractedMetric, ExtractionError)


def _normalize_company_fields(record: RecordWithCompany) -> RecordWithCompany:
    normalized = normalize_company_short_name(record.company_short_name)
    if normalized == record.company_short_name:
        return record
    return record.model_copy(update={"company_short_name": normalized})


@app.callback()
def main() -> None:
    """Portfolio metrics extraction pipeline."""


@app.command()
def run(
    input: Path = typer.Option(INPUT_PDF_DIR, help="Folder containing PDF files"),
    output_dir: Path = typer.Option(OUTPUT_DIR, help="Output folder"),
    confidence_threshold: float = typer.Option(
        CONFIDENCE_THRESHOLD,
        help="Minimum confidence for accepted metrics and identity",
    ),
):
    if not OPENAI_API_KEY:
        raise typer.BadParameter(
            "OPENAI_API_KEY is required. Configure .env before running the pipeline."
        )

    pdfs = sorted(input.glob("*.pdf"))
    if not pdfs:
        print(f"[yellow]Warning: no PDFs found in {input}[/yellow]")
        write_outputs([], [], output_dir)
        return

    all_candidates = []
    all_accepted = []
    all_rejected: list[ExtractionError] = []
    failed_parse_count = 0
    skipped_invalid_identity = 0
    processed_count = 0

    for pdf_path in pdfs:
        try:
            parsed = parse_pdf_local(pdf_path)
        except Exception as exc:
            failed_parse_count += 1
            print(f"[yellow]Warning: failed to parse {pdf_path.name}: {exc}[/yellow]")
            continue

        try:
            llm_payload = extract_identity_with_llm(parsed, pdf_path.name)
            candidate = build_identity_candidate(parsed, llm_payload)
            identity = validate_company_identity(
                candidate,
                parsed,
                pdf_path.name,
                confidence_threshold,
            )
        except Exception as exc:
            skipped_invalid_identity += 1
            print(
                f"[yellow]Warning: identity extraction failed for {pdf_path.name}: {exc}[/yellow]"
            )
            continue

        if identity is None:
            skipped_invalid_identity += 1
            print(
                f"[yellow]Warning: invalid identity for {pdf_path.name}; skipping[/yellow]"
            )
            continue

        print(
            f"Processing {pdf_path.name} — "
            f"{identity.company_short_name} / {identity.company_full_name or 'N/A'}"
        )

        try:
            candidates = extract_metrics_with_llm(parsed, identity)
        except Exception as exc:
            print(f"[yellow]Warning: LLM extraction failed for {pdf_path.name}: {exc}[/yellow]")
            all_rejected.append(
                _normalize_company_fields(
                    ExtractionError(
                        company_short_name=identity.company_short_name,
                        company_full_name=identity.company_full_name,
                        year=identity.year,
                        quarter=identity.quarter,
                        period_type=identity.period_type,
                        metric_name="other",
                        metric_label="",
                        source_file=parsed.source_file,
                        confidence=0.0,
                        status="llm_parse_error",
                        error_message=str(exc),
                    )
                )
            )
            continue

        all_candidates.extend(candidates)
        accepted, rejected = route_extractions(
            candidates,
            confidence_threshold,
            source_text=parsed.full_text,
        )
        all_accepted.extend(_normalize_company_fields(m) for m in accepted)
        all_rejected.extend(_normalize_company_fields(m) for m in rejected)

        print(
            f"  Extracted candidates: {len(candidates)} | "
            f"Accepted: {len(accepted)} | Rejected: {len(rejected)}"
        )
        processed_count += 1

    write_raw_metrics(all_candidates, output_dir)
    write_outputs(all_accepted, all_rejected, output_dir)

    if processed_count > 0 and not all_accepted:
        print("[yellow]Warning: PDFs processed but no metrics were accepted[/yellow]")

    print(f"Processed PDFs: {processed_count}")
    print(f"Skipped invalid identity PDFs: {skipped_invalid_identity}")
    print(f"Failed parse PDFs: {failed_parse_count}")
    print(f"Accepted metrics: {len(all_accepted)}")
    print(f"Rejected metrics: {len(all_rejected)}")
    print(f"Wrote outputs to {output_dir}")
    print(f"  metrics.csv, metrics.json, extraction_errors.csv, extraction_errors.json")


if __name__ == "__main__":
    app()
