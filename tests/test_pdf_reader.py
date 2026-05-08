"""Tests for core.pdf_reader."""
from __future__ import annotations

from core.pdf_reader import read_text


def test_read_text_extracts_known_substring(fixture_pdf_bytes):
    text = read_text(fixture_pdf_bytes)
    assert text is not None
    assert "FACTURE TEST" in text
    assert "73282932000074" in text


def test_read_text_returns_none_for_garbage():
    assert read_text(b"not a pdf at all") is None


def test_read_text_returns_none_for_empty():
    assert read_text(b"") is None
