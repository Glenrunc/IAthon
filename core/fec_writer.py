"""FEC (Fichier des Écritures Comptables) writer per Article A47 A-1 LPF."""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import Optional

from core.models import InvoiceData


FEC_COLUMNS = [
    "JournalCode",
    "JournalLib",
    "EcritureNum",
    "EcritureDate",
    "CompteNum",
    "CompteLib",
    "CompAuxNum",
    "CompAuxLib",
    "PieceRef",
    "PieceDate",
    "EcritureLib",
    "Debit",
    "Credit",
    "EcritureLet",
    "DateLet",
    "ValidDate",
    "Montantdevise",
    "Idevise",
]
_NUM_COLS = len(FEC_COLUMNS)
_DELIM = "|"
_LINE_SEP = "\r\n"
_BOM = "﻿"

_JOURNAL_CODE = "ACH"
_JOURNAL_LIB = "Achats"
_COMPTE_HT = ("6068", "Autres achats")
_COMPTE_TVA = ("44566", "TVA déductible")
_COMPTE_FOURN = ("401", "Fournisseurs")

_DATE_RE = re.compile(r"^\d{8}$")


class FECValidationError(Exception):
    """Raised when generated FEC fails internal validation."""


def _fmt_date(d: date) -> str:
    return d.strftime("%Y%m%d")


def _fmt_amount(value: Decimal) -> str:
    """2-decimal, comma separator, no thousands separator."""
    q = value.quantize(Decimal("0.01"))
    return f"{q:.2f}".replace(".", ",")


def _aux_map(invoices: list[InvoiceData]) -> dict[str, str]:
    """Build supplier_key → CompAuxNum (F00001, F00002, ...) by first appearance."""
    mapping: dict[str, str] = {}
    counter = 1
    for inv in invoices:
        key = inv.supplier_siret or inv.supplier_name
        if key not in mapping:
            mapping[key] = f"F{counter:05d}"
            counter += 1
    return mapping


def fec_filename(siren: str, batch_date: date) -> str:
    return f"FEC_{siren}_{_fmt_date(batch_date)}.txt"


def _row(values: dict[str, str]) -> str:
    return _DELIM.join(values.get(c, "") for c in FEC_COLUMNS)


def _build_rows(
    invoices: list[InvoiceData],
    batch_date: date,
) -> list[str]:
    aux = _aux_map(invoices)
    valid_str = _fmt_date(batch_date)
    lines: list[str] = []

    for idx, inv in enumerate(invoices, start=1):
        ecriture_num = str(idx)
        ecriture_date = _fmt_date(inv.invoice_date)
        piece_date = ecriture_date
        piece_ref = inv.invoice_number
        ecriture_lib = f"{inv.supplier_name} {inv.invoice_number}".strip()
        supplier_key = inv.supplier_siret or inv.supplier_name
        comp_aux_num = aux[supplier_key]

        common = {
            "JournalCode": _JOURNAL_CODE,
            "JournalLib": _JOURNAL_LIB,
            "EcritureNum": ecriture_num,
            "EcritureDate": ecriture_date,
            "PieceRef": piece_ref,
            "PieceDate": piece_date,
            "EcritureLib": ecriture_lib,
            "ValidDate": valid_str,
            "Idevise": inv.currency,
        }

        # Line 1: debit HT, 6068
        l1 = dict(common)
        l1["CompteNum"] = _COMPTE_HT[0]
        l1["CompteLib"] = _COMPTE_HT[1]
        l1["Debit"] = _fmt_amount(inv.amount_ht)
        l1["Credit"] = _fmt_amount(Decimal("0"))
        lines.append(_row(l1))

        # Line 2: debit VAT, 44566
        l2 = dict(common)
        l2["CompteNum"] = _COMPTE_TVA[0]
        l2["CompteLib"] = _COMPTE_TVA[1]
        l2["Debit"] = _fmt_amount(inv.amount_vat)
        l2["Credit"] = _fmt_amount(Decimal("0"))
        lines.append(_row(l2))

        # Line 3: credit TTC, 401 + auxiliary
        l3 = dict(common)
        l3["CompteNum"] = _COMPTE_FOURN[0]
        l3["CompteLib"] = _COMPTE_FOURN[1]
        l3["CompAuxNum"] = comp_aux_num
        l3["CompAuxLib"] = inv.supplier_name
        l3["Debit"] = _fmt_amount(Decimal("0"))
        l3["Credit"] = _fmt_amount(inv.amount_ttc)
        lines.append(_row(l3))

    return lines


def write_fec(
    invoices: list[InvoiceData],
    siren: str = "000000000",
    batch_date: Optional[date] = None,
) -> bytes:
    """Generate the FEC bytes (UTF-8 BOM, CRLF, pipe-delimited)."""
    if batch_date is None:
        batch_date = date.today()

    header = _DELIM.join(FEC_COLUMNS)
    data_lines = _build_rows(invoices, batch_date)
    body = _BOM + header + _LINE_SEP + _LINE_SEP.join(data_lines)
    if data_lines:
        body += _LINE_SEP
    fec_bytes = body.encode("utf-8")

    # Defensive internal validation.
    errors = validate_fec_output(fec_bytes)
    if errors:
        raise FECValidationError("Generated FEC failed validation: " + "; ".join(errors))

    # siren currently informational only; future: emit into a metadata sidecar.
    _ = siren
    return fec_bytes


def _parse_decimal(s: str) -> Decimal:
    return Decimal(s.replace(",", "."))


def validate_fec_output(fec_bytes: bytes) -> list[str]:
    """Return list of error strings; empty list means valid."""
    errors: list[str] = []
    try:
        text = fec_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        return [f"Cannot decode UTF-8 BOM: {e}"]

    raw_lines = text.split(_LINE_SEP)
    # Drop trailing empty line from trailing CRLF
    lines = [ln for ln in raw_lines if ln != ""]

    if not lines:
        return ["Empty FEC"]

    header = lines[0]
    if header.split(_DELIM) != FEC_COLUMNS:
        errors.append("Header mismatch")

    data = lines[1:]
    debit_sum: dict[str, Decimal] = {}
    credit_sum: dict[str, Decimal] = {}

    for i, line in enumerate(data, start=2):
        cols = line.split(_DELIM)
        if len(cols) != _NUM_COLS:
            errors.append(f"Line {i}: expected {_NUM_COLS} columns, got {len(cols)}")
            continue
        row = dict(zip(FEC_COLUMNS, cols))
        for date_col in ("EcritureDate", "PieceDate", "ValidDate"):
            v = row.get(date_col, "")
            if v and not _DATE_RE.match(v):
                errors.append(f"Line {i}: {date_col} '{v}' not AAAAMMJJ")
        try:
            d = _parse_decimal(row["Debit"]) if row["Debit"] else Decimal("0")
            c = _parse_decimal(row["Credit"]) if row["Credit"] else Decimal("0")
        except Exception as e:
            errors.append(f"Line {i}: bad amount: {e}")
            continue
        ec = row["EcritureNum"]
        debit_sum[ec] = debit_sum.get(ec, Decimal("0")) + d
        credit_sum[ec] = credit_sum.get(ec, Decimal("0")) + c

    for ec in set(list(debit_sum.keys()) + list(credit_sum.keys())):
        if debit_sum.get(ec, Decimal("0")) != credit_sum.get(ec, Decimal("0")):
            errors.append(
                f"EcritureNum {ec}: debit {debit_sum.get(ec)} != credit {credit_sum.get(ec)}"
            )

    return errors
