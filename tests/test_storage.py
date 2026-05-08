"""Tests for core.storage."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from core.storage import (
    create_batch,
    get_batch_invoices,
    init_db,
    list_batches,
    save_invoice,
    update_invoice_field,
)


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


def test_init_and_create_batch(db_path):
    init_db(db_path)
    bid = create_batch("test batch", db_path=db_path)
    assert bid >= 1
    batches = list_batches(db_path=db_path)
    assert len(batches) == 1
    assert batches[0]["name"] == "test batch"


def test_save_and_get_invoice(db_path, sample_invoice):
    bid = create_batch("b1", db_path=db_path)
    sample_invoice.confidence = {"supplier_name": 0.9}
    iid = save_invoice(bid, sample_invoice, db_path=db_path)
    assert iid >= 1
    invoices = get_batch_invoices(bid, db_path=db_path)
    assert len(invoices) == 1
    got = invoices[0]
    assert got.supplier_name == sample_invoice.supplier_name
    assert got.supplier_siret == sample_invoice.supplier_siret
    assert got.amount_ht == sample_invoice.amount_ht
    assert got.invoice_date == sample_invoice.invoice_date
    assert got.confidence == {"supplier_name": 0.9}


def test_update_invoice_field_valid(db_path, sample_invoice):
    bid = create_batch(db_path=db_path)
    iid = save_invoice(bid, sample_invoice, db_path=db_path)
    update_invoice_field(iid, "supplier_name", "NewName", db_path=db_path)
    invoices = get_batch_invoices(bid, db_path=db_path)
    assert invoices[0].supplier_name == "NewName"


def test_update_invoice_field_decimal(db_path, sample_invoice):
    bid = create_batch(db_path=db_path)
    iid = save_invoice(bid, sample_invoice, db_path=db_path)
    update_invoice_field(iid, "amount_ht", Decimal("250.50"), db_path=db_path)
    invoices = get_batch_invoices(bid, db_path=db_path)
    assert invoices[0].amount_ht == Decimal("250.50")


def test_update_invoice_field_invalid_raises(db_path, sample_invoice):
    bid = create_batch(db_path=db_path)
    iid = save_invoice(bid, sample_invoice, db_path=db_path)
    with pytest.raises(ValueError):
        update_invoice_field(iid, "id; DROP TABLE invoices", "x", db_path=db_path)


def test_list_batches_ordering(db_path):
    init_db(db_path)
    create_batch("first", db_path=db_path)
    create_batch("second", db_path=db_path)
    batches = list_batches(db_path=db_path)
    assert len(batches) == 2
    assert batches[0]["name"] == "second"  # DESC order
