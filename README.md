# PME AI Toolkit

**Facture → FEC. De la facture papier à l'écriture comptable en un clic.**

PME AI Toolkit extracts structured data from French invoices (PDF or image) using
Gemini Vision, validates it through a Pydantic schema, and exports a legally
compliant FEC file ready for import into Sage, EBP, Cegid, or Pennylane.

## Quickstart

```bash
uv sync
cp .env.example .env   # add your GOOGLE_API_KEY
uv run streamlit run app.py
```

Open http://localhost:8501, upload invoices, review extracted fields, then export FEC.

## Demo dataset

`data/samples/` contains 10 sample French invoices for testing.

## Tests

```bash
uv run pytest tests/ -v
```

## Tech stack

Python 3.11 · Streamlit · Gemini 2.5 Flash · Pydantic · SQLite

## Roadmap

See spec for V2/V3 roadmap.
