import csv
from pathlib import Path

from app.database import SessionLocal
from app.models import Policy, Vendor, VendorStatus

CSV_PATH = Path(__file__).resolve().parents[1] / "sample_data" / "vendors.csv"

# (name, category, min_amount, max_amount, approval_level)
SEED_POLICIES = [
    ("Auto-approve", None, 0, 60000, "normal"),
    ("Manager approval", None, 60000, 150000, "manager_approval_required"),
    ("Finance review", None, 150000, None, "finance_review"),
]


def seed_vendors():
    db = SessionLocal()
    try:
        if db.query(Vendor).count() > 0:
            return
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                ok = r["approved"].strip().lower() == "true"
                status = VendorStatus.approved if ok else VendorStatus.blocked
                db.add(Vendor(name=r["vendor_name"], status=status, category=r["category"]))
        db.commit()
    finally:
        db.close()


def seed_policies():
    db = SessionLocal()
    try:
        if db.query(Policy).count() > 0:
            return
        for name, cat, lo, hi, level in SEED_POLICIES:
            db.add(Policy(name=name, category=cat, min_amount=lo, max_amount=hi, approval_level=level))
        db.commit()
    finally:
        db.close()