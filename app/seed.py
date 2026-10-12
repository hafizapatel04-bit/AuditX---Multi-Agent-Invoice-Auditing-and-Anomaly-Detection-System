import csv
from pathlib import Path

from app.database import SessionLocal
from app.models import Vendor, VendorStatus

CSV_PATH = Path(__file__).resolve().parents[1] / "sample_data" / "vendors.csv"


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