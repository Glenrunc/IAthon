"""Pydantic models for invoice data."""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


_TVA_PATTERN = re.compile(r"^FR[0-9A-Z]{2}\d{9}$")


def _luhn_check(digits: str) -> bool:
    """Standard Luhn checksum."""
    if not digits.isdigit():
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


class InvoiceData(BaseModel):
    """Strict schema for an extracted French invoice."""

    model_config = ConfigDict(
        # Accept str/float for Decimal fields and coerce.
        validate_assignment=True,
    )

    supplier_name: str
    supplier_siret: Optional[str] = None
    supplier_vat_number: Optional[str] = None
    invoice_number: str
    invoice_date: date
    amount_ht: Decimal
    amount_vat: Decimal
    amount_ttc: Decimal
    vat_rate: Optional[Decimal] = None
    currency: Literal["EUR"] = "EUR"
    confidence: dict[str, float] = Field(default_factory=dict)
    source_filename: str = ""

    @field_validator("supplier_siret")
    @classmethod
    def _check_siret(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        v = v.replace(" ", "")
        if len(v) != 14 or not v.isdigit():
            raise ValueError("SIRET must be 14 digits")
        if not _luhn_check(v):
            raise ValueError("SIRET fails Luhn check")
        return v

    @field_validator("supplier_vat_number")
    @classmethod
    def _check_vat(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        v = v.replace(" ", "").upper()
        if not _TVA_PATTERN.match(v):
            raise ValueError("VAT number must match FR + 2 chars + 9 digits")
        return v
