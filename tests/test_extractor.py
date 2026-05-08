"""Tests for core.extractor."""
from __future__ import annotations

import json
import socket

import pytest

from core import extractor
from core.extractor import (
    ExtractionError,
    GeminiProvider,
    JsonParseError,
    MissingKeyError,
    NetworkError,
    RateLimitError,
    SchemaValidationError,
    extract,
)


VALID_PAYLOAD = {
    "supplier_name": "Société Générale",
    "supplier_siret": "73282932000074",
    "supplier_vat_number": "FR44732829320",
    "invoice_number": "F-001",
    "invoice_date": "2026-04-15",
    "amount_ht": 100.0,
    "amount_vat": 20.0,
    "amount_ttc": 120.0,
    "vat_rate": 20.0,
}


def test_extract_returns_invoice_with_confidence(mocker):
    mocker.patch.object(
        GeminiProvider,
        "extract_json",
        return_value=json.dumps(VALID_PAYLOAD),
    )
    inv = extract(b"fakebytes", "test.pdf")
    assert inv.supplier_name == "Société Générale"
    assert inv.source_filename == "test.pdf"
    assert inv.confidence
    assert inv.confidence["supplier_siret"] == 1.0
    assert inv.confidence["supplier_vat_number"] == 1.0


def test_extract_missing_api_key_raises(mocker, monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(MissingKeyError, match="GOOGLE_API_KEY"):
        extract(b"fakebytes", "test.pdf")


def test_extract_missing_api_key_is_extraction_error(mocker, monkeypatch):
    """MissingKeyError must be catchable as ExtractionError (base class)."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ExtractionError):
        extract(b"fakebytes", "test.pdf")


def test_extract_malformed_json_raises(mocker):
    mocker.patch.object(
        GeminiProvider,
        "extract_json",
        return_value="not json at all",
    )
    with pytest.raises(JsonParseError, match="invalid JSON"):
        extract(b"fakebytes", "test.pdf")


def test_extract_unsupported_mime_raises():
    with pytest.raises(ExtractionError, match="Unsupported"):
        extract(b"fakebytes", "test.docx")


def test_extract_strips_code_fence(mocker):
    fenced = "```json\n" + json.dumps(VALID_PAYLOAD) + "\n```"
    mocker.patch.object(GeminiProvider, "extract_json", return_value=fenced)
    inv = extract(b"fakebytes", "test.pdf")
    assert inv.invoice_number == "F-001"


def test_extract_strips_code_fence_no_newline(mocker):
    """Handles ```json{...}``` with no newline after 'json'."""
    fenced = "```json" + json.dumps(VALID_PAYLOAD) + "```"
    mocker.patch.object(GeminiProvider, "extract_json", return_value=fenced)
    inv = extract(b"fakebytes", "test.pdf")
    assert inv.invoice_number == "F-001"


def test_extract_validation_failure_wrapped(mocker):
    bad = dict(VALID_PAYLOAD)
    bad["supplier_siret"] = "12345678901234"  # fails Luhn
    mocker.patch.object(
        GeminiProvider,
        "extract_json",
        return_value=json.dumps(bad),
    )
    with pytest.raises(SchemaValidationError, match="Schema validation"):
        extract(b"fakebytes", "test.pdf")


# ---------------------------------------------------------------------------
# New typed-exception tests (Task 5)
# ---------------------------------------------------------------------------


def test_rate_limit_error_from_resource_exhausted(mocker, monkeypatch):
    """google.api_core ResourceExhausted → RateLimitError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    try:
        from google.api_core import exceptions as gax
        exc = gax.ResourceExhausted("429 quota exceeded")
    except ImportError:
        pytest.skip("google-api-core not installed")

    mocker.patch.object(GeminiProvider, "extract_json", side_effect=exc)
    with pytest.raises(RateLimitError):
        extract(b"fakebytes", "test.pdf")


def test_rate_limit_error_is_extraction_error(mocker, monkeypatch):
    """RateLimitError is a subclass of ExtractionError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    try:
        from google.api_core import exceptions as gax
        exc = gax.ResourceExhausted("429 quota exceeded")
    except ImportError:
        pytest.skip("google-api-core not installed")

    mocker.patch.object(GeminiProvider, "extract_json", side_effect=exc)
    with pytest.raises(ExtractionError):
        extract(b"fakebytes", "test.pdf")


def test_network_error_from_socket_timeout(mocker, monkeypatch):
    """socket.timeout → NetworkError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    mocker.patch.object(GeminiProvider, "extract_json", side_effect=socket.timeout("timed out"))
    with pytest.raises(NetworkError):
        extract(b"fakebytes", "test.pdf")


def test_json_parse_error_from_garbage_response(mocker, monkeypatch):
    """Malformed JSON string → JsonParseError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    mocker.patch.object(GeminiProvider, "extract_json", return_value="not json {{{")
    with pytest.raises(JsonParseError):
        extract(b"fakebytes", "test.pdf")


def test_schema_validation_error_from_15digit_siret(mocker, monkeypatch):
    """15-digit SIRET in JSON → SchemaValidationError (Pydantic rejects it)."""
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    bad = dict(VALID_PAYLOAD)
    bad["supplier_siret"] = "732829320000133"  # 15 digits — the original bug
    mocker.patch.object(GeminiProvider, "extract_json", return_value=json.dumps(bad))
    with pytest.raises(SchemaValidationError):
        extract(b"fakebytes", "test.pdf")


def test_schema_validation_error_from_missing_required_field(mocker, monkeypatch):
    """Missing required field in JSON → SchemaValidationError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    bad = dict(VALID_PAYLOAD)
    del bad["invoice_number"]  # required field
    mocker.patch.object(GeminiProvider, "extract_json", return_value=json.dumps(bad))
    with pytest.raises(SchemaValidationError):
        extract(b"fakebytes", "test.pdf")


def test_mistral_provider_not_implemented():
    from core.extractor import MistralProvider

    with pytest.raises(NotImplementedError):
        MistralProvider().extract_json(b"x", "application/pdf", "p")
