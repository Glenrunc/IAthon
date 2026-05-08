"""Vision LLM extraction → InvoiceData."""
from __future__ import annotations

import json
import os
import re
import socket
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv
from pydantic import ValidationError

from core.confidence import score
from core.models import InvoiceData


load_dotenv()


_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "invoice_extraction.fr.md"
_DEFAULT_MODEL = "gemini-2.5-flash"
_RATE_LIMIT_RE = re.compile(r"quota|rate.?limit|429", re.IGNORECASE)


class ExtractionError(Exception):
    """Base exception for all extraction failures."""


class MissingKeyError(ExtractionError):
    """GOOGLE_API_KEY missing from environment."""


class RateLimitError(ExtractionError):
    """Provider quota or per-second rate limit hit."""


class NetworkError(ExtractionError):
    """Timeout, DNS, or transport failure."""


class JsonParseError(ExtractionError):
    """Provider returned non-JSON or malformed JSON."""


class SchemaValidationError(ExtractionError):
    """Pydantic rejected the extracted payload."""


class Provider(Protocol):
    def extract_json(self, file_bytes: bytes, mime: str, prompt: str) -> str:
        ...


class GeminiProvider:
    """Google Gemini vision provider."""

    def __init__(self, model: str = _DEFAULT_MODEL):
        self.model_name = model

    def extract_json(self, file_bytes: bytes, mime: str, prompt: str) -> str:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise MissingKeyError("GOOGLE_API_KEY missing from environment")
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                [prompt, {"mime_type": mime, "data": file_bytes}]
            )
            return response.text
        except ExtractionError:
            raise
        except Exception as e:
            # Classify by exception type before falling back to message matching.
            try:
                from google.api_core import exceptions as gax
                if isinstance(e, gax.ResourceExhausted):
                    raise RateLimitError(str(e)) from e
                if isinstance(e, gax.DeadlineExceeded):
                    raise NetworkError(str(e)) from e
            except ImportError:
                pass
            if isinstance(e, (socket.timeout, TimeoutError)):
                raise NetworkError(str(e)) from e
            try:
                import requests
                if isinstance(e, requests.exceptions.Timeout):
                    raise NetworkError(str(e)) from e
            except ImportError:
                pass
            msg = str(e)
            if _RATE_LIMIT_RE.search(msg):
                raise RateLimitError(msg) from e
            raise ExtractionError(f"Gemini API call failed: {e}") from e


class MistralProvider:
    """Backup provider stub."""

    def extract_json(self, file_bytes: bytes, mime: str, prompt: str) -> str:
        raise NotImplementedError("Mistral backup, not used in V1")


def _detect_mime(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "application/pdf"
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    raise ExtractionError(f"Unsupported file type: {filename}")


def _load_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except OSError as e:
        raise ExtractionError(f"Could not read extraction prompt: {e}") from e


def _strip_code_fence(text: str) -> str:
    """Strip ```json ... ``` fences if present."""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.endswith("```"):
            s = s[: -3]
        s = s.strip()
        if s.startswith("json\n"):
            s = s[5:]
        elif s.startswith("json"):
            s = s[4:]
        s = s.lstrip()
    return s


def extract(
    file_bytes: bytes,
    filename: str,
    model: str = _DEFAULT_MODEL,
    provider: Provider | None = None,
) -> InvoiceData:
    """Extract invoice data from a file via Gemini Vision.

    Raises ExtractionError on any failure (network, parse, validation).
    """
    mime = _detect_mime(filename)
    prompt = _load_prompt()
    provider = provider or GeminiProvider(model=model)

    try:
        raw = provider.extract_json(file_bytes, mime, prompt)
    except ExtractionError:
        raise
    except Exception as e:
        # Classify exceptions that bypass GeminiProvider's internal handler
        # (e.g. when extract_json is mocked to raise directly in tests).
        try:
            from google.api_core import exceptions as gax
            if isinstance(e, gax.ResourceExhausted):
                raise RateLimitError(str(e)) from e
            if isinstance(e, gax.DeadlineExceeded):
                raise NetworkError(str(e)) from e
        except ImportError:
            pass
        if isinstance(e, (socket.timeout, TimeoutError)):
            raise NetworkError(str(e)) from e
        try:
            import requests
            if isinstance(e, requests.exceptions.Timeout):
                raise NetworkError(str(e)) from e
        except ImportError:
            pass
        msg = str(e)
        if _RATE_LIMIT_RE.search(msg):
            raise RateLimitError(msg) from e
        raise ExtractionError(f"Provider call failed: {e}") from e

    cleaned = _strip_code_fence(raw)

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise JsonParseError(f"LLM returned invalid JSON: {e}") from e

    if not isinstance(payload, dict):
        raise JsonParseError("LLM JSON is not an object")

    payload["source_filename"] = filename

    try:
        invoice = InvoiceData(**payload)
    except ValidationError as e:
        raise SchemaValidationError(f"Schema validation failed: {e}") from e

    invoice.confidence = score(invoice)
    return invoice
