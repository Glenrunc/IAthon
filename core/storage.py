"""SQLite persistence for batches and invoices."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from core.models import InvoiceData


_DEFAULT_DB = "data/app.db"

_INVOICE_COLUMNS = {
    "source_filename",
    "supplier_name",
    "supplier_siret",
    "supplier_vat_number",
    "invoice_number",
    "invoice_date",
    "amount_ht",
    "amount_vat",
    "amount_ttc",
    "vat_rate",
    "currency",
    "confidence_json",
}


def _connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate_db(conn: sqlite3.Connection) -> None:
    """Add new columns to existing tables without breaking existing data."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(batches)").fetchall()}
    if "siren" not in existing:
        conn.execute("ALTER TABLE batches ADD COLUMN siren TEXT NOT NULL DEFAULT ''")
    if "verified" not in existing:
        conn.execute("ALTER TABLE batches ADD COLUMN verified INTEGER NOT NULL DEFAULT 0")
    conn.commit()


def init_db(path: str = _DEFAULT_DB) -> None:
    """Create directories + tables if missing."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = _connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS batches (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS invoices (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              batch_id INTEGER NOT NULL,
              source_filename TEXT NOT NULL,
              supplier_name TEXT NOT NULL,
              supplier_siret TEXT,
              supplier_vat_number TEXT,
              invoice_number TEXT NOT NULL,
              invoice_date TEXT NOT NULL,
              amount_ht TEXT NOT NULL,
              amount_vat TEXT NOT NULL,
              amount_ttc TEXT NOT NULL,
              vat_rate TEXT,
              currency TEXT NOT NULL DEFAULT 'EUR',
              confidence_json TEXT NOT NULL DEFAULT '{}',
              FOREIGN KEY (batch_id) REFERENCES batches(id)
            );
            """
        )
        conn.commit()
        _migrate_db(conn)
    finally:
        conn.close()


def create_batch(
    name: Optional[str] = None,
    siren: str = "",
    db_path: str = _DEFAULT_DB,
) -> int:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO batches (name, siren, created_at) VALUES (?, ?, ?)",
            (name, siren, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def update_batch(
    batch_id: int,
    siren: Optional[str] = None,
    verified: Optional[bool] = None,
    db_path: str = _DEFAULT_DB,
) -> None:
    updates, values = [], []
    if siren is not None:
        updates.append("siren = ?")
        values.append(siren)
    if verified is not None:
        updates.append("verified = ?")
        values.append(1 if verified else 0)
    if not updates:
        return
    values.append(batch_id)
    conn = _connect(db_path)
    try:
        conn.execute(f"UPDATE batches SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def delete_batch(batch_id: int, db_path: str = _DEFAULT_DB) -> None:
    conn = _connect(db_path)
    try:
        conn.execute("DELETE FROM invoices WHERE batch_id = ?", (batch_id,))
        conn.execute("DELETE FROM batches WHERE id = ?", (batch_id,))
        conn.commit()
    finally:
        conn.close()


def save_invoice(
    batch_id: int,
    invoice: InvoiceData,
    db_path: str = _DEFAULT_DB,
) -> int:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO invoices (
              batch_id, source_filename, supplier_name, supplier_siret,
              supplier_vat_number, invoice_number, invoice_date,
              amount_ht, amount_vat, amount_ttc, vat_rate, currency,
              confidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_id,
                invoice.source_filename,
                invoice.supplier_name,
                invoice.supplier_siret,
                invoice.supplier_vat_number,
                invoice.invoice_number,
                invoice.invoice_date.isoformat(),
                str(invoice.amount_ht),
                str(invoice.amount_vat),
                str(invoice.amount_ttc),
                str(invoice.vat_rate) if invoice.vat_rate is not None else None,
                invoice.currency,
                json.dumps(invoice.confidence),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def update_invoice_field(
    invoice_id: int,
    field: str,
    value: Any,
    db_path: str = _DEFAULT_DB,
) -> None:
    if field not in _INVOICE_COLUMNS:
        raise ValueError(f"Field '{field}' is not updatable")
    if isinstance(value, Decimal):
        value = str(value)
    elif isinstance(value, date) and not isinstance(value, datetime):
        value = value.isoformat()
    elif isinstance(value, dict):
        value = json.dumps(value)
    conn = _connect(db_path)
    try:
        # `field` is whitelisted — safe to interpolate as identifier.
        conn.execute(
            f"UPDATE invoices SET {field} = ? WHERE id = ?",  # noqa: S608
            (value, invoice_id),
        )
        conn.commit()
    finally:
        conn.close()


def _row_to_invoice(row: sqlite3.Row) -> InvoiceData:
    return InvoiceData(
        supplier_name=row["supplier_name"],
        supplier_siret=row["supplier_siret"],
        supplier_vat_number=row["supplier_vat_number"],
        invoice_number=row["invoice_number"],
        invoice_date=date.fromisoformat(row["invoice_date"]),
        amount_ht=Decimal(row["amount_ht"]),
        amount_vat=Decimal(row["amount_vat"]),
        amount_ttc=Decimal(row["amount_ttc"]),
        vat_rate=Decimal(row["vat_rate"]) if row["vat_rate"] else None,
        currency=row["currency"],
        confidence=json.loads(row["confidence_json"] or "{}"),
        source_filename=row["source_filename"],
    )


def get_batch_invoices(batch_id: int, db_path: str = _DEFAULT_DB) -> list[InvoiceData]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM invoices WHERE batch_id = ? ORDER BY id",
            (batch_id,),
        ).fetchall()
        return [_row_to_invoice(r) for r in rows]
    finally:
        conn.close()


def get_batch_records(
    batch_id: int, db_path: str = _DEFAULT_DB
) -> list[tuple[int, InvoiceData]]:
    """Return (invoice_id, InvoiceData) pairs for a batch, ordered by id."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM invoices WHERE batch_id = ? ORDER BY id",
            (batch_id,),
        ).fetchall()
        return [(row["id"], _row_to_invoice(row)) for row in rows]
    finally:
        conn.close()


def list_batches(db_path: str = _DEFAULT_DB) -> list[dict]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT b.id, b.name, b.siren, b.verified, b.created_at,
                   COUNT(i.id) AS invoice_count
            FROM batches b
            LEFT JOIN invoices i ON i.batch_id = b.id
            GROUP BY b.id
            ORDER BY b.id DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
