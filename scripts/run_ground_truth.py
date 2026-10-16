import csv
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "sample_data" / "test_invoices"
CSV_PATH = ROOT / "sample_data" / "ground_truth.csv"


def matches(expected: str, audit: dict) -> bool:
    if expected == "none":
        return audit["final_status"] == "approved"
    if expected == "duplicate":
        return audit["duplicate_check"] != "no_duplicate"
    if expected == "unapproved_vendor":
        return audit["vendor_check"] != "approved"
    if expected == "total_mismatch":
        return audit["total_check"] == "mismatch"
    if expected == "anomaly":
        return bool(((audit.get("details") or {}).get("anomaly") or {}).get("is_anomaly"))
    return False


def main():
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    passed = 0
    with httpx.Client(base_url=BASE, timeout=180) as client:
        existing = client.get("/invoices").json()
        if existing:
            raise SystemExit(f"Database already has {len(existing)} invoices. "
                             "Stop the server, delete invoice_audit.db, restart, then rerun.")
        for row in rows:
            name, expected = row["filename"], row["expected_audit"]
            path = PDF_DIR / name
            if not path.exists():
                print(f"SKIP  {name} (file missing)")
                continue

            with open(path, "rb") as f:
                up = client.post("/upload-invoice", files={"file": (name, f, "application/pdf")})
            up.raise_for_status()
            invoice = up.json()

            res = client.post(f"/analyze-invoice/{invoice['id']}")
            res.raise_for_status()
            audit = res.json()

            ok = matches(expected, audit)
            passed += ok
            print(f"{'PASS' if ok else 'FAIL'}  {name:24} expected={expected:18} "
                  f"got={audit['final_status']:13} vendor={invoice['vendor_name'][:24]}")
            if not ok:
                print("        reasons:", audit["reasons"])

    print(f"\n{passed}/{len(rows)} match the ground truth")


if __name__ == "__main__":
    main()