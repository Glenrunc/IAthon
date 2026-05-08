"""Tests for core.fec_writer."""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest

from core.fec_writer import (
    FEC_COLUMNS,
    FECValidationError,
    fec_filename,
    validate_fec_output,
    write_fec,
)


def test_write_fec_structure(sample_invoice, second_invoice):
    fec = write_fec([sample_invoice, second_invoice], siren="123456782", batch_date=date(2026, 5, 7))
    assert fec.startswith("﻿".encode("utf-8"))
    text = fec.decode("utf-8-sig")
    lines = [ln for ln in text.split("\r\n") if ln != ""]
    assert lines[0].split("|") == FEC_COLUMNS
    data = lines[1:]
    assert len(data) == 6  # 2 invoices × 3 lines
    for line in data:
        assert len(line.split("|")) == 18


def test_write_fec_balanced_per_ecriture(sample_invoice, second_invoice):
    fec = write_fec([sample_invoice, second_invoice], batch_date=date(2026, 5, 7))
    text = fec.decode("utf-8-sig")
    lines = [ln for ln in text.split("\r\n") if ln != ""][1:]
    sums: dict[str, list[Decimal]] = {}
    for line in lines:
        cols = line.split("|")
        row = dict(zip(FEC_COLUMNS, cols))
        ec = row["EcritureNum"]
        d = Decimal(row["Debit"].replace(",", ".")) if row["Debit"] else Decimal("0")
        c = Decimal(row["Credit"].replace(",", ".")) if row["Credit"] else Decimal("0")
        s = sums.setdefault(ec, [Decimal("0"), Decimal("0")])
        s[0] += d
        s[1] += c
    for ec, (debit, credit) in sums.items():
        assert debit == credit, f"EcritureNum {ec}: D={debit} != C={credit}"


def test_write_fec_dates_format(sample_invoice):
    fec = write_fec([sample_invoice], batch_date=date(2026, 5, 7))
    text = fec.decode("utf-8-sig")
    lines = [ln for ln in text.split("\r\n") if ln != ""][1:]
    for line in lines:
        cols = line.split("|")
        row = dict(zip(FEC_COLUMNS, cols))
        assert re.match(r"^\d{8}$", row["EcritureDate"])
        assert re.match(r"^\d{8}$", row["PieceDate"])
        assert re.match(r"^\d{8}$", row["ValidDate"])


def test_validate_fec_output_clean(sample_invoice, second_invoice):
    fec = write_fec([sample_invoice, second_invoice], batch_date=date(2026, 5, 7))
    assert validate_fec_output(fec) == []


def test_validate_fec_output_detects_imbalance():
    # Hand-craft a bad FEC: header + 1 line with non-zero debit only.
    header = "|".join(FEC_COLUMNS)
    bad_line = "ACH|Achats|1|20260507|6068|Autres achats||||20260507|Bad|10,00|0,00|||20260507||EUR"
    bad = ("﻿" + header + "\r\n" + bad_line + "\r\n").encode("utf-8")
    errors = validate_fec_output(bad)
    assert any("debit" in e.lower() and "credit" in e.lower() for e in errors)


def test_validate_fec_output_detects_wrong_columns():
    header = "|".join(FEC_COLUMNS[:-1])  # one column missing
    bad = ("﻿" + header + "\r\n").encode("utf-8")
    errors = validate_fec_output(bad)
    assert any("Header mismatch" in e for e in errors)


def test_fec_filename_format():
    assert fec_filename("123456782", date(2026, 5, 7)) == "FEC_123456782_20260507.txt"


def test_aux_num_stable_per_supplier(sample_invoice, second_invoice):
    # Two invoices same supplier_siret → same CompAuxNum
    duplicate = sample_invoice.model_copy()
    duplicate.invoice_number = "F-002"
    fec = write_fec([sample_invoice, duplicate, second_invoice], batch_date=date(2026, 5, 7))
    text = fec.decode("utf-8-sig")
    lines = [ln for ln in text.split("\r\n") if ln != ""][1:]
    aux_by_ecriture: dict[str, str] = {}
    for line in lines:
        cols = line.split("|")
        row = dict(zip(FEC_COLUMNS, cols))
        if row["CompAuxNum"]:
            aux_by_ecriture[row["EcritureNum"]] = row["CompAuxNum"]
    # Ecriture 1 and 2 share supplier → same aux. Ecriture 3 different supplier.
    assert aux_by_ecriture["1"] == aux_by_ecriture["2"] == "F00001"
    assert aux_by_ecriture["3"] == "F00002"


def test_write_fec_raises_on_empty(sample_invoice):
    # Sanity: empty list should still produce header (no validation error).
    fec = write_fec([], batch_date=date(2026, 5, 7))
    text = fec.decode("utf-8-sig")
    assert text.startswith("|".join(FEC_COLUMNS) + "\r\n") or text == "|".join(FEC_COLUMNS)


def test_write_fec_internal_validation_path():
    # Exercise the FECValidationError path via monkey-patched broken row.
    from core import fec_writer

    # Force validate_fec_output to report an error.
    with pytest.raises(FECValidationError):
        original = fec_writer.validate_fec_output
        try:
            fec_writer.validate_fec_output = lambda b: ["forced error"]  # type: ignore[assignment]
            fec_writer.write_fec([], batch_date=date(2026, 5, 7))
        finally:
            fec_writer.validate_fec_output = original
