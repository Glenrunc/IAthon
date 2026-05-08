# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
uv sync
cp .env.example .env   # add GOOGLE_API_KEY

# Run app
uv run streamlit run app.py

# Tests
uv run pytest tests/ -v
uv run pytest tests/test_fec_writer.py -v   # single test file
uv run pytest -k test_write_fec             # single test by name
```

## Architecture

Single-page Streamlit app that converts French invoices (PDF/image) to FEC accounting files.

**Data flow:** PDF/image upload → Gemini Vision extraction → Pydantic validation → SQLite persistence → review table → FEC export

**Core modules (`core/`):**
- `models.py` — `InvoiceData` Pydantic model with SIRET (Luhn) and TVA (`FRXX...`) validators
- `extractor.py` — calls Gemini Vision (`gemini-2.5-flash`) with a French prompt, strips JSON fences, validates against `InvoiceData`. Defines a `Provider` Protocol so tests can inject a mock. Exception hierarchy: `ExtractionError` → `MissingKeyError / RateLimitError / NetworkError / JsonParseError / SchemaValidationError`
- `confidence.py` — rule-based per-field scores in `[0.0, 1.0]`; flags amount imbalance (`HT + VAT ≠ TTC ± 0.01`) and checksum failures
- `fec_writer.py` — generates FEC (Article A47 A-1 LPF): UTF-8 BOM, CRLF, pipe-delimited, 3 journal lines per invoice (6068 debit HT / 44566 debit TVA / 401 credit TTC). Internally validates debit=credit balance before returning bytes
- `storage.py` — SQLite at `data/app.db`; amounts stored as strings (no float rounding), confidence as JSON blob

**UI modules (`ui/`):** `upload.py`, `review.py`, `export.py` — called from `app.py`

**Prompt:** `prompts/invoice_extraction.fr.md` — French-language system prompt sent to Gemini alongside the file bytes

**Session state keys:** `batch_id`, `invoices` (list of `(invoice_id, InvoiceData)`), `batch_siren`, `_processing`, `_just_exported`

## Key constraints

- All UI copy is in French
- FEC format is legally mandated; do not change column order or delimiters (`FEC_COLUMNS` in `fec_writer.py`)
- `amount_ht + amount_vat` must equal `amount_ttc` within €0.01 — the confidence scorer flags deviations and the FEC writer validates debit/credit balance
- `update_invoice_field` in `storage.py` uses a whitelist (`_INVOICE_COLUMNS`) to prevent SQL injection via field names
- `MistralProvider` exists as a stub but is not used in V1
