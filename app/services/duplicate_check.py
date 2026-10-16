import re

from sqlalchemy.orm import Session

from app.models import Invoice
from app.services.vendor_check import normalize

DATE_WINDOW_DAYS = 7
AMOUNT_TOLERANCE = 0.01


def _norm_number(n: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (n or "").lower())


def check_duplicate(db: Session, invoice: Invoice) -> dict:
    vendor = normalize(invoice.vendor_name or "")
    number = _norm_number(invoice.invoice_number)
    can_fuzzy = invoice.amount is not None and invoice.invoice_date is not None

    if not vendor or vendor == "unknown" or not (number or can_fuzzy):
        return {"result": "unchecked", "match_id": None,
                "reason": "Not enough data to check for duplicates"}

    # only compare against invoices processed earlier
    earlier = db.query(Invoice).filter(Invoice.id < invoice.id).all()
    same_vendor = [i for i in earlier if normalize(i.vendor_name or "") == vendor]

    if number:
        for i in same_vendor:
            if _norm_number(i.invoice_number) == number:
                return {"result": "exact_duplicate", "match_id": i.id,
                        "reason": f"Invoice {invoice.invoice_number} from {invoice.vendor_name} "
                                  f"already exists (invoice #{i.id})"}

    if can_fuzzy:
        for i in same_vendor:
            if (i.amount is not None and i.invoice_date is not None
                    and abs(i.amount - invoice.amount) <= AMOUNT_TOLERANCE
                    and abs((i.invoice_date - invoice.invoice_date).days) <= DATE_WINDOW_DAYS):
                return {"result": "possible_duplicate", "match_id": i.id,
                        "reason": f"Same vendor, amount and date as invoice #{i.id}"}

    return {"result": "no_duplicate", "match_id": None, "reason": "No duplicate found"}