"""Tests for core.confidence."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from core.confidence import _luhn, _validate_fr_tva, score
from core.models import InvoiceData


def test_luhn_valid():
    assert _luhn("73282932000074") is True


def test_luhn_invalid():
    assert _luhn("73282932000075") is False


def test_luhn_non_digits():
    assert _luhn("abc") is False


def test_fr_tva_valid():
    # SIREN 732829320 → key (12 + 3*(732829320 % 97)) % 97 = 44
    assert _validate_fr_tva("FR44732829320") is True


def test_fr_tva_invalid_key():
    assert _validate_fr_tva("FR45732829320") is False


def test_fr_tva_bad_format():
    assert _validate_fr_tva("XX44732829320") is False


def test_score_balanced_amounts():
    inv = InvoiceData(
        supplier_name="A",
        supplier_siret="73282932000074",
        supplier_vat_number="FR44732829320",
        invoice_number="F-1",
        invoice_date=date(2026, 1, 1),
        amount_ht=Decimal("100"),
        amount_vat=Decimal("20"),
        amount_ttc=Decimal("120"),
        source_filename="x.pdf",
    )
    s = score(inv)
    assert s["amount_ht"] == 1.0
    assert s["amount_vat"] == 1.0
    assert s["amount_ttc"] == 1.0
    assert s["supplier_siret"] == 1.0
    assert s["supplier_vat_number"] == 1.0
    assert s["invoice_date"] == 1.0


def test_score_unbalanced_amounts():
    inv = InvoiceData(
        supplier_name="A",
        invoice_number="F-1",
        invoice_date=date(2026, 1, 1),
        amount_ht=Decimal("100"),
        amount_vat=Decimal("20"),
        amount_ttc=Decimal("125"),
        source_filename="x.pdf",
    )
    s = score(inv)
    assert s["amount_ht"] == 0.5
    assert s["amount_vat"] == 0.5
    assert s["amount_ttc"] == 0.5


def test_score_none_siret_treated_as_full_confidence():
    inv = InvoiceData(
        supplier_name="A",
        supplier_siret=None,
        invoice_number="F-1",
        invoice_date=date(2026, 1, 1),
        amount_ht=Decimal("100"),
        amount_vat=Decimal("20"),
        amount_ttc=Decimal("120"),
        source_filename="x.pdf",
    )
    s = score(inv)
    assert s["supplier_siret"] == 1.0
    assert s["supplier_vat_number"] == 1.0
