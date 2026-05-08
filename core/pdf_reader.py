"""Lightweight pdfplumber wrapper for text-layer extraction."""
from __future__ import annotations

from io import BytesIO
from typing import Optional

import pdfplumber


_MIN_TEXT_LEN = 20


def read_text(file_bytes: bytes) -> Optional[str]:
    """Return concatenated text from all pages, or None if image-only / errors."""
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            parts: list[str] = []
            for page in pdf.pages:
                t = page.extract_text() or ""
                if t:
                    parts.append(t)
            text = "\n".join(parts).strip()
        if len(text) < _MIN_TEXT_LEN:
            return None
        return text
    except Exception:
        return None
