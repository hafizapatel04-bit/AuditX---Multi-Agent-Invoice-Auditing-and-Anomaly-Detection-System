"""
Single entry point for anomaly detection.
Person B calls: check_anomaly(amount, category, vendor)
"""
import csv
from pathlib import Path

from anomaly.detector import check_anomaly_statistical
from anomaly.ml_detector import check_anomaly_ml
from sample_data.historical_invoices import historical_invoices as fallback_history

CSV_PATH = Path(__file__).resolve().parents[1] / "sample_data" / "invoices.csv"


def _load_history():
    if not CSV_PATH.exists():
        return fallback_history
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return [{"amount": float(r["amount"]), "category": r["category"]}
                for r in csv.DictReader(f)]


def check_anomaly(amount, category, vendor):
    stat = check_anomaly_statistical(amount, category, _load_history())
    ml = check_anomaly_ml(amount, category, vendor)

    # Flag if EITHER detector flags it
    is_anomaly = stat["is_anomaly"] or ml["is_anomaly"]

    reasons = []
    if stat["is_anomaly"]:
        reasons.append(stat["reason"])
    if ml["is_anomaly"]:
        reasons.append(ml["reason"])
    if not reasons:
        reasons.append("Amount is within the expected range for this category")

    return {
        "is_anomaly": is_anomaly,
        "reason": "; ".join(reasons),
        "details": {"statistical": stat, "isolation_forest": ml},
    }