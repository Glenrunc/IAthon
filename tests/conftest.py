"""Shared test fixtures."""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from core.models import InvoiceData


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _generate_test_pdf(path: Path) -> None:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica", 14)
    c.drawString(100, 800, "FACTURE TEST")
    c.drawString(100, 770, "Fournisseur: Acme SARL")
    c.drawString(100, 740, "SIRET: 73282932000074")
    c.drawString(100, 710, "Numero: F-2026-001")
    c.drawString(100, 680, "Date: 2026-04-15")
    c.drawString(100, 650, "Montant HT: 100,00 EUR")
    c.drawString(100, 620, "TVA 20%: 20,00 EUR")
    c.drawString(100, 590, "Montant TTC: 120,00 EUR")
    c.showPage()
    c.save()
    path.write_bytes(buf.getvalue())


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = FIXTURES_DIR / "test.pdf"
    if not pdf_path.exists():
        _generate_test_pdf(pdf_path)
    json_path = FIXTURES_DIR / "sample_invoice.json"
    if not json_path.exists():
        json_path.write_text(
            json.dumps(
                {
                    "supplier_name": "Acme SARL",
                    "supplier_siret": "73282932000074",
                    "supplier_vat_number": "FR44732829320",
                    "invoice_number": "F-2026-001",
                    "invoice_date": "2026-04-15",
                    "amount_ht": 100.0,
                    "amount_vat": 20.0,
                    "amount_ttc": 120.0,
                    "vat_rate": 20.0,
                },
                indent=2,
            ),
            encoding="utf-8",
        )


@pytest.fixture
def sample_invoice() -> InvoiceData:
    return InvoiceData(
        supplier_name="Acme SARL",
        supplier_siret="73282932000074",
        supplier_vat_number="FR44732829320",
        invoice_number="F-2026-001",
        invoice_date=date(2026, 4, 15),
        amount_ht=Decimal("100.00"),
        amount_vat=Decimal("20.00"),
        amount_ttc=Decimal("120.00"),
        vat_rate=Decimal("20.0"),
        source_filename="test.pdf",
    )


@pytest.fixture
def second_invoice() -> InvoiceData:
    return InvoiceData(
        supplier_name="Beta SAS",
        supplier_siret=None,
        supplier_vat_number=None,
        invoice_number="B-9",
        invoice_date=date(2026, 4, 20),
        amount_ht=Decimal("50.00"),
        amount_vat=Decimal("5.00"),
        amount_ttc=Decimal("55.00"),
        vat_rate=Decimal("10.0"),
        source_filename="other.pdf",
    )


@pytest.fixture
def fixture_pdf_bytes() -> bytes:
    return (FIXTURES_DIR / "test.pdf").read_bytes()
