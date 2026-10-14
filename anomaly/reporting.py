"""
Reporting Agent.
Python makes every decision (check results + final status).
The LLM only writes a short plain-English summary of those decisions.
If Ollama is off or fails, a template summary is used, so a report is always produced.
"""
import re
import ollama

MODEL_NAME = "llama3.2:3b"   # same model as Person A
LLM_TIMEOUT_SECONDS = 120    # first call is slow while the model loads


def _norm(value):
    return str(value or "").strip().lower().replace("_", " ")


def build_findings(audit: dict) -> list:
    """Each finding is (label, ok, detail). A missing or unknown result is flagged, never passed silently."""
    findings = []

    # --- Vendor: only "approved" passes ---
    v = _norm(audit.get("vendor_status"))
    vendor_ok = v in ("approved", "approved vendor")
    if vendor_ok:
        vendor_detail = "Approved vendor"
    elif v == "":
        vendor_detail = "Vendor could not be verified"
    elif v in ("unapproved", "not approved"):
        vendor_detail = "Vendor is not on the approved list"
    else:
        vendor_detail = f"Vendor is not approved (status: {v})"
    findings.append(("Vendor Check", vendor_ok, vendor_detail))

    # --- Required fields: vendor, invoice number, date, amount ---
    f = _norm(audit.get("fields_status"))
    fields_ok = f in ("complete", "ok", "pass")
    missing = audit.get("missing_fields") or []
    if fields_ok:
        fields_detail = "All required fields present"
    elif missing:
        fields_detail = "Missing: " + ", ".join(str(m).replace("_", " ") for m in missing)
    else:
        fields_detail = "One or more required fields are missing"
    findings.append(("Required Fields", fields_ok, fields_detail))

    # --- Duplicate ---
    d = _norm(audit.get("duplicate_status"))
    if d in ("no duplicate", "not duplicate", "none", "pass"):
        dup_ok, dup_detail = True, "No duplicate found"
    elif d == "exact duplicate":
        dup_ok, dup_detail = False, "Exact duplicate of an existing invoice"
    elif "duplicate" in d:
        dup_ok, dup_detail = False, "Possible duplicate of an existing invoice"
    elif d == "unchecked":
        dup_ok, dup_detail = False, "Duplicate check could not be run"
    else:
        dup_ok, dup_detail = False, "Duplicate check result is missing"
    findings.append(("Duplicate Check", dup_ok, dup_detail))

    # --- Total: subtotal + tax should equal the printed total ---
    t = _norm(audit.get("total_status"))
    if t in ("mismatch", "mismatched", "total mismatch"):
        try:
            extra = f" (difference {abs(float(audit.get('total_difference'))):,.2f})"
        except (TypeError, ValueError):
            extra = ""
        total_ok = False
        total_detail = "Subtotal plus tax does not match the printed total" + extra
    elif t in ("ok", "match", "matches"):
        total_ok, total_detail = True, "Subtotal plus tax matches the total"
    else:
        total_ok, total_detail = True, "Not verified (subtotal or tax not found)"
    findings.append(("Total Check", total_ok, total_detail))

    # --- Policy ---
    p = _norm(audit.get("policy_status"))
    policy_ok = (not p) or re.search(r"\b(normal|pass|passed|ok|within)\b", p) is not None
    findings.append(("Policy Check", policy_ok,
                     "Within the normal approval limit" if policy_ok
                     else f"Extra approval needed ({p})"))

    # --- Anomaly (dict from anomaly.engine.check_anomaly, or a plain string) ---
    a = audit.get("anomaly")
    if isinstance(a, dict):
        flagged = bool(a.get("is_anomaly"))
        reason = a.get("reason") or ""
        findings.append(("Anomaly Detection", not flagged,
                         (reason or "Amount is unusual compared with history") if flagged
                         else "Amount is within the expected range"))
    elif a or audit.get("anomaly_status"):
        s = _norm(audit.get("anomaly_status") or a)
        flagged = "anomal" in s and "no anomal" not in s and "not anomal" not in s
        findings.append(("Anomaly Detection", not flagged,
                         "Amount is unusual compared with history" if flagged
                         else "Amount is within the expected range"))
    else:
        findings.append(("Anomaly Detection", True, "Not checked (no comparable history)"))
    return findings


def decide_final_status(audit: dict, findings: list) -> str:
    if audit.get("final_status"):
        return str(audit["final_status"])
    failed = [label for label, ok, _ in findings if not ok]
    if not failed:
        return "APPROVED"
    if failed == ["Policy Check"]:
        return "PENDING MANAGER APPROVAL"
    return "FLAGGED - MANUAL REVIEW"


def template_summary(findings: list) -> str:
    failed = [detail for _, ok, detail in findings if not ok]
    if not failed:
        return "All checks passed, so this invoice can be processed normally."
    return "This invoice needs attention because: " + "; ".join(failed) + "."


BANNED_PHRASES = ["needs attention", "under passed", "here is", "summary of the",
                  "2-3 sentence", "fraud"]


def llm_summary(invoice: dict, findings: list, final_status: str) -> str:
    facts = []
    for label, ok, detail in findings:
        if ok:
            facts.append(f"{label} was fine.")
        else:
            facts.append(f"{label} found a problem: {detail}.")
    facts_text = "\n".join(facts)
    number = invoice.get("invoice_number") or "this invoice"

    prompt = f"""Write the summary paragraph of an invoice audit report in 2 or 3 plain sentences.
Start directly with the invoice number. No introduction. Use only the facts given.
Do not change the final status. Do not mention fraud.

Example facts:
Invoice INV0001 from Acme Ltd. Final status: PENDING MANAGER APPROVAL.
Vendor Check was fine.
Policy Check found a problem: Extra approval needed (manager approval required).
Example summary:
Invoice INV0001 from Acme Ltd is waiting for manager approval. The vendor check was fine, but the amount is above the normal approval limit.

Facts:
Invoice {number} from {invoice.get('vendor')}. Final status: {final_status}.
{facts_text}
Summary:"""

    client = ollama.Client(timeout=LLM_TIMEOUT_SECONDS)
    response = client.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0},
    )
    summary = response["message"]["content"].strip()

    # Safety checks: any failure raises an error, and generate_report then
    # falls back to the template summary automatically.
    lowered = summary.lower()
    if any(phrase in lowered for phrase in BANNED_PHRASES):
        raise ValueError("summary repeated prompt wording")
    if invoice.get("invoice_number") and str(invoice["invoice_number"]) not in summary:
        raise ValueError("summary does not mention the invoice number")
    if len(summary) > 700:
        raise ValueError("summary too long")
    return summary

def _money(invoice: dict) -> str:
    try:
        return f"{invoice.get('currency') or 'INR'} {float(invoice.get('total') or invoice.get('amount')):,.2f}"
    except (TypeError, ValueError):
        return "unknown"


def generate_report(invoice: dict, audit: dict, use_llm: bool = True) -> dict:
    findings = build_findings(audit)
    final_status = decide_final_status(audit, findings)

    summary, used_llm = None, False
    if use_llm:
        try:
            summary = llm_summary(invoice, findings, final_status)
            used_llm = bool(summary)
        except Exception as error:
            print(f"[reporting] LLM unavailable, using template summary ({error})")
    if not summary:
        summary = template_summary(findings)

    lines = [
        "INVOICE AUDIT REPORT",
        "----------------------------",
        f"Invoice Number: {invoice.get('invoice_number') or 'MISSING'}",
        f"Vendor:         {invoice.get('vendor') or 'MISSING'}",
        f"Amount:         {_money(invoice)}",
        f"Date:           {invoice.get('date') or 'MISSING'}",
        f"Category:       {invoice.get('category') or 'MISSING'}",
        "",
    ]
    for label, ok, detail in findings:
        lines.append(f"{label + ':':<19}{'PASS' if ok else 'FLAG'} - {detail}")
    lines += ["", f"FINAL STATUS: {final_status}", "", f"Summary: {summary}"]

    return {
        "report_text": "\n".join(lines),
        "final_status": final_status,
        "findings": [{"check": l, "ok": ok, "detail": d} for l, ok, d in findings],
        "used_llm": used_llm,
    }


if __name__ == "__main__":
    clean_invoice = {"invoice_number": "INV1024", "vendor": "Northwind Software Pvt Ltd",
                     "total": 29500, "currency": "INR", "category": "Software Subscription",
                     "date": "2026-09-20"}
    clean_audit = {"vendor_status": "approved", "fields_status": "complete",
                   "duplicate_status": "no_duplicate", "policy_status": "manager_approval_required",
                   "anomaly": {"is_anomaly": False, "reason": "Amount is within the expected range"}}

    bad_invoice = {"invoice_number": "INV9001", "vendor": "Zenith Global Traders",
                   "total": 177000, "currency": "INR", "category": "Software Subscription",
                   "date": "2026-05-01"}
    bad_audit = {"vendor_status": "unapproved", "fields_status": "complete",
                 "duplicate_status": "no_duplicate", "policy_status": "finance_review",
                 "anomaly": {"is_anomaly": True,
                             "reason": "Amount is 133.12 standard deviations from the category average"}}

    print("=== TEST 1: normal invoice that needs manager approval (with LLM) ===")
    print(generate_report(clean_invoice, clean_audit)["report_text"])

    print("\n=== TEST 2: invoice with several problems (with LLM) ===")
    print(generate_report(bad_invoice, bad_audit)["report_text"])

    print("\n=== TEST 3: same invoice, LLM switched off (template only) ===")
    print(generate_report(bad_invoice, bad_audit, use_llm=False)["report_text"])
    wrong_total_invoice = {"invoice_number": "INV9002", "vendor": "Northwind Software Pvt Ltd",
                           "total": 15000, "currency": "INR", "category": "Software Subscription",
                           "date": "2026-03-04"}
    wrong_total_audit = {"vendor_status": "approved", "fields_status": "complete",
                         "duplicate_status": "unchecked", "total_status": "mismatch",
                         "total_difference": 2450.5, "policy_status": "manager_approval_required",
                         "anomaly": {"is_anomaly": False, "reason": ""}}
    print("\n=== TEST 4: total mismatch and unchecked duplicate (template only) ===")
    print(generate_report(wrong_total_invoice, wrong_total_audit, use_llm=False)["report_text"])