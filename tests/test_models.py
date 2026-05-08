"""Tests for core.models."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from core.models import InvoiceData


def test_valid_invoice_constructs():
    inv = InvoiceData(
        supplier_name="Acme",
        supplier_siret="73282932000074",
        supplier_vat_number="FR44732829320",
        invoice_number="F-1",
        invoice_date=date(2026, 4, 15),
        amount_ht=Decimal("100.00"),
        amount_vat=Decimal("20.00"),
        amount_ttc=Decimal("120.00"),
        vat_rate=Decimal("20.0"),
        source_filename="x.pdf",
    )
    assert inv.supplier_siret == "73282932000074"
    assert inv.currency == "EUR"


def test_siret_invalid_luhn_raises():
    with pytest.raises(ValidationError):
        InvoiceData(
            supplier_name="Acme",
            supplier_siret="73282932000075",  # last digit flipped
            invoice_number="F-1",
            invoice_date=date(2026, 4, 15),
            amount_ht=Decimal("100"),
            amount_vat=Decimal("20"),
            amount_ttc=Decimal("120"),
            source_filename="x.pdf",
        )


def test_tva_invalid_pattern_raises():
    with pytest.raises(ValidationError):
        InvoiceData(
            supplier_name="Acme",
            supplier_vat_number="XX44732829320",  # not FR
            invoice_number="F-1",
            invoice_date=date(2026, 4, 15),
            amount_ht=Decimal("100"),
            amount_vat=Decimal("20"),
            amount_ttc=Decimal("120"),
            source_filename="x.pdf",
        )


def test_amounts_accept_str_float_decimal():
    inv = InvoiceData(
        supplier_name="Acme",
        invoice_number="F-1",
        invoice_date=date(2026, 4, 15),
        amount_ht="100.00",
        amount_vat=20.0,
        amount_ttc=Decimal("120"),
        source_filename="x.pdf",
    )
    assert inv.amount_ht == Decimal("100.00")
    assert inv.amount_vat == Decimal("20.0")
    assert inv.amount_ttc == Decimal("120")


def test_none_siret_and_tva_accepted():
    inv = InvoiceData(
        supplier_name="Acme",
        supplier_siret=None,
        supplier_vat_number=None,
        invoice_number="F-1",
        invoice_date=date(2026, 4, 15),
        amount_ht=Decimal("100"),
        amount_vat=Decimal("20"),
        amount_ttc=Decimal("120"),
        source_filename="x.pdf",
    )
    assert inv.supplier_siret is None
    assert inv.supplier_vat_number is None
