from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Vendor, VendorStatus
from app.services.vendor_check import verify_vendor


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add_all([
        Vendor(name="Apex IT Solutions", status=VendorStatus.approved),
        Vendor(name="FastCash Traders", status=VendorStatus.blocked),
    ])
    db.commit()
    return db


def test_approved():
    assert verify_vendor(make_db(), "Apex IT Solutions")["result"] == "approved"


def test_case_insensitive():
    assert verify_vendor(make_db(), "APEX IT SOLUTIONS")["result"] == "approved"


def test_typo_still_matches():
    assert verify_vendor(make_db(), "Apex IT Solution")["result"] == "approved"


def test_blocked():
    assert verify_vendor(make_db(), "FastCash Traders")["result"] == "blocked"


def test_unknown():
    assert verify_vendor(make_db(), "Random Company")["result"] == "unknown"