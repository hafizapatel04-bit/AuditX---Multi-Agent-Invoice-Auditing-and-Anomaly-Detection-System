import csv
import os
import sys

from extraction.extractor import extract_invoice, review_flags

CSV_PATH = "sample_data/ground_truth.csv"
PDF_DIR = "sample_data/test_invoices"


def norm(s):
    return " ".join(str(s or "").lower().split())


def main(limit=None):
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    cols = {c.lower().strip(): c for c in rows[0]}
    print("CSV columns:", list(cols))
    fcol = next((cols[k] for k in ("filename", "file", "file_name", "pdf") if k in cols), None)
    if not fcol:
        sys.exit("No filename column found. Tell me the column names above.")

    totals, hits = {}, {}
    poor_total = poor_flagged = 0
    for row in rows[:limit]:
        name = row[fcol]
        path = os.path.join(PDF_DIR, name)
        if not os.path.exists(path):
            print("missing file:", path)
            continue
        try:
            got = extract_invoice(path)
        except Exception as e:
            print(f"FAILED  {name}: {str(e)[:80]}")
            continue
        if norm(row.get(cols.get("quality", ""), "")) == "poor":
            flags = review_flags(got)
            poor_total += 1
            poor_flagged += int(bool(flags))
            print(f"{'FLAGGED' if flags else 'MISSED '} {name} {flags}")
            continue
        checks = {
            "vendor": norm(row.get(cols.get("vendor_name", cols.get("vendor", "")), "")) in norm(got.vendor_name)
                      or norm(got.vendor_name) in norm(row.get(cols.get("vendor_name", cols.get("vendor", "")), "")),
            "invoice_number": norm(row.get(cols.get("invoice_number", ""), "")) == norm(got.invoice_number),
            "date": norm(row.get(cols.get("invoice_date", cols.get("date", "")), "")) == norm(got.invoice_date),
            "amount": got.amount is not None and abs(float(str(row.get(cols.get("amount", ""), 0)).replace(",", "") or 0) - got.amount) < 0.01,
            "currency": norm(row.get(cols.get("currency", ""), "")) == norm(got.currency),
            "category": norm(row.get(cols.get("category", ""), "")) == norm(got.category),
        }
        for k, ok in checks.items():
            totals[k] = totals.get(k, 0) + 1
            hits[k] = hits.get(k, 0) + int(ok)
        bad = [k for k, ok in checks.items() if not ok]
        print(f"{'OK    ' if not bad else 'WRONG '} {name} {bad if bad else ''}")

    print("\nField accuracy:")
    for k in totals:
        print(f"  {k:15} {hits[k]}/{totals[k]}  ({100 * hits[k] / totals[k]:.0f}%)")
    print(f"\nPoor files flagged for review: {poor_flagged}/{poor_total}")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
