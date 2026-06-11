from pathlib import Path
from typing import Optional

import pdfplumber

from src.models import ParsedDocument, ParsedPage


def _clean_cell(cell: Optional[str]) -> str:
    if cell is None:
        return ""
    return str(cell).strip()


def parse_pdf_local(pdf_path: Path) -> ParsedDocument:
    pages: list[ParsedPage] = []
    metadata_title: Optional[str] = None

    with pdfplumber.open(pdf_path) as pdf:
        if pdf.metadata and pdf.metadata.get("Title"):
            metadata_title = str(pdf.metadata["Title"]).strip() or None

        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            raw_tables = page.extract_tables() or []
            tables = [
                [[_clean_cell(cell) for cell in row] for row in table]
                for table in raw_tables
            ]
            pages.append(
                ParsedPage(
                    page_number=index,
                    text=text,
                    tables=tables,
                )
            )

    return ParsedDocument(
        source_file=pdf_path.name,
        pages=pages,
        full_text="\n\n".join(page.text for page in pages),
        metadata_title=metadata_title,
    )
