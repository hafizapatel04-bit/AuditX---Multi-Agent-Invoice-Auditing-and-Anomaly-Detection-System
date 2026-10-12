import json
import re

import ollama
from pydantic import ValidationError

from app.schemas import ExtractedInvoice
from extraction.ocr import get_text

MODEL = "llama3.2:3b"  # try "qwen2.5:7b" later for better line items
client = ollama.Client(timeout=90)

PROMPT = """You extract data from invoices. Return ONLY JSON.
Fields: vendor_name (string), invoice_number (string or null), invoice_date (YYYY-MM-DD or null), amount (number or null), currency (3-letter code), category (string or null), line_items (list of {description, quantity, unit_price, total}).
Rules:
- Copy values exactly as written. Never guess. Use null if a field is missing.
- Numbers must be plain numbers without currency symbols.
- vendor_name is the company issuing the invoice (the "From" side), not the customer.
- amount is the final total due, including tax.
- currency is the 3-letter code printed on the invoice, or inferred from the symbol ($ = USD, ₹ or Rs = INR). If no currency is shown, use null.
- line_items are only the products or services being sold. Never include table headings, Tax, Sub Total or Total rows.
- category must be exactly one of: Software Subscription, Travel, Food, Equipment, Office Supplies, Cloud Services, Other. Use Other if unsure.
Invoice text:
{text}
"""

_NULLS = {"", "null", "none", "n/a", "na", "-"}

_NOT_ITEMS = {"tax", "sub total", "subtotal", "total", "hrs/qty", "service",
              "qty", "quantity", "rate/price", "rate", "adjust", "discount"}


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
    for k, v in list(data.items()):
        if isinstance(v, str) and v.strip().lower() in _NULLS:
            data[k] = None
    data["amount"] = _num(data.get("amount"))
    if not data.get("currency"):
        data.pop("currency", None)  # fall back to the schema default

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



def extract_invoice(file_path: str) -> ExtractedInvoice:
    text = get_text(file_path)[:3000]
    response = client.chat(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT.replace("{text}", text)}],
        format="json",
        options={"temperature": 0, "num_predict": 600},
    )
    try:
        data = _clean(json.loads(response.message.content))
        return ExtractedInvoice.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Extraction failed: {e}\nRaw output: {response.message.content}")
