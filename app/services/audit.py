import logging

from sqlalchemy.orm import Session

from app.models import AuditResult, Invoice, InvoiceStatus
from app.services.duplicate_check import check_duplicate
from app.services.policy_check import check_policy
from app.services.vendor_check import verify_vendor

log = logging.getLogger(__name__)

TOTAL_TOLERANCE = 1.00  # differences under this are rounding


def check_fields(invoice: Invoice) -> dict:
    missing = []
    vendor = (invoice.vendor_name or "").strip()
    if not vendor or vendor.upper() == "UNKNOWN":
        missing.append("vendor")
    if not (invoice.invoice_number or "").strip():
        missing.append("invoice_number")
    if invoice.invoice_date is None:
        missing.append("date")
    if not invoice.amount:  # None or 0
        missing.append("amount")
    return {"result": "missing" if missing else "complete", "missing_fields": missing}


def check_total(invoice: Invoice) -> dict:
    if invoice.subtotal is None or invoice.tax_amount is None or invoice.amount is None:
        return {"result": "unchecked", "difference": None}
    diff = round(abs(invoice.subtotal + invoice.tax_amount - invoice.amount), 2)
    if diff < TOTAL_TOLERANCE:
        return {"result": "ok", "difference": diff}
    return {"result": "mismatch", "difference": diff}


def run_anomaly(invoice: Invoice) -> dict | None:
    """Person C's history is in rupees, so only INR invoices with a category are scored."""
    if invoice.amount is None or not invoice.category or (invoice.currency or "").upper() != "INR":
        return None
    try:
        from anomaly.engine import check_anomaly
        return check_anomaly(invoice.amount, invoice.category, invoice.vendor_name)
    except Exception as e:
        log.warning("Anomaly check failed for invoice %s: %s", invoice.id, e)
        return None  # report shows "Not checked"


def decide_status(flags: dict) -> InvoiceStatus:
    flagged = {name for name, is_flagged in flags.items() if is_flagged}
    if not flagged:
        return InvoiceStatus.approved
    if flagged == {"policy"}:
        return InvoiceStatus.needs_review
    return InvoiceStatus.flagged

STATUS_TEXT = {
    InvoiceStatus.approved: "APPROVED",
    InvoiceStatus.needs_review: "PENDING MANAGER APPROVAL",
    InvoiceStatus.flagged: "FLAGGED - MANUAL REVIEW",
}


def make_report(invoice: Invoice, details: dict, status: InvoiceStatus, use_llm: bool) -> str | None:
    try:
        from anomaly.reporting import generate_report
        result = generate_report(
            {
                "invoice_number": invoice.invoice_number,
                "vendor": invoice.vendor_name,
                "total": invoice.amount,
                "currency": invoice.currency,
                "category": invoice.category,
                "date": str(invoice.invoice_date) if invoice.invoice_date else None,
            },
            {**details, "final_status": STATUS_TEXT[status]},  # my decision wins
            use_llm=use_llm,
        )
        text = result["report_text"]
        if details.get("extraction_flags"):
            text += "\n\nExtraction notes: " + "; ".join(details["extraction_flags"])
        return text
    except Exception as e:
        log.warning("Report generation failed for invoice %s: %s", invoice.id, e)
        return None

def run_audit(db: Session, invoice: Invoice, use_llm: bool = False) -> AuditResult:
    vendor = verify_vendor(db, invoice.vendor_name or "")
    invoice.vendor_id = vendor["vendor_id"]
    fields = check_fields(invoice)
    total = check_total(invoice)
        # A's arithmetic flag is ignored: check_total() above uses Person C's 1.00 tolerance
    extraction_flags = [f for f in (invoice.review_flags or []) if "does not equal total" not in f]
    duplicate = check_duplicate(db, invoice)
    if (invoice.currency or "").upper() == "INR":
        policy = check_policy(db, invoice.amount, invoice.category)
    else:
        policy = {"result": "unchecked",
                "reason": "Currency missing or not INR, approval limits are in rupees"}
    anomaly = run_anomaly(invoice)

    flags = {
        "vendor": vendor["result"] != "approved",
        "fields": fields["result"] != "complete",
        "total": total["result"] == "mismatch",
        "duplicate": duplicate["result"] != "no_duplicate",
        "policy": policy["result"] != "normal",
        "extraction": bool(extraction_flags),
        "anomaly": bool(anomaly and anomaly.get("is_anomaly")),
    }

    reasons = []
    if flags["vendor"]:
        reasons.append(vendor["reason"])
    if flags["fields"]:
        reasons.append("Missing fields: " + ", ".join(fields["missing_fields"]))
    if flags["total"]:
        reasons.append(f"Total mismatch: subtotal + tax differs from amount by {total['difference']:,.2f}")
    if flags["duplicate"]:
        reasons.append(duplicate["reason"])
    if flags["policy"]:
        reasons.append(policy["reason"])
    if flags["extraction"] and fields["result"] == "complete":
        reasons.extend(extraction_flags)
    if flags["anomaly"]:
        reasons.append(anomaly.get("reason") or "Amount flagged as anomalous")

    status = decide_status(flags)

    # same keys Person C's generate_report() reads (final_status left out on purpose,
    # C applies the same rule and prints its own wording)
    details = {
        "vendor_status": vendor["result"],
        "fields_status": fields["result"],
        "missing_fields": fields["missing_fields"],
        "total_status": total["result"],
        "total_difference": total["difference"],
        "duplicate_status": duplicate["result"],
        "policy_status": policy["result"],
    }
    if anomaly is not None:
        details["anomaly"] = anomaly

    result = invoice.audit or AuditResult(invoice_id=invoice.id)
    result.vendor_check = vendor["result"]
    result.fields_check = fields["result"]
    result.total_check = total["result"]
    result.duplicate_check = duplicate["result"]
    result.policy_check = policy["result"]
    result.anomaly_score = (anomaly or {}).get("score")
    result.final_status = status
    result.reasons = reasons
    result.details = details
    result.report = make_report(invoice, details, status, use_llm)
    invoice.status = status

    db.add(result)
    db.commit()
    db.refresh(result)
    return result