"""FEC export zone: preview + validation + download button."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from html import escape

import streamlit as st

from core.fec_writer import (
    FECValidationError,
    fec_filename,
    validate_fec_output,
    write_fec,
)
from core.models import InvoiceData


PREVIEW_LINES = 10


_CHECKC_SVG = (
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:-0.15em;">'
    '<circle cx="12" cy="12" r="10"/><polyline points="9 12 11.5 14.5 16 9.5"/></svg>'
)
_ALERT_SVG = (
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:-0.15em;">'
    '<path d="M12 9v4"/><path d="M12 17h.01"/>'
    '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
    "</svg>"
)
_CHECK_SMALL = (
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:-0.15em;">'
    '<polyline points="20 6 9 17 4 12"/></svg>'
)
_X_SMALL = (
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:-0.15em;">'
    '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
)
_FEC_SVG = (
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:-0.15em;">'
    '<rect x="3" y="3" width="18" height="18" rx="2"/>'
    '<line x1="3" y1="9" x2="21" y2="9"/>'
    '<line x1="9" y1="21" x2="9" y2="9"/></svg>'
)


def _zone_heading(step: str, title: str, sub: str) -> None:
    st.markdown(
        f"""
<div class="fct-zone-head">
  <span class="fct-zone-step" style="color:var(--accent);">{step}</span>
  <div>
    <h2 class="fct-zone-title">{title}</h2>
    <div class="fct-zone-sub">{sub}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_fec_preview(text: str, filename: str, total_lines: int) -> None:
    """Dark monospace card with line numbers + soft scroll."""
    preview = text.split("\r\n")[:PREVIEW_LINES]
    line_html = "".join(
        f'<span class="fct-line {"fct-head-line" if i == 0 else ""}">'
        f"{escape(line)}</span>\n"
        for i, line in enumerate(preview)
    )
    st.markdown(
        f"""
<div class="fct-fec-card">
  <div class="fct-fec-head">
    <span class="fct-fec-name">{_FEC_SVG}{escape(filename)}</span>
    <span>aperçu · {len(preview)} / {total_lines} lignes</span>
  </div>
  <pre class="fct-fec-pre">{line_html}</pre>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_validation_hero(
    valid: bool, errors: list[str], n_invoices: int, period: str, siren: str
) -> None:
    """Render the hero validation card (green Conforme FEC ✓ or red errors)."""
    if valid:
        cls_card = "ok"
        cls_head = "ok"
        title = "FEC valide · prêt à exporter"
        items = [
            (True, "Structure 18 colonnes (DGFiP, art. A47 A-1)"),
            (True, "Équilibre débit / crédit par écriture"),
            (True, f"SIREN déclarant valide ({siren})"),
            (True, f"Période continue · {n_invoices} pièce{'s' if n_invoices > 1 else ''} · {period}"),
            (True, "Tous les champs obligatoires renseignés"),
        ]
    else:
        cls_card = "err"
        cls_head = "err"
        n_err = len(errors)
        title = f"{n_err} erreur{'s' if n_err > 1 else ''} de validation"
        items = [(False, err) for err in errors]

    items_html = "".join(
        f'<li class="{"ok" if ok else "err"}">'
        f'<span style="margin-top:2px;line-height:0;color:{"var(--success)" if ok else "var(--error)"};">'
        f'{_CHECK_SMALL if ok else _X_SMALL}</span>'
        f"<span>{escape(text)}</span></li>"
        for ok, text in items
    )
    st.markdown(
        f"""
<div class="fct-val-hero {cls_card}">
  <div class="fct-val-head {cls_head}">
    {_CHECKC_SVG if valid else _ALERT_SVG}
    {escape(title)}
  </div>
  <ul class="fct-val-list">{items_html}</ul>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_stats(n_lines: int, total_ttc: Decimal) -> None:
    """Two small stat cards: écritures + Total TTC."""
    ttc_str = f"{total_ttc:,.2f} €".replace(",", " ").replace(".", ",")
    st.markdown(
        f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;">
  <div style="background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:10px 12px;">
    <div style="font-size:11px;letter-spacing:.06em;text-transform:uppercase;
         color:var(--ink-3);font-weight:600;">Écritures</div>
    <div style="margin-top:2px;font-family:var(--font-display);font-weight:600;
         font-size:18px;color:var(--ink);font-variant-numeric:tabular-nums;">{n_lines}</div>
  </div>
  <div style="background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:10px 12px;">
    <div style="font-size:11px;letter-spacing:.06em;text-transform:uppercase;
         color:var(--ink-3);font-weight:600;">Total TTC</div>
    <div style="margin-top:2px;font-family:var(--font-mono);font-weight:600;
         font-size:18px;color:var(--ink);font-variant-numeric:tabular-nums;">{ttc_str}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_toast() -> None:
    """One-shot success toast on FEC download."""
    st.markdown(
        """
<div style="position:fixed;bottom:28px;left:50%;transform:translateX(-50%);
     background:var(--ink);color:var(--bg);padding:12px 18px;border-radius:10px;
     display:flex;align-items:center;gap:12px;
     box-shadow:0 12px 32px -12px rgba(11,31,58,.5);
     z-index:50;animation:toastIn .3s ease both;font-size:13.5px;">
  <span style="color:#7DD3A4;line-height:0;">"""
        + _CHECKC_SVG
        + """</span>
  <div>
    <div style="font-weight:600;">FEC téléchargé</div>
    <div style="opacity:.7;font-size:12px;margin-top:1px;">
      Prêt pour Sage / EBP / Cegid / Pennylane / OpenConcerto
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_export(invoices: list[InvoiceData], siren: str) -> None:
    if not invoices:
        _zone_heading(
            "④",
            "Exportez le fichier FEC",
            "Aucune facture à exporter pour le moment.",
        )
        st.button("Générer FEC", disabled=True)
        return

    today = date.today()

    try:
        fec_bytes = write_fec(invoices, siren=siren, batch_date=today)
    except FECValidationError as e:
        _zone_heading("④", "Exportez le fichier FEC", "Génération impossible.")
        st.error(f"FEC invalide: {e}")
        return
    except Exception as e:  # noqa: BLE001
        _zone_heading("④", "Exportez le fichier FEC", "Génération impossible.")
        st.error(f"Erreur génération FEC: {e}")
        return

    errors = validate_fec_output(fec_bytes)
    valid = not errors

    _zone_heading(
        "④",
        "Exportez le fichier FEC",
        "Format légal · 18 colonnes · prêt pour Sage, EBP, Cegid, Pennylane, OpenConcerto.",
    )

    text = fec_bytes.decode("utf-8-sig")
    n_lines = text.count("\r\n") + (0 if text.endswith("\r\n") else 1)
    filename = fec_filename(siren, today)
    total_ttc = sum(
        (inv.amount_ttc for inv in invoices),
        start=Decimal("0"),
    )
    period = f"01/{today.month:02d}/{today.year} – {today.day:02d}/{today.month:02d}/{today.year}"

    # Two-column layout: preview (left), hero + button (right).
    left, right = st.columns([1.4, 1])

    with left:
        _render_fec_preview(text, filename, n_lines)

    with right:
        _render_validation_hero(valid, errors, len(invoices), period, siren)
        _render_stats(n_lines, total_ttc)

        clicked = st.download_button(
            label="⤓  Télécharger le FEC",
            data=fec_bytes,
            file_name=filename,
            mime="text/plain",
            type="primary",
            disabled=not valid,
            use_container_width=True,
        )
        st.markdown(
            '<div style="font-size:11.5px;color:var(--ink-3);text-align:center;margin-top:6px;">'
            "Le fichier reste accessible 30 jours dans « Lots récents »."
            "</div>",
            unsafe_allow_html=True,
        )

        if clicked:
            st.session_state["_just_exported"] = True
            _render_toast()
