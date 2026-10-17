import csv

import httpx
from run_ground_truth import BASE, CSV_PATH, matches


def norm(s):
    return " ".join(str(s or "").lower().split())


def main():
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    with httpx.Client(base_url=BASE, timeout=60) as client:
        invoices = sorted(client.get("/invoices").json(), key=lambda i: i["id"])
        if len(invoices) != len(rows):
            print(f"WARNING: {len(invoices)} invoices in the DB but {len(rows)} rows in the CSV. "
                  "Rows are matched by upload order, so check the result carefully.\n")

        passed = 0
        for inv, row in zip(invoices, rows):
            audit_res = client.get(f"/audit/{inv['id']}")
            if audit_res.status_code != 200:
                print(f"----  {row['filename']:24} not analyzed")
                continue
            audit = audit_res.json()

            ok = matches(row["expected_audit"], audit)
            passed += ok
            print(f"{'PASS' if ok else 'FAIL'}  {row['filename']:24} expected={row['expected_audit']:18} "
                  f"got={audit['final_status']}")

            wrong = []
            if norm(row["vendor"]) not in norm(inv["vendor_name"]):
                wrong.append(f"vendor {inv['vendor_name']!r} (truth {row['vendor']!r})")
            if norm(row["invoice_number"]) != norm(inv["invoice_number"]):
                wrong.append(f"number {inv['invoice_number']!r} (truth {row['invoice_number']!r})")
            if str(row["date"]) != str(inv["invoice_date"]):
                wrong.append(f"date {inv['invoice_date']!r} (truth {row['date']!r})")
            if inv["amount"] is None or abs(float(row["amount"]) - inv["amount"]) > 0.01:
                wrong.append(f"amount {inv['amount']!r} (truth {row['amount']!r})")
            if wrong:
                print("        extraction differs:", "; ".join(wrong))
            if not ok:
                print("        reasons:", audit["reasons"])
            if inv.get("review_flags"):
                print("        review_flags:", inv["review_flags"])
            if inv.get("notes"):
                print("        notes:", inv["notes"][:200])

    print(f"\n{passed}/{len(rows)} match the ground truth")


if __name__ == "__main__":
    main()