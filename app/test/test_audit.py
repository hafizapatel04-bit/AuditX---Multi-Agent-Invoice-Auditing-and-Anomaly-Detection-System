from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import AuditResult, Invoice, InvoiceStatus, Policy, Vendor, VendorStatus
from app.services import audit as audit_module
from app.services.audit import run_audit


@pytest.fixture(autouse=True)
def no_anomaly(monkeypatch):
    monkeypatch.setattr(audit_module, "run_anomaly", lambda invoice: None)


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add_all([
        Vendor(name="Tasty Bites Catering", status=VendorStatus.approved),
        Policy(name="Auto", min_amount=0, max_amount=60000, approval_level="normal"),
        Policy(name="Manager", min_amount=60000, max_amount=150000,
               approval_level="manager_approval_required"),
        Policy(name="Finance", min_amount=150000, max_amount=None,
               approval_level="finance_review"),
    ])
    db.commit()
    return db


def add(db, **overrides):
    data = dict(vendor_name="Tasty Bites Catering", invoice_number="INV2001",
                invoice_date=date(2026, 7, 22), subtotal=3395.73, tax_amount=611.23,
                amount=4006.96, currency="INR", category="Food", line_items=[])
    data.update(overrides)
    inv = Invoice(**data)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def test_clean_invoice_is_approved():
    db = make_db()
    result = run_audit(db, add(db))
    assert result.final_status == InvoiceStatus.approved
    assert result.reasons == []


def test_unknown_vendor_is_flagged():
    db = make_db()
    result = run_audit(db, add(db, vendor_name="Zenith Global Traders"))
    assert result.vendor_check == "unknown"
    assert result.final_status == InvoiceStatus.flagged


def test_wrong_total_is_flagged():
    db = make_db()
    result = run_audit(db, add(db, amount=4800.00))
    assert result.total_check == "mismatch"
    assert result.final_status == InvoiceStatus.flagged


def test_missing_totals_are_unchecked_not_flagged():
    db = make_db()
    result = run_audit(db, add(db, subtotal=None, tax_amount=None))
    assert result.total_check == "unchecked"
    assert result.final_status == InvoiceStatus.approved


def test_duplicate_is_flagged():
    db = make_db()
    run_audit(db, add(db))
    result = run_audit(db, add(db))
    assert result.duplicate_check == "exact_duplicate"
    assert result.final_status == InvoiceStatus.flagged


def test_only_policy_flag_means_needs_review():
    db = make_db()
    result = run_audit(db, add(db, subtotal=67796.61, tax_amount=12203.39, amount=80000.00))
    assert result.policy_check == "manager_approval_required"
    assert result.final_status == InvoiceStatus.needs_review


def test_missing_field_is_flagged():
    db = make_db()
    result = run_audit(db, add(db, invoice_number=None))
    assert result.fields_check == "missing"
    assert result.details["missing_fields"] == ["invoice_number"]
    assert result.final_status == InvoiceStatus.flagged


def test_anomaly_is_flagged(monkeypatch):
    monkeypatch.setattr(audit_module, "run_anomaly",
                        lambda inv: {"is_anomaly": True, "reason": "Far above normal"})
    db = make_db()
    result = run_audit(db, add(db))
    assert result.final_status == InvoiceStatus.flagged
    assert "Far above normal" in result.reasons


def test_rerun_updates_same_row():
    db = make_db()
    invoice = add(db)
    run_audit(db, invoice)
    run_audit(db, invoice)
    assert db.query(AuditResult).count() == 1

def test_unreadable_invoice_number_flag_goes_to_review():
    db = make_db()
    result = run_audit(db, add(db, invoice_number="INV 20O1",
                               review_flags=["invoice number missing or unreadable"]))
    assert result.final_status == InvoiceStatus.flagged
    assert "invoice number missing or unreadable" in result.reasons


def test_arithmetic_flag_from_extraction_is_ignored():
    db = make_db()
    result = run_audit(db, add(db, review_flags=["subtotal + tax does not equal total"]))
    assert result.final_status == InvoiceStatus.approved