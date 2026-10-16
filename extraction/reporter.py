import json
import re

import ollama

from extraction.extractor import MODEL, review_flags

client = ollama.Client(timeout=60)


def _get(x, keys, default=None):
    for k in keys:
        v = x.get(k) if isinstance(x, dict) else getattr(x, k, None)
        if v not in (None, ""):
            return v
    return default


def _normalize(findings):
    out = []
    for f in findings or []:
        if isinstance(f, str):
            out.append({"rule": "check", "severity": "medium", "message": f})
            continue
        out.append({
            "rule": str(_get(f, ("rule", "type", "code", "name", "check"), "check")),
            "severity": str(_get(f, ("severity", "level", "risk"), "medium")).lower(),
            "message": str(_get(f, ("message", "detail", "reason", "description", "explanation"), "")),
        })
    return out


def _numbers(s):
    return {float(n.replace(",", "")) for n in re.findall(r"\d+(?:[,.]\d+)*", s)}


def _template(facts, status):
    who = facts["vendor"] or "an unknown vendor"
    num = facts["invoice_number"] or "no readable number"
    if facts["amount"] is not None:
        amt = f"{float(facts['amount']):,.2f} {facts['currency'] or ''}".strip()
    else:
        amt = "an unreadable amount"
    lines = [f"Invoice {num} from {who} for {amt}: {status}."]
    for f in facts["findings"]:
        lines.append(f"- {f['rule']} ({f['severity']}): {f['message']}")
    for fl in facts["extraction_flags"]:
        lines.append(f"- Extraction: {fl}")
    if status == "CLEAN":
        lines.append("No issues found.")
    return "\n".join(lines)


def _narrate(facts, status):
    prompt = (
        "You write a short audit summary for an accountant. Use ONLY the facts below. "
        "Write 2-3 plain sentences, mention every finding, and say what to do next. "
        "Do not invent numbers, names or reasons.\n"
        f"Status: {status}\nFacts: {json.dumps(facts, default=str)}"
    )
    try:
        r = client.chat(model=MODEL, messages=[{"role": "user", "content": prompt}],
                        options={"temperature": 0, "num_predict": 160}, keep_alive="30m")
        text = r.message.content.strip()
    except Exception:
        return None
    text = re.sub(r"^here('s| is)[^\n]*:\s*", "", text, flags=re.I).strip()
    evidence = " ".join(
        [f["rule"] + " " + f["message"] for f in facts["findings"]] + facts["extraction_flags"]
    ).lower()
    claims = set(re.findall(r"subtotal|\btax\b|mismatch|duplicate|unapproved|anomal|outlier|fraud|overdue", text.lower()))
    if not text or any(c not in evidence for c in claims):
        return None  # mentions a problem that isn't in the facts
    if not _numbers(text) <= _numbers(json.dumps(facts, default=str)):
        return None  # mentions a number that isn't in the facts
    return text


def build_report(inv, findings=None, use_llm=True):
    findings = _normalize(findings)
    flags = review_flags(inv)
    if findings:
        status = "FLAGGED"
    elif flags:
        status = "NEEDS REVIEW"
    else:
        status = "CLEAN"
    facts = {
        "vendor": inv.vendor_name,
        "invoice_number": inv.invoice_number,
        "date": str(inv.invoice_date) if inv.invoice_date else None,
        "amount": inv.amount,
        "currency": inv.currency,
        "category": inv.category,
        "findings": findings,
        "extraction_flags": flags,
    }
    summary = (use_llm and _narrate(facts, status)) or _template(facts, status)
    return {"status": status, "summary": summary, "facts": facts}
