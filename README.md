# Sagard Technical Challenge — Portfolio Metrics Extraction

Technical challenge to build a POC crawl that extracts metrics from PDf reports.

## Requirements

- Python 3.9+
- Pydantic v2
- Node.js 18+ (dashboard only)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Place PDFs in `data/raw/` 

The sample PDFs from the Google Drive are already included

Add `OPENAI_API_KEY` in `.env` to run the extraction pipeline. The dashboard, review notebook, and tests can be run without an `OPENAI_API_KEY` using the committed data in `output/`.

---

## Run without API key

Use this path to see the dashboard, review notebook, and run tests. No network access or OpenAI account required.

### 1. Install Python dependencies

Follow steps in Setup section above

Skip setting `OPENAI_API_KEY` in `.env`.

### 2. Dashboard

The repo contains committed pipeline outputs in `output/`. Sync them into the dashboard and start the dev server:

```bash
python scripts/sync_dashboard_data.py
cd dashboard
npm install
npm run dev
```

Open http://localhost:3000

### 3. Review notebook

```bash
jupyter notebook notebooks/extraction_review.ipynb
```

Reads from `../output/` (`metrics.csv`, `extraction_errors.csv`, `metrics_wide.csv`).

### 4. Tests

```bash
pytest
```

---

## Run with API key

Use this path to regenerate extraction outputs from the sample PDFs via the LLM pipeline.

### 1. Configure API key

Add your key to `.env`:

```bash
OPENAI_API_KEY=sk-...
```

Other defaults in `.env.example` (`OPENAI_MODEL`, `CONFIDENCE_THRESHOLD`, etc.) can be left as-is.

### 2. Run the extraction pipeline

```bash
python -m src.pipeline run --input data/raw --output-dir output
```

Options: Setting custom confidence threshold

```bash
python -m src.pipeline run --confidence-threshold 0.6  # custom threshold
```

`OPENAI_API_KEY` is required for every pipeline run (identity + metrics extraction).

### 3. Sync dashboard data

```bash
python scripts/sync_dashboard_data.py
cd dashboard && npm install && npm run dev
```

### 4. Review results

```bash
jupyter notebook notebooks/extraction_review.ipynb
```

---

## Approach

`pipeline.py` runs the pipeline for extracting the metrics from PDFs
`parse_pdf.py` reads the PDF and gets the title, number of pages and text using pdfpumber. Output  used in the LLM extraction
`llm_client.py` generic call to Open AI 
`llm_identity.py` LLM prompt to get the company name and quarter info
`llm_extract.py` LLM prompt to get the metrics
`llM_parsing.py`, `normalize.py`, `validate.py` used to normalize data to include formatting and validation of data with the PDF contents
`output.py` output the normalized data to the CSV in `/output` 
- `metrics.csv` / `metrics.json` — accepted metrics (confidence >= threshold, valid)
- `extraction_errors.csv` / `extraction_errors.json` — rejected metrics
- `metrics_wide.csv` — pivoted accepted metrics
- `raw_metrics.json` — all LLM candidates before routing
`scripts/sync_dashboard_data.py` copies output to be rendered in the dashboard


Chose to use an LLM as can deal with the ambiguity of incosistent formatting, labels, names for financial concepts to be accounted for better than using large hardcoded datasets and regex.

The LLM assigns confidence 0–1. Python accepts a metric when:

```text
confidence >= 0.5 (configurable)
AND value is valid
AND metric_name is supported
AND raw_text is grounded in the PDF
AND schema validation passes
```

Normalization and validation steps needed to ensure that extracted metric truly is present in the PDF and the LLM is not hallucinating


Rejected statuses: `low_confidence`, `missing_source_text`, `ambiguous_company`, `unsupported_metric`, `invalid_number`, `llm_parse_error`.

## Assumptions

- Sample PDFs contain extractable text.
- Company identity is extracted via LLM and verified (confidence, grounding, single-company flag, period cross-check).
- Multi-company or portfolio summary PDFs are skipped when identity validation fails.
- Missing metrics are blank, not errors.
- Dashboard demo data is synced from committed `output/metrics.json`.
- ApexFreight (rebrand of FleetLink) contains the data from both ApexFreight and FleetLink reports

## Limitations

- LLM extraction requires API key and network access.
- No OCR for scanned PDFs.
- Currency normalization is basic (no FX conversion).

## Next steps / Improvements

- change LLM client to use another LLM if desired
- Use an OCR tool designed for reading documents such as Azure Document Intelligence / Google Document AI 
- Turn existing pieces of pipeline into reusable tool calls
- Flag uncertain metrics for human review in a dashboard
- Use RAG to have company-specific metrics defined in a doc / vector DB
- cron job to run the pipeline each quarter and save metrics in DB 
