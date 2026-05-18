"""Streamlit entry point — Facture (Facture → FEC)."""
from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from core.storage import (
    create_batch,
    delete_batch,
    get_batch_records,
    init_db,
    list_batches,
    update_batch,
)
from core.config import charger_configuration, charger_logo
from core.helpers import configurer_api
from ui.export import render_export
from ui.review import render_review
from ui.upload import process_files, render_upload
from ui.accueil_view import render_accueil_view
from ui.rh_view import render_rh_view
from ui.marketing_view import render_marketing_view
from ui.audio_view import render_audio_view
from ui.client_view import render_client_view
from ui.config_view import render_config_view
from ui.facture_view import render_facture_view


MIN_PER_INVOICE = 3


# ──────────────────────────  Global CSS  ──────────────────────────
_GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600;8..60,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #F7F6F2;
    --surface: #FFFFFF;
    --ink: #0B1F3A;
    --ink-2: #38445C;
    --ink-3: #6B7384;
    --accent: #1F3A8A;
    --accent-2: #3354BB;
    --line: #E8E4D8;
    --line-2: #EFECE2;
    --mute: #C7C2B6;
    --bronze: #8A6F3D;
    --warn-bg: #FBF1D9;
    --warn-border: #E6CD8A;
    --warn-ink: #6B4F12;
    --success: #15803D;
    --success-bg: #E8F3EB;
    --error: #B91C1C;
    --error-bg: #FBEAE9;
    --r-1: 4px; --r-2: 8px; --r-3: 12px;
    --shadow-1: 0 1px 0 rgba(11,31,58,.04), 0 1px 2px rgba(11,31,58,.04);
    --shadow-2: 0 1px 0 rgba(11,31,58,.04), 0 8px 24px -12px rgba(11,31,58,.18);
    --font-display: "Source Serif 4", "Source Serif Pro", Georgia, serif;
    --font-body: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    --font-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, monospace;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: var(--bg) !important;
    color: var(--ink) !important;
    font-family: var(--font-body) !important;
    font-size: 14px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
}

/* faint paper texture */
.stApp::before {
    content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image: radial-gradient(rgba(11,31,58,.018) 1px, transparent 1.2px);
    background-size: 4px 4px; mix-blend-mode: multiply;
}

/* hide chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] { background: transparent; height: 0; }

/* main padding */
.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 4rem !important;
    max-width: 1240px;
}

/* typography */
h1, h2, h3, h4 {
    font-family: var(--font-display) !important;
    color: var(--ink) !important;
    letter-spacing: -0.005em;
}
h1 { font-weight: 600 !important; }
h2 { font-weight: 600 !important; font-size: 22px !important; }
h3 { font-weight: 600 !important; font-size: 17px !important; }
.stMarkdown p, .stMarkdown li, label { font-family: var(--font-body) !important; color: var(--ink-2); }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--ink-3) !important; font-size: 12.5px !important; }

::selection { background: #DCE3F5; color: var(--ink); }

/* scrollbar */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb {
    background: rgba(11,31,58,.14); border-radius: 6px;
    border: 2px solid transparent; background-clip: content-box;
}
::-webkit-scrollbar-thumb:hover { background: rgba(11,31,58,.28); border: 2px solid transparent; background-clip: content-box; }

/* sidebar */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-family: var(--font-display) !important;
    font-size: 15px !important;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: var(--ink-3) !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] label { font-size: 12px !important; color: var(--ink-2) !important; }

/* inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    font-family: var(--font-mono) !important;
    background: var(--bg) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
    color: var(--ink) !important;
    letter-spacing: .04em;
}
.stTextInput input:focus, .stTextArea textarea:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 2px rgba(31,58,138,.12) !important; }

/* buttons */
.stButton > button, .stDownloadButton > button {
    font-family: var(--font-body) !important;
    font-weight: 500;
    border-radius: 8px !important;
    border: 1px solid var(--line) !important;
    background: var(--surface);
    color: var(--ink-2);
    box-shadow: var(--shadow-1);
    transition: all .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: var(--bronze) !important;
    color: var(--ink) !important;
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
    background: var(--ink) !important;
    color: var(--bg) !important;
    border-color: var(--ink) !important;
    font-weight: 600;
    letter-spacing: .01em;
    box-shadow: 0 1px 0 rgba(255,255,255,.06) inset, 0 1px 2px rgba(11,31,58,.18);
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    transform: translateY(-1px);
    box-shadow: 0 1px 0 rgba(255,255,255,.08) inset, 0 6px 18px -6px rgba(11,31,58,.45);
}
.stButton > button[kind="primary"]:disabled, .stDownloadButton > button[kind="primary"]:disabled {
    background: var(--mute) !important;
    border-color: var(--mute) !important;
    color: var(--bg) !important;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

/* file uploader — restyle dashed border */
[data-testid="stFileUploader"] section {
    background: var(--surface) !important;
    border: 1px dashed var(--line) !important;
    border-radius: 12px !important;
    padding: 24px !important;
    transition: border-color .15s ease, background .15s ease;
}
[data-testid="stFileUploader"] section:hover {
    border-color: var(--accent) !important;
    background: rgba(31,58,138,.03) !important;
}
[data-testid="stFileUploader"] section small,
[data-testid="stFileUploader"] section span,
[data-testid="stFileUploader"] section p { color: var(--ink-3) !important; }
[data-testid="stFileUploader"] button {
    background: var(--bg) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
    color: var(--accent) !important;
    font-weight: 500;
}

/* st.metric */
[data-testid="stMetric"] {
    background: var(--bg);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 10px 14px;
}
[data-testid="stMetricLabel"] {
    color: var(--ink-3) !important;
    font-size: 12px !important;
    letter-spacing: .04em;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-display) !important;
    font-weight: 600 !important;
    font-size: 22px !important;
    color: var(--ink) !important;
    font-variant-numeric: tabular-nums;
}

/* st.status / st.expander */
[data-testid="stExpander"], [data-testid="stStatus"] {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
}

/* code blocks (FEC preview fallback) */
[data-testid="stCodeBlock"] pre, .stCodeBlock pre {
    font-family: var(--font-mono) !important;
    font-size: 12px !important;
    background: var(--ink) !important;
    color: #D6DCE6 !important;
    border-radius: 12px !important;
    box-shadow: var(--shadow-2);
}

/* alerts */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border: 1px solid var(--line) !important;
    box-shadow: var(--shadow-1);
}
[data-testid="stAlert"][data-baseweb="notification"] { padding: 14px 16px !important; }

/* progress bar */
[data-testid="stProgress"] [role="progressbar"] {
    background: var(--line-2) !important;
    height: 4px !important;
    border-radius: 999px !important;
    overflow: hidden;
}
[data-testid="stProgress"] [role="progressbar"] > div {
    background: var(--accent) !important;
    border-radius: 999px !important;
    height: 100% !important;
}

/* data editor */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    overflow: hidden;
    background: var(--surface);
}

/* verification checkbox card */
.fct-verify-wrap {
    margin: 10px 0 16px;
    border-radius: 10px;
    border: 1px solid var(--line);
    background: var(--surface);
    transition: border-color .2s ease, background .2s ease;
    overflow: hidden;
}
.fct-verify-wrap:has(input[type="checkbox"]:checked) {
    border-color: var(--success);
    background: var(--success-bg);
}
.fct-verify-wrap [data-testid="stCheckbox"] { padding: 12px 14px; margin: 0; }
.fct-verify-wrap [data-testid="stCheckbox"] label {
    font-size: 13.5px !important;
    font-weight: 600 !important;
    color: var(--ink) !important;
    gap: 10px;
    cursor: pointer;
}
.fct-verify-wrap:has(input:checked) [data-testid="stCheckbox"] label {
    color: var(--success) !important;
}

/* Sidebar secondary buttons = delete actions → compact danger style */
[data-testid="stSidebar"] button[kind="secondary"] {
    color: var(--error) !important;
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
    font-size: 15px !important;
    line-height: 1 !important;
    padding: 4px 6px !important;
    min-height: 28px !important;
    height: 28px !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background: var(--error-bg) !important;
    border-color: var(--error) !important;
}

/* animations */
@keyframes shimmer { 0%{ background-position: -200px 0; } 100%{ background-position: 200px 0; } }
.fct-sk {
    background: linear-gradient(90deg, #EFECE2 0px, #F7F6F2 80px, #EFECE2 160px);
    background-size: 200px 100%;
    animation: shimmer 1.4s infinite linear;
    border-radius: 4px;
    height: 12px;
    display: block;
}
@keyframes fadeUp { from { opacity:0; transform: translateY(4px); } to { opacity:1; transform: translateY(0); } }
.fct-fade-up { animation: fadeUp .35s ease both; }
@keyframes pulseDot { 0%,100%{ opacity:.5; } 50%{ opacity:1; } }
@keyframes countUp { from { opacity: 0; } to { opacity: 1; } }
@keyframes toastIn { from { opacity:0; transform: translate(-50%, 8px); } to { opacity:1; transform: translate(-50%, 0); } }

/* count-up metric (custom) */
.fct-counter {
    display: inline-flex; align-items: baseline; gap: 8px;
    padding: 10px 14px; border-radius: 10px;
    border: 1px solid var(--line); background: var(--bg);
}
.fct-counter .fct-counter-num {
    font-family: var(--font-display); font-weight: 600; font-size: 22px;
    color: var(--ink); font-variant-numeric: tabular-nums;
    --c: 0;
    counter-reset: count var(--c);
    animation: countUp 1.1s cubic-bezier(.2,.8,.2,1) both;
}
.fct-counter .fct-counter-num::after { content: counter(count); }
.fct-counter .fct-counter-label { font-size: 12px; color: var(--ink-3); }
.fct-counter svg { color: var(--bronze); }

/* JS-driven count up (more reliable than CSS counter) */
.fct-num[data-target] { font-variant-numeric: tabular-nums; }

/* header card */
.fct-header {
    display: flex; align-items: flex-end; justify-content: space-between;
    padding: 22px 24px 18px; border: 1px solid var(--line);
    background: var(--surface); border-radius: 12px;
    box-shadow: var(--shadow-1);
    margin-bottom: 18px;
}
.fct-brand { display: flex; align-items: center; gap: 14px; }
.fct-logo {
    width: 36px; height: 36px; border-radius: 8px;
    background: var(--ink); color: var(--bg);
    display: grid; place-items: center;
}
.fct-wordmark {
    font-family: var(--font-display); font-weight: 600;
    font-size: 26px; line-height: 1; letter-spacing: -0.01em; color: var(--ink);
}
.fct-tagline { margin-top: 4px; font-size: 12.5px; color: var(--ink-3); letter-spacing: .01em; }
.fct-header-right { display: flex; align-items: center; gap: 16px; }
.fct-trust { display: flex; align-items: center; gap: 6px; color: var(--ink-3); font-size: 12.5px; }

/* step rail */
.fct-steprail {
    display: flex; align-items: center; gap: 8px; margin-bottom: 24px;
    padding: 12px 16px; background: var(--surface);
    border: 1px solid var(--line); border-radius: 10px;
}
.fct-step { display: flex; align-items: center; gap: 8px; }
.fct-step-bullet {
    width: 22px; height: 22px; border-radius: 999px;
    display: grid; place-items: center;
    font-size: 11px; font-weight: 600; font-family: var(--font-body);
}
.fct-step-bullet.done { background: var(--success); color: var(--bg); }
.fct-step-bullet.active { background: var(--ink); color: var(--bg); }
.fct-step-bullet.idle { background: transparent; color: var(--ink-3); border: 1px solid var(--line); }
.fct-step-label { font-size: 12.5px; }
.fct-step-label.done { color: var(--ink-2); font-weight: 500; }
.fct-step-label.active { color: var(--ink); font-weight: 600; }
.fct-step-label.idle { color: var(--ink-3); font-weight: 500; }
.fct-step-line { flex: 1; height: 1px; background: var(--line); }
.fct-step-line.done { background: var(--success); opacity: .35; }

/* zone heading */
.fct-zone-head { display: flex; align-items: baseline; gap: 14px; margin: 18px 0 12px; }
.fct-zone-step {
    font-family: var(--font-display); font-size: 14px; font-weight: 500;
    color: var(--bronze); letter-spacing: .02em;
}
.fct-zone-title {
    margin: 0; font-family: var(--font-display); font-weight: 600;
    font-size: 22px; letter-spacing: -0.005em; color: var(--ink);
}
.fct-zone-sub { margin-top: 3px; font-size: 12.5px; color: var(--ink-3); }

/* processing rows */
.fct-proc-row {
    display: grid; grid-template-columns: 20px 1fr auto;
    align-items: center; gap: 12px;
    padding: 9px 12px; border-radius: 6px;
    font-size: 12.5px; margin-bottom: 4px;
}
.fct-proc-row.doing { background: rgba(31,58,138,.04); }
.fct-proc-row .fct-proc-dot.ok { color: var(--success); }
.fct-proc-row .fct-proc-dot.doing { color: var(--accent); animation: pulseDot 1.2s infinite; }
.fct-proc-row .fct-proc-dot.idle { color: var(--ink-3); opacity: .4; }
.fct-proc-row .fct-proc-name.idle { color: var(--ink-3); }
.fct-proc-row .fct-proc-name { color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.fct-proc-row .fct-proc-state { color: var(--ink-3); font-variant-numeric: tabular-nums; font-size: 11.5px; }

/* skeleton table preview */
.fct-skel-card {
    margin-top: 16px; padding: 16px; border: 1px dashed var(--line);
    border-radius: 8px; background: var(--bg);
}
.fct-skel-eyebrow {
    font-size: 11px; font-weight: 600; letter-spacing: .06em;
    text-transform: uppercase; color: var(--ink-3); margin-bottom: 10px;
}
.fct-skel-row {
    display: grid; grid-template-columns: 2fr 2fr 1.5fr 1fr 1fr 1fr;
    gap: 8px; margin-bottom: 8px;
}

/* warm-amber confidence preview cards */
.fct-flag-preview {
    background: var(--warn-bg);
    border: 1px solid var(--warn-border);
    border-left: 2px solid var(--warn-border);
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 10px;
    color: var(--warn-ink);
    font-size: 12.5px;
    display: flex; align-items: flex-start; gap: 10px;
    animation: fadeUp .35s ease both;
}
.fct-flag-preview .fct-flag-icon { color: var(--warn-ink); margin-top: 2px; line-height: 0; }
.fct-flag-preview .fct-flag-body { flex: 1; }
.fct-flag-preview .fct-flag-title {
    font-family: var(--font-display); font-weight: 600; font-size: 14px;
    color: var(--ink); margin-bottom: 4px;
}
.fct-flag-preview .fct-flag-fields {
    display: flex; flex-wrap: wrap; gap: 6px;
    margin-top: 4px;
}
.fct-flag-preview .fct-flag-chip {
    background: rgba(255,255,255,.5);
    border: 1px solid var(--warn-border);
    border-radius: 4px;
    padding: 2px 8px;
    font-family: var(--font-mono);
    font-size: 11.5px;
    color: var(--warn-ink);
}

/* FEC monospace card */
.fct-fec-card {
    background: var(--ink); color: #E2E5EC; border-radius: 12px;
    overflow: hidden; box-shadow: var(--shadow-2); margin-bottom: 16px;
}
.fct-fec-head {
    padding: 10px 14px; border-bottom: 1px solid rgba(255,255,255,.08);
    display: flex; justify-content: space-between; align-items: center;
    font-size: 11.5px; color: rgba(255,255,255,.55);
    letter-spacing: .05em; text-transform: uppercase;
}
.fct-fec-head .fct-fec-name { display: flex; align-items: center; gap: 8px; }
.fct-fec-pre {
    margin: 0; padding: 14px 16px;
    font: 12px/1.6 var(--font-mono);
    overflow-x: auto; white-space: pre;
    color: #D6DCE6;
    counter-reset: line;
}
.fct-fec-pre .fct-line { display: block; }
.fct-fec-pre .fct-line::before {
    content: counter(line);
    counter-increment: line;
    display: inline-block; width: 28px; margin-right: 12px;
    color: rgba(255,255,255,.25); text-align: right;
    user-select: none;
}
.fct-fec-pre .fct-line.fct-head-line { color: #9AA3B5; }

/* validation hero */
.fct-val-hero {
    border-radius: 12px; padding: 18px;
    position: relative; overflow: hidden; margin-bottom: 14px;
}
.fct-val-hero.ok { border: 1px solid var(--success); background: var(--success-bg); }
.fct-val-hero.warn { border: 1px solid var(--warn-border); background: var(--warn-bg); }
.fct-val-hero.err { border: 1px solid var(--error); background: var(--error-bg); }
.fct-val-head {
    display: flex; align-items: center; gap: 10px;
    font-family: var(--font-display); font-weight: 600; font-size: 18px;
    color: var(--ink);
}
.fct-val-head.ok svg { color: var(--success); }
.fct-val-head.warn svg { color: var(--warn-ink); }
.fct-val-head.err svg { color: var(--error); }
.fct-val-list {
    margin: 12px 0 0 0; padding: 0; list-style: none;
    font-size: 12.5px; color: var(--ink-2); line-height: 1.7;
}
.fct-val-list li {
    display: flex; align-items: flex-start; gap: 8px; padding: 2px 0;
}
.fct-val-list li.ok svg { color: var(--success); }
.fct-val-list li.err svg { color: var(--error); }

/* small footer */
.fct-footer {
    margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--line);
    display: flex; justify-content: space-between;
    font-size: 11.5px; color: var(--ink-3);
}
</style>
"""


# ──────────────────────────  Inline Lucide icons (1.5px stroke)  ──────────────────────────
def _icon(name: str, size: int = 14, stroke: float = 1.5) -> str:
    """Return an inline Lucide-style SVG."""
    paths = {
        "logo": '<rect x="4" y="3" width="14" height="18" rx="1.5"/><path d="M8 8h6M8 12h6M8 16h3"/><path d="M18 7l3 3-3 3"/>',
        "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><polyline points="9 12 11 14 15 10"/>',
        "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
        "check": '<polyline points="20 6 9 17 4 12"/>',
        "checkc": '<circle cx="12" cy="12" r="10"/><polyline points="9 12 11.5 14.5 16 9.5"/>',
        "alert": '<path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>',
        "x": '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
        "xc": '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>',
        "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
        "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
        "filepdf": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
        "fec": '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>',
        "circle": '<circle cx="12" cy="12" r="10"/>',
    }
    body = paths.get(name, "")
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round" style="display:inline-block;vertical-align:-0.15em;">{body}</svg>'
    )


# ──────────────────────────  Phase + step rail  ──────────────────────────
def _current_phase() -> str:
    """Determine which step is active based on session state."""
    invoices = st.session_state.get("invoices", [])
    if st.session_state.get("_just_exported"):
        return "exported"
    if invoices:
        return "review"
    if st.session_state.get("_processing"):
        return "processing"
    return "loaded"


def _render_step_rail(phase: str, verified: bool = False) -> None:
    """Render the 4-step navigation rail."""
    steps = [
        ("loaded", "Dépôt"),
        ("processing", "Extraction"),
        ("review", "Vérification"),
        ("exported", "Export FEC"),
    ]
    order = ["loaded", "processing", "review", "exported"]
    idx = order.index(phase) if phase in order else 0

    parts = ['<div class="fct-steprail">']
    for i, (sid, label) in enumerate(steps):
        # Treat "review" as done when user has checked verified
        force_done = verified and sid == "review"
        if i < idx or force_done:
            cls = "done"
            inner = _icon("check", size=11, stroke=2.4)
        elif i == idx:
            cls = "active"
            inner = str(i + 1)
        else:
            cls = "idle"
            inner = str(i + 1)

        badge = ""
        if force_done and phase == "review":
            badge = (
                '<span style="font-size:10px;font-weight:600;letter-spacing:.03em;'
                'background:var(--success);color:#fff;border-radius:3px;'
                'padding:1px 5px;margin-left:5px;vertical-align:middle;">Vérifié</span>'
            )
        parts.append(
            f'<div class="fct-step">'
            f'<span class="fct-step-bullet {cls}">{inner}</span>'
            f'<span class="fct-step-label {cls}">{label}{badge}</span>'
            f"</div>"
        )
        if i < len(steps) - 1:
            line_cls = "done" if (i < idx or force_done) else ""
            parts.append(f'<span class="fct-step-line {line_cls}"></span>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


# ──────────────────────────  Header  ──────────────────────────
def _render_header() -> None:
    n_invoices = len(st.session_state["invoices"])
    minutes = n_invoices * MIN_PER_INVOICE
    html = f"""
<div class="fct-header">
  <div class="fct-brand">
    <div class="fct-logo">{_icon("logo", size=18, stroke=1.6)}</div>
    <div>
      <div class="fct-wordmark">Facture</div>
      <div class="fct-tagline">De la facture papier à l'écriture comptable, en un clic.</div>
    </div>
  </div>
  <div class="fct-header-right">
    <div class="fct-trust">{_icon("shield", size=14)} Conforme PCG · FEC validé</div>
    <div class="fct-counter">
      <span style="color:var(--bronze);line-height:0;">{_icon("clock", size=14)}</span>
      <span class="fct-counter-num" style="font-family:var(--font-display);font-weight:600;
            font-size:22px;color:var(--ink);font-variant-numeric:tabular-nums;">{minutes}</span>
      <span class="fct-counter-label">min économisées · ce mois</span>
    </div>
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# ──────────────────────────  Sidebar  ──────────────────────────
def _siren_feedback(siren_val: str) -> str:
    """Return an HTML snippet with contextual SIREN validation feedback."""
    n = len(siren_val)
    all_digits = siren_val.isdigit() or siren_val == ""
    if n == 9 and all_digits:
        return (
            f'<div style="font-size:11px;color:var(--success);display:flex;align-items:center;'
            f'gap:5px;margin-top:-6px;margin-bottom:4px;">'
            f'{_icon("check", size=12, stroke=2.2)} SIREN valide</div>'
        )
    if not all_digits:
        return (
            '<div style="font-size:11px;color:var(--error);margin-top:-6px;margin-bottom:4px;">'
            "Chiffres uniquement (format INSEE)</div>"
        )
    if 0 < n < 9:
        return (
            f'<div style="font-size:11px;color:var(--warn-ink);margin-top:-6px;margin-bottom:4px;">'
            f"{n}&thinsp;/&thinsp;9 chiffres</div>"
        )
    return (
        '<div style="font-size:11px;color:var(--ink-3);margin-top:-6px;margin-bottom:4px;">'
        "Format INSEE &mdash; 9 chiffres</div>"
    )


def _save_siren_to_batch() -> None:
    bid = st.session_state.get("batch_id")
    if bid is not None:
        update_batch(bid, siren=st.session_state.get("batch_siren", ""))


def _render_sidebar() -> None:
    with st.sidebar:
        if st.session_state.get('entreprise_logo'):
            st.image(st.session_state['entreprise_logo'], use_column_width=True)

        st.markdown(
            f"""
<div style="display:flex;align-items:center;gap:10px;padding:8px 0 18px;">
  <div style="width:28px;height:28px;border-radius:6px;background:var(--ink);color:var(--bg);
       display:grid;place-items:center;">{_icon("logo", size=14, stroke=1.6)}</div>
  <div style="font-family:var(--font-display);font-weight:600;font-size:18px;color:var(--ink);
       letter-spacing:-0.01em;">{st.session_state.get('entreprise_nom', 'Facture')}</div>
</div>
""",
            unsafe_allow_html=True,
        )

        api_active = configurer_api()
        if not api_active:
            st.error("🔑 Clé API non configurée dans le fichier .env")
            st.stop()

        st.markdown(
            '<div style="font-size:11px;font-weight:600;letter-spacing:.08em;'
            'text-transform:uppercase;color:var(--ink-3);margin-bottom:6px;">Navigation</div>',
            unsafe_allow_html=True,
        )

        st.session_state['navigation_radio'] = st.radio(
            "Navigation",
            [
                "🏠 Accueil",
                "📊 Gestion",
                "🤝 Ressources",
                "🚀 Croissance",
                "⚙️ Paramètres"
            ],
            index=0,
            label_visibility="collapsed"
        )

        st.divider()

        if st.session_state['navigation_radio'] == "📊 Gestion":
            st.markdown(
                '<div style="font-size:11px;font-weight:600;letter-spacing:.08em;'
                'text-transform:uppercase;color:var(--ink-3);margin-bottom:6px;">Entreprise</div>',
                unsafe_allow_html=True,
            )
            st.text_input(
                label="SIREN",
                key="batch_siren",
                max_chars=9,
                placeholder="123456789",
                help="Format INSEE — 9 chiffres, sans espace",
                on_change=_save_siren_to_batch,
            )
            st.markdown(_siren_feedback(st.session_state["batch_siren"]), unsafe_allow_html=True)

            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

            if st.button("+ Nouveau lot", type="primary", use_container_width=True):
                st.session_state["batch_id"] = None
                st.session_state["invoices"] = []
                st.session_state["_just_exported"] = False
                st.session_state["batch_verified"] = False
                st.rerun()

            st.markdown(
                '<div style="font-size:11px;font-weight:600;letter-spacing:.08em;'
                'text-transform:uppercase;color:var(--ink-3);margin:20px 0 8px;">Lots récents</div>',
                unsafe_allow_html=True,
            )

            batches = list_batches()
            current_id = st.session_state.get("batch_id")

            if not batches:
                st.markdown(
                    '<div style="font-size:12px;color:var(--ink-3);padding:6px 4px;">'
                    "Aucun lot. Déposez vos factures pour commencer."
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div style="border:1px solid var(--line);border-radius:8px;'
                    'overflow:hidden;background:var(--surface);">',
                    unsafe_allow_html=True,
                )
                for list_idx, b in enumerate(batches[:10]):
                    is_current = b["id"] == current_id
                    date_str = b["created_at"][:10]
                    n_inv = b.get("invoice_count", 0)
                    siren_display = b.get("siren") or ""
                    separator = "border-top:1px solid var(--line);" if list_idx > 0 else ""
                    bg = "background:rgba(31,58,138,.05);" if is_current else ""
                    accent_bar = (
                        "border-left:2px solid var(--accent);"
                        if is_current
                        else "border-left:2px solid transparent;"
                    )
                    verified_icon = (
                        f'&ensp;<span style="color:var(--success);font-size:11px;">'
                        f'{_icon("check", size=11, stroke=2.4)} Vérifié</span>'
                        if b.get("verified")
                        else ""
                    )
                    badge = (
                        '&ensp;<span style="font-size:10px;font-weight:500;'
                        'background:var(--accent);color:var(--bg);border-radius:3px;'
                        'padding:1px 5px;">EN COURS</span>'
                        if is_current
                        else ""
                    )
                    st.markdown(
                        f"""
<div style="padding:8px 10px;{separator}{bg}{accent_bar}">
  <div style="font-size:12.5px;font-weight:600;
       color:{'var(--accent)' if is_current else 'var(--ink)'};">
    Lot #{b['id']}{badge}{verified_icon}
  </div>
  <div style="font-size:11px;color:var(--ink-3);margin-top:2px;line-height:1.4;">
    {date_str}&ensp;·&ensp;{n_inv}&thinsp;pièce{'s' if n_inv != 1 else ''}
    {'<br/><span style="font-family:var(--font-mono);letter-spacing:.04em;">' + siren_display + '</span>' if siren_display else ''}
  </div>
</div>""",
                        unsafe_allow_html=True,
                    )

                    load_col, del_col = st.columns([3, 1])
                    if not is_current:
                        with load_col:
                            if st.button(
                                "↗ Charger",
                                key=f"load_batch_{b['id']}",
                                use_container_width=True,
                                type="primary",
                            ):
                                records = get_batch_records(b["id"])
                                st.session_state["batch_id"] = b["id"]
                                st.session_state["invoices"] = records
                                st.session_state["_pending_siren"] = b.get("siren") or ""
                                st.session_state["batch_verified"] = bool(b.get("verified"))
                                st.session_state["_just_exported"] = False
                                st.rerun()
                    with del_col:
                        if st.button(
                            "🗑",
                            key=f"del_batch_{b['id']}",
                            use_container_width=True,
                            help="Supprimer ce lot",
                        ):
                            delete_batch(b["id"])
                            if is_current:
                                st.session_state["batch_id"] = None
                                st.session_state["invoices"] = []
                                st.session_state["batch_verified"] = False
                            st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            '<div style="margin-top:28px;padding-top:14px;border-top:1px solid var(--line);'
            'font-size:11px;color:var(--ink-3);line-height:1.5;">'
            "Les pièces sont traitées localement.<br/>Aucune donnée transmise à des tiers."
            "</div>",
            unsafe_allow_html=True,
        )


# ──────────────────────────  Bootstrap  ──────────────────────────
def _bootstrap() -> None:
    load_dotenv()
    init_db()

    config = charger_configuration()
    st.session_state.setdefault("entreprise_nom", config['entreprise_nom'])
    st.session_state.setdefault("entreprise_gerant", config['entreprise_gerant'])

    logo = charger_logo(config.get('logo_path'))
    if logo:
        st.session_state.setdefault("entreprise_logo", logo)

    st.session_state.setdefault("navigation_radio", "🏠 Accueil")

    # Apply any pending session-state writes that must precede widget instantiation.
    # batch_siren cannot be set after st.text_input(key="batch_siren") renders,
    # so the "Charger" handler stores it here and we apply it first.
    if "_pending_siren" in st.session_state:
        st.session_state["batch_siren"] = st.session_state.pop("_pending_siren")
    st.session_state.setdefault("batch_id", None)
    st.session_state.setdefault("invoices", [])  # list[(invoice_id, InvoiceData)]
    st.session_state.setdefault("batch_siren", "")
    st.session_state.setdefault("batch_verified", False)
    st.session_state.setdefault("_processing", False)
    st.session_state.setdefault("_just_exported", False)


@st.cache_resource
def _reset_db_for_demo() -> None:
    """Wipe the SQLite DB exactly once per server process (clean demo start)."""
    db_path = "data/app.db"
    if os.path.exists(db_path):
        os.remove(db_path)


def main() -> None:
    st.set_page_config(
        page_title="PME AI Toolkit",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
    _reset_db_for_demo()
    _bootstrap()

    _render_sidebar()

    choix = st.session_state['navigation_radio']

    if choix == "🏠 Accueil":
        render_accueil_view()

    elif choix == "📊 Gestion":
        with st.expander("📝 Générateur de Factures", expanded=True):
            render_facture_view()
        st.divider()

        _render_header()
        _render_step_rail(_current_phase(), verified=st.session_state.get("batch_verified", False))

        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        disabled_reason = (
            "Ajoutez GOOGLE_API_KEY dans .env pour activer l'extraction"
            if not api_key
            else None
        )
        if disabled_reason:
            st.warning(disabled_reason)

        files, clicked = render_upload(disabled_reason=disabled_reason)

        if clicked and files:
            if st.session_state["batch_id"] is None:
                new_id = create_batch(siren=st.session_state.get("batch_siren", ""))
                st.session_state["batch_id"] = new_id
                st.session_state["invoices"] = []
                st.toast(f"Lot #{new_id} créé", icon="✅")

            def _on_invoice(invoice_id, invoice):
                st.session_state["invoices"].append((invoice_id, invoice))

            st.session_state["_processing"] = True
            process_files(
                files=files,
                batch_id=st.session_state["batch_id"],
                on_invoice=_on_invoice,
            )
            st.session_state["_processing"] = False

        render_review(st.session_state["invoices"])

        invoices_only = [inv for _id, inv in st.session_state["invoices"]]
        render_export(invoices_only, siren=st.session_state["batch_siren"])

        st.markdown(
            '<div class="fct-footer">'
            "<span>Facture · v0.4 — De la facture papier à l'écriture comptable</span>"
            "<span>Article A47 A-1 du Livre des procédures fiscales</span>"
            "</div>",
            unsafe_allow_html=True,
        )

    elif choix == "🤝 Ressources":
        with st.expander("🤝 Recrutement RH", expanded=False):
            render_rh_view()
        st.divider()
        with st.expander("🎙️ Compte-rendu Réunion", expanded=False):
            render_audio_view()

    elif choix == "🚀 Croissance":
        with st.expander("🚀 Générateur Fiches Produits", expanded=False):
            render_marketing_view()
        st.divider()
        with st.expander("💬 Copilote Service Client", expanded=False):
            render_client_view()

    elif choix == "⚙️ Paramètres":
        render_config_view()


if __name__ == "__main__":
    main()
