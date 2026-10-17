from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Invoice
from app.services.duplicate_check import check_duplicate


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def add(db, vendor="Tasty Bites Catering", number="INV2001", amount=4006.96,
        d=date(2026, 7, 22)):
    inv = Invoice(vendor_name=vendor, invoice_number=number, amount=amount,
                  invoice_date=d, line_items=[])
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def test_original_is_not_flagged():
    db = make_db()
    assert check_duplicate(db, add(db))["result"] == "no_duplicate"


def test_exact_copy_is_flagged():
    db = make_db()
    original = add(db)
    result = check_duplicate(db, add(db))
    assert result["result"] == "exact_duplicate"
    assert result["match_id"] == original.id


def test_number_format_difference_still_matches():
    db = make_db()
    add(db, number="INV2001")
    assert check_duplicate(db, add(db, number="inv-2001"))["result"] == "exact_duplicate"


def test_same_number_different_vendor_is_ok():
    db = make_db()
    add(db)
    other = add(db, vendor="Metro Office Mart", amount=100, d=date(2026, 1, 1))
    assert check_duplicate(db, other)["result"] == "no_duplicate"


def test_same_amount_and_date_different_number_is_possible():
    db = make_db()
    add(db)
    assert check_duplicate(db, add(db, number="INV9999"))["result"] == "possible_duplicate"


def test_same_amount_two_months_apart_is_ok():
    db = make_db()
    add(db)
    later = add(db, number="INV2050", d=date(2026, 9, 22))
    assert check_duplicate(db, later)["result"] == "no_duplicate"


def test_failed_extraction_is_unchecked():
    db = make_db()
    failed = add(db, vendor="UNKNOWN", number=None, amount=None, d=None)
    assert check_duplicate(db, failed)["result"] == "unchecked"