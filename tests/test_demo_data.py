"""Tests for generated sample PDFs: verify SIRETs are 14-digit and Luhn-valid."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR = ROOT / "data" / "samples"

from core.confidence import _luhn


def test_generate_invoices_exits_zero():
    """scripts/generate_invoices.py must complete without error."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_invoices.py")],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, (
        f"generate_invoices.py exited {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.parametrize(
    "pdf_path",
    sorted(
        p for p in SAMPLES_DIR.glob("*.pdf") if "scan" not in p.name
    ),
    ids=lambda p: p.name,
)
def test_text_layer_pdf_siret_is_14_digits_and_luhn_valid(pdf_path):
    """Each text-layer PDF must contain a 14-digit Luhn-valid SIRET."""
    try:
        import pdfplumber
    except ImportError:
        pytest.skip("pdfplumber not installed")

    try:
        text = pdfplumber.open(pdf_path).pages[0].extract_text() or ""
    except Exception as e:
        pytest.fail(f"Could not open {pdf_path.name}: {e}")

    m = re.search(r"SIRET[^\d]*([\d ]{14,16})", text)
    assert m, f"No SIRET found in {pdf_path.name}"

    siret = m.group(1).replace(" ", "").strip()
    assert len(siret) == 14, f"{pdf_path.name}: SIRET {siret!r} is {len(siret)} digits, expected 14"
    assert siret.isdigit(), f"{pdf_path.name}: SIRET {siret!r} contains non-digits"
    assert _luhn(siret), f"{pdf_path.name}: SIRET {siret!r} fails Luhn check"


def test_scan_pdfs_exist():
    """Scanned PDFs must exist (they are image-only; SIRET extraction skipped)."""
    for name in ("orange_business_scan.pdf", "manutan_scan.pdf"):
        assert (SAMPLES_DIR / name).exists(), f"Missing scan PDF: {name}"


def test_photo_jpgs_exist():
    """Phone-photo JPGs must exist."""
    for name in ("edf_pro_photo.jpg", "la_poste_pro_photo.jpg"):
        assert (SAMPLES_DIR / name).exists(), f"Missing photo JPG: {name}"
