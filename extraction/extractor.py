import json
import re
from datetime import date

import ollama
from pydantic import ValidationError

from app.schemas import ExtractedInvoice
from extraction.ocr import get_text

MODEL = "llama3.2:3b"  # change to "qwen2.5:7b" if you switched models
client = ollama.Client(timeout=90)

PROMPT = """You extract data from invoices. Return ONLY JSON.
Fields: vendor_name (string), invoice_number (string or null), invoice_date (YYYY-MM-DD or null), due_date (YYYY-MM-DD or null), subtotal (number or null, the amount before tax), tax_amount (number or null, total GST/VAT/tax), amount (number or null, final total due), currency (3-letter code or null), category (string or null), line_items (list of {description, quantity, unit_price, total}).
Rules:
- Copy values exactly as written. Never guess. Use null if a field is missing.
- Numbers must be plain numbers without currency symbols.
- Numeric dates like 05/03/2026 are day/month/year, so that one is 2026-03-05.
- vendor_name is the company issuing the invoice (the "From" side), not the customer.
- amount is the final total due, including tax.
- currency is the 3-letter code printed on the invoice, or inferred from the symbol ($ = USD, Rs or ₹ = INR). If no currency is shown, use null.
- category must be exactly one of: Software Subscription, Travel, Food, Equipment, Office Supplies, Cloud Services, Other. Choose Software Subscription only for recurring software or licence fees. Web design, consulting, plants, chemicals, medicine and any other goods or services are Other. Use Other if unsure.
- line_items are only the products or services being sold. Never include table headings, Tax, Sub Total or Total rows.

Invoice text:
{text}
"""

_NULLS = {"", "null", "none", "n/a", "na", "-"}
_NOT_ITEMS = {"tax", "sub total", "subtotal", "total", "hrs/qty", "service",
              "qty", "quantity", "rate/price", "rate", "adjust", "discount"}
_MONEY = re.compile(r"\d{1,3}(?:,\d{2,3})*\.\d{2}|\d+\.\d{2}")
_DMY = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b")


def _num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d.\-]", "", str(v).replace(",", ""))
    try:
        return float(s)
    except ValueError:
        return None


def _clean(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Model did not return a JSON object")
    for k, v in list(data.items()):
        if isinstance(v, str) and v.strip().lower() in _NULLS:
            data[k] = None
    data["amount"] = _num(data.get("amount"))
    data["subtotal"] = _num(data.get("subtotal"))
    data["tax_amount"] = _num(data.get("tax_amount"))
    if not data.get("currency"):
        data.pop("currency", None)  # fall back to the schema default

    for k in ("invoice_date", "due_date"):
        v = data.get(k)
        if v is not None:
            try:
                date.fromisoformat(str(v))
            except ValueError:
                data[k] = None

    items = []
    for it in data.get("line_items") or []:
        if not isinstance(it, dict):
            continue
        desc = str(it.get("description") or "").strip()
        total = _num(it.get("total"))
        if not desc or desc.lower() in _NOT_ITEMS or total is None:
            continue
        items.append({
            "description": desc,
            "quantity": _num(it.get("quantity")) or 1,
            "unit_price": _num(it.get("unit_price")),
            "total": total,
        })
    data["line_items"] = items
    return data


def _ground_amount(text, amount):
    """Keep the model's amount only if it really appears in the text."""
    nums = [float(m.replace(",", "")) for m in _MONEY.findall(text)]
    if not nums:
        return amount
    if amount is not None and any(abs(amount - n) < 0.005 for n in nums):
        return amount
    for line in text.splitlines():
        low = line.lower()
        if "sub" not in low and any(k in low for k in ("amount due", "total due", "grand total", "total")):
            found = _MONEY.findall(line)
            if found:
                return float(found[-1].replace(",", ""))
    return max(nums)


def _fix_date(text, d):
    """Numeric dates like 05/03/2026 are day-first here (Indian format)."""
    m = _DMY.search(text)
    if not m or d is None:
        return d
    a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        day_first, month_first = date(y, b, a), date(y, a, b)
    except ValueError:
        return d
    return day_first if d == month_first and d != day_first else d

_SUB_RE = re.compile(r"sub\s*total|\bnet\b|taxable")
_TAX_RE = re.compile(r"\bgst\b|\bvat\b|\btax\b|\bcgst\b|\bsgst\b|\bigst\b")
_EXTRA_RE = re.compile(r"shipping|handling|freight|delivery|discount|round\s*off")

def _ground_field(text, value, label_re):
    """Keep the value only if it appears in the text; else read it from the labelled line."""
    nums = [float(m.replace(",", "")) for m in _MONEY.findall(text)]
    if value is not None and any(abs(value - n) < 0.005 for n in nums):
        return value
    for line in text.splitlines():
        if label_re.search(line.lower()):
            found = _MONEY.findall(line)
            if found:
                return float(found[-1].replace(",", ""))
    return None

_CAT_WORDS = {
    "Software Subscription": r"software|subscription|licen[cs]e|saas",
    "Travel": r"travel|flight|airline|hotel|booking|ticket|taxi",
    "Food": r"food|cater|restaurant|meal|beverage|lunch|dinner",
    "Equipment": r"equipment|hardware|laptop|printer|machine|monitor",
    "Office Supplies": r"office|stationery|supplies|toner|paper",
    "Cloud Services": r"cloud|hosting|server|storage|compute",
}

def _ground_category(text, cat):
    if cat not in _CAT_WORDS:
        return "Other"
    if not re.search(_CAT_WORDS[cat], text.lower()):
        return "Other"
    return cat

_CUR_PATTERNS = {
    "USD": r"\$|usd|us\s*dollar",
    "INR": r"₹|\brs\b|inr|rupee",
    "EUR": r"€|eur",
    "GBP": r"£|gbp",
}


def _ground_currency(text, cur):
    if not cur:
        return None
    pat = _CUR_PATTERNS.get(str(cur).upper(), re.escape(str(cur)))
    return cur if re.search(pat, text.lower()) else None


def extract_invoice(file_path: str) -> ExtractedInvoice:
    text = get_text(file_path)
    if len(text) > 3500:
        text = text[:2000] + "\n...\n" + text[-1500:]
    response = client.chat(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT.replace("{text}", text)}],
        format="json",
        options={"temperature": 0, "num_predict": 900},
        keep_alive="30m",
    )
    try:
        data = _clean(_parse_json(response.message.content))
        data["amount"] = _ground_amount(text, data.get("amount"))
        data["subtotal"] = _ground_field(text, data.get("subtotal"), _SUB_RE)
        data["tax_amount"] = _ground_field(text, data.get("tax_amount"), _TAX_RE)
        data["category"] = _ground_category(text, data.get("category"))
        data["currency"] = _ground_currency(text, data.get("currency"))
        inv = ExtractedInvoice.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Extraction failed: {e}\nRaw output: {response.message.content}")
    inv.invoice_date = _fix_date(text, inv.invoice_date)
    if inv.invoice_date and str(inv.invoice_date)[:4] not in text:
        inv.invoice_date = None  # year isn't in the text, so the model invented the date
    num = (inv.invoice_number or "").strip()
    if num and (len(num) < 2 or not re.search(rf"(?<!\w){re.escape(num)}(?!\w)", text)):
        inv.invoice_number = None  # too short, or not found as a whole token in the text
    if (None not in (inv.subtotal, inv.tax_amount, inv.amount)
            and _EXTRA_RE.search(text.lower())
            and abs(inv.subtotal + inv.tax_amount - inv.amount) > 0.05):
        inv.subtotal = None  # extra charge lines present, so subtotal + tax can't be checked
    return inv

def _parse_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        i = raw.find('"line_items"')
        if i == -1:
            raise
        return json.loads(raw[:i].rstrip().rstrip(",") + "}")  # keep header, drop truncated items

def check_arithmetic(inv, tol: float = 0.05):
    """True if subtotal + tax == total, False if not, None if the numbers are missing."""
    if None in (inv.subtotal, inv.tax_amount, inv.amount):
        return None
    return abs(inv.subtotal + inv.tax_amount - inv.amount) <= tol


def review_flags(inv):
    flags = []
    num = (inv.invoice_number or "").strip()
    if not num or not re.search(r"\d", num) or " " in num:
        flags.append("invoice number missing or unreadable")
    if inv.amount is None:
        flags.append("amount missing")
    if inv.invoice_date is None:
        flags.append("invoice date missing")
    if check_arithmetic(inv) is False:
        flags.append("subtotal + tax does not equal total")
    return flags

