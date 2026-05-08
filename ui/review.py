"""Review table with low-confidence highlights + inline edit persistence."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
import streamlit as st

from core.models import InvoiceData
from core.storage import update_batch, update_invoice_field


# Display column → InvoiceData attribute → confidence key
COLUMN_MAP: list[tuple[str, str, str | None]] = [
    ("file", "source_filename", None),
    ("fournisseur", "supplier_name", "supplier_name"),
    ("SIRET", "supplier_siret", "supplier_siret"),
    ("TVA", "supplier_vat_number", "supplier_vat_number"),
    ("date", "invoice_date", "invoice_date"),
    ("HT", "amount_ht", "amount_ht"),
    ("TVA EUR", "amount_vat", "amount_vat"),
    ("TTC", "amount_ttc", "amount_ttc"),
    ("conf", None, None),
    ("source", "source_filename", None),
]

DISPLAY_COLS = [c[0] for c in COLUMN_MAP]
DISABLED_COLS = ["file", "conf", "source"]
LOW_CONF_THRESHOLD = 0.7
# Warm-amber subtle treatment (replaces former #ffcccc red).
LOW_CONF_BG = (
    "background-color: #FBF1D9; "
    "color: #6B4F12; "
    "border-left: 2px solid #E6CD8A;"
)


_ALERT_SVG = (
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:-0.15em;">'
    '<path d="M12 9v4"/><path d="M12 17h.01"/>'
    '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
    "</svg>"
)


# Storage column names (writable per core.storage._INVOICE_COLUMNS)
ATTR_TO_DB_FIELD = {
    "supplier_name": "supplier_name",
    "supplier_siret": "supplier_siret",
    "supplier_vat_number": "supplier_vat_number",
    "invoice_date": "invoice_date",
    "amount_ht": "amount_ht",
    "amount_vat": "amount_vat",
    "amount_ttc": "amount_ttc",
}

_FIELD_REASONS = {
    "supplier_name": "Nom de fournisseur partiellement illisible",
    "supplier_siret": "SIRET non détecté ou invalide",
    "supplier_vat_number": "Numéro TVA absent ou format inattendu",
    "invoice_date": "Date d'émission non détectée",
    "amount_ht": "Montant HT incertain — image floue",
    "amount_vat": "TVA en € incertaine — recoupez avec HT × taux",
    "amount_ttc": "TTC à confirmer",
}

_FIELD_LABELS = {
    "supplier_name": "Fournisseur",
    "supplier_siret": "SIRET",
    "supplier_vat_number": "TVA",
    "invoice_date": "Date",
    "amount_ht": "HT",
    "amount_vat": "TVA €",
    "amount_ttc": "TTC",
}


def _zone_heading(step: str, title: str, sub: str) -> None:
    st.markdown(
        f"""
<div class="fct-zone-head">
  <span class="fct-zone-step">{step}</span>
  <div>
    <h2 class="fct-zone-title">{title}</h2>
    <div class="fct-zone-sub">{sub}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _row_min_conf(conf: dict[str, float]) -> float:
    if not conf:
        return 1.0
    return min(conf.values())


def _to_dataframe(records: list[tuple[int, InvoiceData]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _inv_id, inv in records:
        row_conf = _row_min_conf(inv.confidence)
        # Prefix file with a small marker for low-confidence rows so users
        # spot them at a glance even within st.data_editor (which does not
        # render HTML inside cells).
        has_low = any(
            inv.confidence.get(k, 1.0) < LOW_CONF_THRESHOLD
            for k in _FIELD_LABELS
        )
        marker = "⚠ " if has_low else ""
        rows.append(
            {
                "file": f"{marker}{inv.source_filename}",
                "fournisseur": inv.supplier_name,
                "SIRET": inv.supplier_siret or "",
                "TVA": inv.supplier_vat_number or "",
                "date": inv.invoice_date,
                "HT": str(inv.amount_ht),
                "TVA EUR": str(inv.amount_vat),
                "TTC": str(inv.amount_ttc),
                "conf": round(row_conf, 2),
                "source": inv.source_filename,
            }
        )
    return pd.DataFrame(rows, columns=DISPLAY_COLS)


def _style_low_conf(records: list[tuple[int, InvoiceData]], df: pd.DataFrame):
    """Per-cell highlight where the field's confidence < threshold (warm-amber)."""

    def _styler(_df: pd.DataFrame) -> pd.DataFrame:
        styles = pd.DataFrame("", index=_df.index, columns=_df.columns)
        for row_idx, (_inv_id, inv) in enumerate(records):
            conf = inv.confidence or {}
            for col_name, _attr, conf_key in COLUMN_MAP:
                if conf_key is None:
                    continue
                if conf.get(conf_key, 1.0) < LOW_CONF_THRESHOLD:
                    if col_name in styles.columns:
                        styles.iloc[row_idx, styles.columns.get_loc(col_name)] = LOW_CONF_BG
        return styles

    return df.style.apply(_styler, axis=None)


def _render_flag_summary(records: list[tuple[int, InvoiceData]]) -> int:
    """Render warm-amber preview cards for any row with low-confidence fields.

    Returns the count of rows flagged.
    """
    flagged = 0
    cards: list[str] = []
    for _inv_id, inv in records:
        low = {
            k: round(v * 100)
            for k, v in (inv.confidence or {}).items()
            if v < LOW_CONF_THRESHOLD and k in _FIELD_LABELS
        }
        if not low:
            continue
        flagged += 1
        chips = "".join(
            f'<span class="fct-flag-chip" title="{_FIELD_REASONS.get(k, "")}">'
            f"{_FIELD_LABELS[k]} · {pct}%"
            "</span>"
            for k, pct in low.items()
        )
        reasons = " · ".join(_FIELD_REASONS.get(k, "") for k in low)
        cards.append(
            f"""
<div class="fct-flag-preview">
  <span class="fct-flag-icon">{_ALERT_SVG}</span>
  <div class="fct-flag-body">
    <div class="fct-flag-title" title="{reasons}">{inv.source_filename}</div>
    <div style="font-size:11.5px;opacity:.85;">{reasons}</div>
    <div class="fct-flag-fields">{chips}</div>
  </div>
</div>
"""
        )
    if cards:
        st.markdown("".join(cards), unsafe_allow_html=True)
    return flagged


def _coerce(attr: str, raw: Any) -> Any:
    """Coerce edited cell into the type InvoiceData expects."""
    if raw is None:
        return None
    if attr in ("supplier_siret", "supplier_vat_number"):
        s = str(raw).strip()
        return s if s else None
    if attr == "invoice_date":
        if isinstance(raw, date):
            return raw
        return date.fromisoformat(str(raw))
    if attr in ("amount_ht", "amount_vat", "amount_ttc"):
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"montant invalide: {raw}") from e
    return str(raw)


def _apply_edits(
    records: list[tuple[int, InvoiceData]],
    edited_df: pd.DataFrame,
) -> int:
    """Detect cell-level changes and persist them. Returns number of writes."""
    writes = 0
    for row_idx, (inv_id, inv) in enumerate(records):
        for col_name, attr, _conf_key in COLUMN_MAP:
            if attr is None or col_name in DISABLED_COLS:
                continue
            db_field = ATTR_TO_DB_FIELD.get(attr)
            if db_field is None:
                continue
            new_raw = edited_df.iloc[row_idx][col_name]
            current = getattr(inv, attr)

            # Normalize for comparison
            try:
                new_val = _coerce(attr, new_raw)
            except ValueError as e:
                st.warning(f"Ligne {row_idx + 1} {col_name}: {e}")
                continue

            # Compare in a type-tolerant way
            if isinstance(current, Decimal) and isinstance(new_val, Decimal):
                changed = current != new_val
            elif current is None and (new_val is None or new_val == ""):
                changed = False
            else:
                changed = current != new_val

            if not changed:
                continue

            try:
                setattr(inv, attr, new_val)  # validate via pydantic
            except Exception as e:  # noqa: BLE001
                st.warning(f"Ligne {row_idx + 1} {col_name} invalide: {e}")
                continue

            update_invoice_field(inv_id, db_field, new_val)
            writes += 1
    return writes


def render_review(records: list[tuple[int, InvoiceData]]) -> int:
    """Render the editable review table. Returns the number of writes applied."""
    if not records:
        _zone_heading(
            "③",
            "Vérifiez les écritures",
            "Aucune facture extraite. Déposez et lancez le traitement.",
        )
        st.info("Aucune facture extraite. Uploadez et lancez le traitement.")
        return 0

    # Count flagged fields for the sub-line.
    low_count = sum(
        1
        for _id, inv in records
        for k, v in (inv.confidence or {}).items()
        if v < LOW_CONF_THRESHOLD and k in _FIELD_LABELS
    )
    flagged_rows = sum(
        1
        for _id, inv in records
        if any(
            (inv.confidence or {}).get(k, 1.0) < LOW_CONF_THRESHOLD
            for k in _FIELD_LABELS
        )
    )

    if low_count > 0:
        sub = (
            f"{flagged_rows} pièce{'s' if flagged_rows > 1 else ''} à vérifier · "
            f"{low_count} champ{'s' if low_count > 1 else ''} signalé{'s' if low_count > 1 else ''}"
        )
    else:
        sub = "Toutes les extractions sont fiables. Vous pouvez exporter."

    _zone_heading("③", "Vérifiez les écritures", sub)

    # Read-only warm-amber preview cards above the editor.
    _render_flag_summary(records)

    # Verification checkbox
    def _save_verified() -> None:
        bid = st.session_state.get("batch_id")
        if bid is not None:
            update_batch(bid, verified=st.session_state.get("batch_verified", False))

    st.markdown('<div class="fct-verify-wrap">', unsafe_allow_html=True)
    st.checkbox(
        "✓  Données vérifiées — prêt pour l'export FEC",
        key="batch_verified",
        on_change=_save_verified,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    df = _to_dataframe(records)
    styled = _style_low_conf(records, df)

    st.markdown('<div class="fct-fade-up">', unsafe_allow_html=True)
    edited_df = st.data_editor(
        styled,
        disabled=DISABLED_COLS,
        hide_index=True,
        use_container_width=True,
        key="review_editor",
        column_config={
            "fournisseur": st.column_config.TextColumn(
                "Fournisseur",
                help="Cliquez pour modifier. Les cellules en ambre indiquent une confiance < 70 %.",
            ),
            "SIRET": st.column_config.TextColumn(
                "SIRET",
                help="14 chiffres · validation Luhn.",
            ),
            "TVA": st.column_config.TextColumn(
                "N° TVA",
                help="Format INSEE : FR + 2 caractères + 9 chiffres.",
            ),
            "date": st.column_config.DateColumn("Date", help="Date d'émission"),
            "HT": st.column_config.TextColumn("HT", help="Montant hors taxes (€)"),
            "TVA EUR": st.column_config.TextColumn("TVA €", help="Montant TVA (€)"),
            "TTC": st.column_config.TextColumn("TTC", help="Montant toutes taxes (€)"),
            "conf": st.column_config.NumberColumn(
                "Conf.",
                help="Confiance minimale parmi les champs",
                format="%.0f%%",
            ),
            "file": st.column_config.TextColumn(
                "Pièce",
                help="⚠ indique une ligne avec champ(s) à vérifier.",
            ),
        },
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if isinstance(edited_df, pd.io.formats.style.Styler):
        edited_df = edited_df.data
    return _apply_edits(records, edited_df)
