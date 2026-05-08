"""Upload + processing zone."""
from __future__ import annotations

import re
from typing import Callable, Iterable

import streamlit as st

from core.extractor import (
    ExtractionError,
    JsonParseError,
    MissingKeyError,
    NetworkError,
    RateLimitError,
    SchemaValidationError,
    extract,
)
from core.models import InvoiceData
from core.storage import save_invoice


ACCEPTED_TYPES = ["pdf", "png", "jpg", "jpeg"]

# Batch-killing errors: one global banner instead of per-file messages.
_BATCH_KILL_TYPES = (MissingKeyError, RateLimitError)


_UPLOAD_ICON = (
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:-0.15em;">'
    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
    '<polyline points="17 8 12 3 7 8"/>'
    '<line x1="12" y1="3" x2="12" y2="15"/></svg>'
)
_CHECKC_ICON = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:-0.15em;">'
    '<circle cx="12" cy="12" r="10"/><polyline points="9 12 11.5 14.5 16 9.5"/></svg>'
)
_CIRCLE_ICON = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:-0.15em;">'
    '<circle cx="12" cy="12" r="10"/></svg>'
)


def _zone_heading_html(step: str, title: str, sub: str) -> str:
    return (
        f'<div class="fct-zone-head">'
        f'<span class="fct-zone-step">{step}</span>'
        f'<div><h2 class="fct-zone-title">{title}</h2>'
        f'<div class="fct-zone-sub">{sub}</div></div>'
        f"</div>"
    )


def _zone_heading(step: str, title: str, sub: str) -> None:
    st.markdown(_zone_heading_html(step, title, sub), unsafe_allow_html=True)


def _friendly_error(exc: ExtractionError) -> str:
    """Return a French user-facing string for an extraction error."""
    if isinstance(exc, MissingKeyError):
        return (
            "Clé Gemini manquante. Ajoutez GOOGLE_API_KEY dans le fichier .env,"
            " puis relancez l'application."
        )
    if isinstance(exc, RateLimitError):
        return "Quota Gemini dépassé. Attendez quelques minutes avant de relancer."
    if isinstance(exc, NetworkError):
        return "Connexion interrompue. Vérifiez votre accès Internet et réessayez."
    if isinstance(exc, JsonParseError):
        return "Réponse Gemini invalide. Essayez à nouveau avec ce fichier."
    if isinstance(exc, SchemaValidationError):
        detail = _extract_validation_detail(exc)
        return f"Données invalides : {detail}. Corrigez-les dans le tableau ou réessayez."
    # Generic ExtractionError fallback
    return "Extraction impossible pour ce fichier. Retirez-le ou saisissez les données manuellement."


def _extract_validation_detail(exc: SchemaValidationError) -> str:
    """Pull a short field-level summary from a SchemaValidationError message."""
    msg = str(exc)
    # Match Pydantic v2 style: "1 validation error for InvoiceData\nfield_name\n  reason"
    m = re.search(r"(\w+)\n\s+Value error,?\s*(.+?)(?:\s+\[|$)", msg)
    if m:
        field, reason = m.group(1), m.group(2).strip()
        return f"{field} — {reason}"
    # Fallback: trim to first 80 chars to avoid dumping a wall of Pydantic text
    return msg[:80].strip()


def render_upload(disabled_reason: str | None = None) -> tuple[list, bool]:
    """Render uploader + Traiter button.

    Returns (uploaded_files, process_clicked).
    """
    _zone_heading(
        "①",
        "Déposez vos factures",
        "PDF, PNG ou JPG · Jusqu'à 50 pièces par lot · 10 Mo max par fichier",
    )

    files = st.file_uploader(
        label="Glissez vos factures ici ou parcourez le dossier",
        accept_multiple_files=True,
        type=ACCEPTED_TYPES,
        key="uploader",
        label_visibility="collapsed",
    )
    files = files or []

    n = len(files)
    label = f"Traiter {n} facture{'s' if n != 1 else ''}"
    is_disabled = bool(disabled_reason) or n == 0

    if n > 0:
        st.markdown(
            f'<div style="font-size:12.5px;color:var(--ink-3);margin:8px 0 12px;">'
            f"Extraction par Gemini Vision · ~3 s par pièce · "
            f"<strong style=\"color:var(--ink);\">{n}</strong> pièce{'s' if n > 1 else ''} prête{'s' if n > 1 else ''}"
            "</div>",
            unsafe_allow_html=True,
        )

    clicked = st.button(label, disabled=is_disabled, type="primary")
    if disabled_reason:
        st.caption(disabled_reason)
    return list(files), clicked


def process_files(
    files: Iterable,
    batch_id: int,
    on_invoice: Callable[[int, InvoiceData], None],
) -> None:
    """Process each uploaded file with custom-styled progress UI.

    Calls on_invoice(invoice_id, invoice) on every successful save so the
    caller can update session state.

    On MissingKeyError or RateLimitError, shows a single top-level st.error
    instead of per-file messages. On RateLimitError mid-batch, offers a
    "Reprendre" button to retry only the failed files.
    """
    files = list(files)
    total = len(files)
    if total == 0:
        return

    heading_slot = st.empty()

    def _update_heading(done: int) -> None:
        heading_slot.markdown(
            _zone_heading_html(
                "②",
                "Extraction en cours",
                f"{done} / {total} pièce{'s' if total > 1 else ''} traitée{'s' if done > 1 else ''}",
            ),
            unsafe_allow_html=True,
        )

    _update_heading(0)

    # Skeleton table preview during extraction.
    skel_slot = st.empty()
    skel_slot.markdown(
        f"""
<div class="fct-skel-card">
  <div class="fct-skel-eyebrow">Aperçu de la table</div>
  {''.join(
      f'<div class="fct-skel-row">'
      + ''.join(f'<span class="fct-sk" style="opacity:{1 - i*0.2:.1f};"></span>' for _ in range(6))
      + '</div>'
      for i in range(3)
  )}
</div>
""",
        unsafe_allow_html=True,
    )

    progress = st.progress(0.0, text=f"0 / {total}")
    rows_slot = st.empty()
    failed_files: list = []
    statuses: list[str] = ["idle"] * total  # 'idle' | 'doing' | 'ok' | 'err'

    def _render_rows() -> None:
        parts: list[str] = []
        for idx, f in enumerate(files):
            state = statuses[idx]
            if state == "ok":
                dot = f'<span class="fct-proc-dot ok">{_CHECKC_ICON}</span>'
                state_label = "extrait"
                row_cls = ""
                name_cls = ""
            elif state == "doing":
                dot = f'<span class="fct-proc-dot doing">{_CIRCLE_ICON}</span>'
                state_label = "lecture…"
                row_cls = "doing"
                name_cls = ""
            elif state == "err":
                dot = '<span class="fct-proc-dot" style="color:var(--error);">' + _CIRCLE_ICON + "</span>"
                state_label = "échec"
                row_cls = ""
                name_cls = ""
            else:
                dot = f'<span class="fct-proc-dot idle">{_CIRCLE_ICON}</span>'
                state_label = "en attente"
                row_cls = ""
                name_cls = "idle"
            # escape file name lightly
            safe_name = (f.name or "").replace("<", "&lt;").replace(">", "&gt;")
            parts.append(
                f'<div class="fct-proc-row {row_cls}">'
                f"{dot}"
                f'<span class="fct-proc-name {name_cls}">{safe_name}</span>'
                f'<span class="fct-proc-state">{state_label}</span>'
                f"</div>"
            )
        rows_slot.markdown(
            f'<div style="margin-top:6px;">{"".join(parts)}</div>',
            unsafe_allow_html=True,
        )

    _render_rows()

    for i, f in enumerate(files, start=1):
        statuses[i - 1] = "doing"
        _render_rows()
        progress.progress((i - 1) / total, text=f"{i - 1} / {total}")
        filename = f.name
        try:
            file_bytes = f.getvalue()
            invoice = extract(file_bytes, filename)
            invoice_id = save_invoice(batch_id, invoice)
            on_invoice(invoice_id, invoice)
            statuses[i - 1] = "ok"
        except _BATCH_KILL_TYPES as e:
            # Abort the whole batch; show one top-level banner.
            statuses[i - 1] = "err"
            _render_rows()
            progress.empty()
            skel_slot.empty()
            msg = _friendly_error(e)
            st.error(msg)
            # For rate limits: offer to retry remaining files.
            if isinstance(e, RateLimitError):
                remaining = files[i - 1 :]  # current file + unprocessed
                if remaining and st.button("Reprendre", key=f"retry_{batch_id}"):
                    process_files(remaining, batch_id, on_invoice)
            return
        except ExtractionError as e:
            msg = _friendly_error(e)
            statuses[i - 1] = "err"
            failed_files.append(f)
            st.warning(f"Échec — {filename} : {msg}")
        except Exception as e:  # noqa: BLE001 — UI must not crash mid-batch
            statuses[i - 1] = "err"
            failed_files.append(f)
            st.warning(f"Erreur inattendue — {filename} : {e}")
        _render_rows()
        progress.progress(i / total, text=f"{i} / {total}")
        _update_heading(i)

    progress.empty()
    skel_slot.empty()
