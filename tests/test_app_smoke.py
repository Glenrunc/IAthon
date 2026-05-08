import compileall
import importlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_app_compiles():
    """app.py must be syntactically valid Python."""
    result = compileall.compile_file(str(ROOT / "app.py"), quiet=1)
    assert result, "app.py failed to compile"


def test_ui_modules_import():
    """All ui/* modules must import without exception."""
    for name in ("ui", "ui.upload", "ui.review", "ui.export"):
        importlib.import_module(name)


def test_ui_modules_dont_run_streamlit_at_import(monkeypatch):
    """Importing ui.* must not invoke top-level st.* calls."""
    import streamlit as st
    called = []
    monkeypatch.setattr(st, "title", lambda *a, **kw: called.append("title"))
    monkeypatch.setattr(st, "header", lambda *a, **kw: called.append("header"))
    for name in ("ui.upload", "ui.review", "ui.export"):
        importlib.reload(importlib.import_module(name))
    assert called == [], f"ui.* triggered Streamlit calls at import: {called}"
