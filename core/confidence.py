"""Per-field confidence scoring for extracted invoice data."""
from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.models import InvoiceData


_TVA_PATTERN = re.compile(r"^FR[0-9A-Z]{2}\d{9}$")
_AMOUNT_TOLERANCE = Decimal("0.01")


def _luhn(digits: str) -> bool:
    if not digits or not digits.isdigit():
        return False
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _validate_fr_tva(tva: str) -> bool:
    """Validate French VAT number: FR + 2-char key + 9-digit SIREN.

    The numeric 2-digit key matches `(12 + 3*(SIREN%97))%97`.
    Non-numeric keys (legacy alphanumeric) are not algorithmically validated
    and return False here (the caller may treat these as low confidence).
    """
    if not tva or not _TVA_PATTERN.match(tva):
        return False
    key_part = tva[2:4]
    siren = tva[4:]
    if not key_part.isdigit():
        return False
    expected = (12 + 3 * (int(siren) % 97)) % 97
    return int(key_part) == expected


def score(invoice: "InvoiceData") -> dict[str, float]:
    """Compute per-field confidence scores in [0.0, 1.0]."""
    scores: dict[str, float] = {}

    # SIRET
    if invoice.supplier_siret is None:
        scores["supplier_siret"] = 1.0
    elif _luhn(invoice.supplier_siret):
        scores["supplier_siret"] = 1.0
    else:
        scores["supplier_siret"] = 0.4

    # TVA
    if invoice.supplier_vat_number is None:
        scores["supplier_vat_number"] = 1.0
    elif _validate_fr_tva(invoice.supplier_vat_number):
        scores["supplier_vat_number"] = 1.0
    else:
        scores["supplier_vat_number"] = 0.4

    # Date — pydantic already typed it as `date`
    scores["invoice_date"] = 1.0

    # Amounts: HT + VAT == TTC ±0.01
    diff = abs(invoice.amount_ht + invoice.amount_vat - invoice.amount_ttc)
    if diff <= _AMOUNT_TOLERANCE:
        scores["amount_ht"] = 1.0
        scores["amount_vat"] = 1.0
        scores["amount_ttc"] = 1.0
    else:
        scores["amount_ht"] = 0.5
        scores["amount_vat"] = 0.5
        scores["amount_ttc"] = 0.5

    # Heuristic placeholders (future: LLM self-rating).
    scores["supplier_name"] = 0.9
    scores["invoice_number"] = 0.9

    return scores
