"""Luhn / TVA / invoice helpers for French invoice generation."""


def luhn_check_digit(partial: str) -> str:
    """Compute Luhn check digit for the given digit string (without check digit)."""
    digits = [int(d) for d in partial]
    # Double every second digit from the right (i.e., from the end of `partial`)
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    check = (10 - (total % 10)) % 10
    return str(check)


def luhn_valid(number: str) -> bool:
    """Return True if the full digit string passes Luhn."""
    return luhn_check_digit(number[:-1]) == number[-1]


def make_siret(siren: str, nic: str = "0001") -> str:
    """Build a Luhn-valid 14-digit SIRET from a 9-digit SIREN + 4-digit NIC partial.

    SIRET = SIREN(9) + nic_partial(4) + Luhn_check(1) = 14 digits total.
    """
    assert len(siren) == 9, f"SIREN must be 9 digits, got {siren!r}"
    assert len(nic) == 4, f"NIC partial must be 4 digits, got {nic!r}"
    base = siren + nic  # 13 digits
    check = luhn_check_digit(base)
    result = base + check
    assert len(result) == 14, f"Generated SIRET {result!r} is not 14 digits!"
    assert luhn_valid(result), f"Generated SIRET {result!r} fails Luhn!"
    return result


def make_tva_intra(siren: str) -> str:
    """Compute French intracommunity VAT number: FR<2-digit key><9-digit SIREN>."""
    key = (12 + 3 * (int(siren) % 97)) % 97
    return f"FR{key:02d}{siren}"


def make_invoice_number(idx: int) -> str:
    """Return invoice number like F-2026-001."""
    return f"F-2026-{idx:03d}"
