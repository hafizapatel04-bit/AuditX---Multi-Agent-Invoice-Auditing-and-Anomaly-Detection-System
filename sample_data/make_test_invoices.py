"""
Creates test invoice PDFs + ground_truth.csv/json (the correct answers).
Needs sample_data/vendors.csv (run make_history.py first).
Run: venv\\Scripts\\python.exe sample_data\\make_test_invoices.py
"""
import csv
import io
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import pymupdf as fitz  # PyMuPDF
from fpdf import FPDF
from PIL import Image, ImageFilter

random.seed(7)
BASE = Path(__file__).parent
OUT = BASE / "test_invoices"
OUT.mkdir(exist_ok=True)

RANGES = {
    "Software Subscription": (11000, 15000),
    "Equipment": (44000, 53000),
    "Office Supplies": (4800, 6500),
    "Travel": (6000, 12000),
    "Food": (1500, 3500),
    "Cloud Services": (8000, 14000),
}
ITEMS = {
    "Software Subscription": "Annual software licence",
    "Travel": "Flight and hotel booking",
    "Food": "Team lunch catering",
    "Equipment": "Laptops and monitors",
    "Office Supplies": "Stationery and printer paper",
    "Cloud Services": "Cloud hosting and storage",
}
# Three layouts with different wording, so extraction is tested on variety
STYLES = {
    1: {"num": "Invoice Number", "date": "Date", "sub": "Subtotal", "tax": "GST (18%)", "total": "Total"},
    2: {"num": "Bill No.", "date": "Invoice Date", "sub": "Amount before tax", "tax": "Tax", "total": "Grand Total"},
    3: {"num": "Inv #", "date": "Dated", "sub": "Net", "tax": "GST", "total": "Amount Due"},
}
DATE_FORMATS = {1: "%d/%m/%Y", 2: "%d %b %Y", 3: "%B %d, %Y"}


def load_vendors():
    path = BASE / "vendors.csv"
    if not path.exists():
        raise FileNotFoundError("vendors.csv not found. Run sample_data/make_history.py first.")
    with open(path, encoding="utf-8") as f:
        return {r["vendor_name"]: r["category"] for r in csv.DictReader(f)}


VENDORS = load_vendors()


def money(x):
    return f"{x:,.2f}"


def new_invoice(filename, vendor, number, style, quality="clean", category=None,
                amount_scale=1.0, wrong_total=False, note="", expected_audit="none"):
    category = category or VENDORS.get(vendor) or "Software Subscription"
    low, high = RANGES[category]
    subtotal = round(random.uniform(low, high) * amount_scale, 2)
    tax = round(subtotal * 0.18, 2)
    total = round(subtotal + tax, 2)
    printed_total = round(total * 1.1 + 500, 2) if wrong_total else total
    date = datetime(2026, 1, 1) + timedelta(days=random.randint(0, 270))
    return {"filename": filename, "vendor": vendor, "invoice_number": number,
            "date": date, "subtotal": subtotal, "tax": tax, "amount": printed_total,
            "currency": "INR", "category": category, "style": style,
            "quality": quality, "note": note, "expected_audit": expected_audit}


def build_pdf(inv, path):
    s = STYLES[inv["style"]]
    pdf = FPDF()
    pdf.add_page()
    align = "R" if inv["style"] == 2 else "L"
    line = dict(new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, inv["vendor"], align=align, **line)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6, "12 Business Park Road, Pune, Maharashtra", align=align, **line)
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "TAX INVOICE", **line)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 7, f"{s['num']}: {inv['invoice_number']}", **line)
    pdf.cell(0, 7, f"{s['date']}: {inv['date'].strftime(DATE_FORMATS[inv['style']])}", **line)
    pdf.ln(4)
    pdf.cell(0, 7, f"Description: {ITEMS.get(inv['category'], 'Services')}", **line)
    pdf.cell(0, 7, f"{s['sub']}: INR {money(inv['subtotal'])}", **line)
    pdf.cell(0, 7, f"{s['tax']}: INR {money(inv['tax'])}", **line)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 9, f"{s['total']}: INR {money(inv['amount'])}", **line)
    pdf.output(str(path))


def degrade(path, quality):
    """Turns a clean PDF into a 'scanned' or 'poor quality' image-only PDF."""
    doc = fitz.open(path)
    page = doc[0]
    zoom = 1.6 if quality == "scanned" else 0.9
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("L")
    width, height = page.rect.width, page.rect.height
    doc.close()

    if quality == "poor":
        img = img.filter(ImageFilter.GaussianBlur(1.1))
        img = img.rotate(random.uniform(-2.5, 2.5), expand=True, fillcolor=255)
        jpeg_quality = 35
    else:
        img = img.rotate(random.uniform(-1, 1), expand=True, fillcolor=255)
        jpeg_quality = 70

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=jpeg_quality)
    new_doc = fitz.open()
    new_page = new_doc.new_page(width=width, height=height)
    new_page.insert_image(new_page.rect, stream=buf.getvalue())
    tmp = Path(str(path) + ".tmp")
    new_doc.save(str(tmp))
    new_doc.close()
    tmp.replace(path)


def main():
    names = list(VENDORS.keys())
    pick = lambda: random.choice(names)
    invoices = []

    # 8 clean invoices (mixed layouts)
    for n in range(1, 9):
        invoices.append(new_invoice(f"inv_{n:02d}_clean.pdf", pick(),
                                    f"INV{2000 + n}", style=(n % 3) + 1))
    # 2 scanned + 2 poor quality
    for n, q in [(9, "scanned"), (10, "scanned"), (11, "poor"), (12, "poor")]:
        invoices.append(new_invoice(f"inv_{n:02d}_{q}.pdf", pick(), f"INV{2000 + n}",
                                    style=(n % 3) + 1, quality=q,
                                    note=f"{q} image-only PDF"))

    # Rigged invoices
    original = invoices[0]
    dup = dict(original)
    dup.update(filename="rig_duplicate.pdf", expected_audit="duplicate",
               note=f"RIGGED: exact duplicate of {original['filename']} (process the original first)")
    invoices.append(dup)

    invoices.append(new_invoice("rig_unknown_vendor.pdf", "Zenith Global Traders", "INV9001",
                                style=1, category="Software Subscription",
                                note="RIGGED: vendor not in approved list",
                                expected_audit="unapproved_vendor"))
    invoices.append(new_invoice("rig_wrong_total.pdf", pick(), "INV9002", style=2,
                                wrong_total=True,
                                note="RIGGED: printed total does not equal subtotal + tax",
                                expected_audit="total_mismatch"))
    invoices.append(new_invoice("rig_huge_amount.pdf", "Northwind Software Pvt Ltd", "INV9003",
                                style=3, category="Software Subscription", amount_scale=15,
                                note="RIGGED: amount about 15x normal",
                                expected_audit="anomaly"))

    rows = []
    for inv in invoices:
        path = OUT / inv["filename"]
        build_pdf(inv, path)
        if inv["quality"] in ("scanned", "poor"):
            degrade(path, inv["quality"])
        rows.append({
            "filename": inv["filename"], "vendor": inv["vendor"],
            "invoice_number": inv["invoice_number"],
            "date": inv["date"].strftime("%Y-%m-%d"),
            "amount": inv["amount"], "currency": inv["currency"],
            "category": inv["category"], "quality": inv["quality"],
            "expected_audit": inv["expected_audit"], "note": inv["note"],
        })

    fields = list(rows[0].keys())
    with open(BASE / "ground_truth.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with open(BASE / "ground_truth.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"Created {len(rows)} PDFs in {OUT}")
    print("Wrote ground_truth.csv and ground_truth.json")


if __name__ == "__main__":
    main()