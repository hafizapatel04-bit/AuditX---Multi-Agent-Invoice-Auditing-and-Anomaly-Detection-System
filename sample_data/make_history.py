"""
Creates vendors.csv and invoices.csv (historical data) for ALL categories.
Run: venv\\Scripts\\python.exe sample_data\\make_history.py
"""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(11)
BASE = Path(__file__).parent

# vendor -> the category they normally bill for
VENDORS = {
    "Northwind Software Pvt Ltd": "Software Subscription",
    "Apex Digital Solutions": "Software Subscription",
    "Prime Equipments Ltd": "Equipment",
    "Metro Office Mart": "Office Supplies",
    "Skyline Travels": "Travel",
    "Tasty Bites Catering": "Food",
    "Orbit Cloud Services": "Cloud Services",
    "Bluepeak Technologies": "Cloud Services",
}

RANGES = {
    "Software Subscription": (11000, 15000),
    "Equipment": (44000, 53000),
    "Office Supplies": (4800, 6500),
    "Travel": (6000, 12000),
    "Food": (1500, 3500),
    "Cloud Services": (8000, 14000),
}

INVOICES_PER_CATEGORY = 10

with open(BASE / "vendors.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "vendor_name", "approved", "category"])
    for i, (name, cat) in enumerate(VENDORS.items(), start=1):
        w.writerow([i, name, True, cat])

rows = []
n = 1
for category, (low, high) in RANGES.items():
    vendors_for_cat = [v for v, c in VENDORS.items() if c == category]
    for _ in range(INVOICES_PER_CATEGORY):
        date = datetime(2026, 1, 1) + timedelta(days=random.randint(0, 250))
        rows.append({
            "id": n,
            "invoice_number": f"INV{1000 + n}",
            "vendor": random.choice(vendors_for_cat),
            "date": date.strftime("%Y-%m-%d"),
            "amount": round(random.uniform(low, high), 2),
            "currency": "INR",
            "category": category,
        })
        n += 1

with open(BASE / "invoices.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(f"Wrote {len(VENDORS)} vendors and {len(rows)} historical invoices.")