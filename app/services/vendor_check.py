import re
from difflib import get_close_matches

from sqlalchemy.orm import Session

from app.models import Vendor, VendorStatus

SUFFIXES = r"\b(pvt|private|ltd|limited|llc|inc|corp|co)\b"


def normalize(name: str) -> str:
    """'Bright Logistics Pvt. Ltd.' -> 'bright logistics'"""
    name = name.lower()
    name = re.sub(r"[^\w\s]", " ", name)   # remove punctuation
    name = re.sub(SUFFIXES, " ", name)     # remove company suffixes
    return " ".join(name.split())          # clean extra spaces


def verify_vendor(db: Session, vendor_name: str) -> dict:
    target = normalize(vendor_name)
    lookup = {normalize(v.name): v for v in db.query(Vendor).all()}

    match = lookup.get(target)

    # OCR/LLM often makes small spelling errors, so try a close match
    if match is None and target:
        close = get_close_matches(target, lookup.keys(), n=1, cutoff=0.85)
        if close:
            match = lookup[close[0]]

    if match is None:
        return {
            "result": "unknown",
            "vendor_id": None,
            "reason": f"Vendor '{vendor_name}' is not in the vendor list",
        }

    if match.status == VendorStatus.blocked:
        reason = f"Vendor '{match.name}' is blocked"
    elif match.status == VendorStatus.approved:
        reason = f"Vendor '{match.name}' is approved"
    else:
        reason = f"Vendor '{match.name}' is not yet approved"

    return {"result": match.status.value, "vendor_id": match.id, "reason": reason}