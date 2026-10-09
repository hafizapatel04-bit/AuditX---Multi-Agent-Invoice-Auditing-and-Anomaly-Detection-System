"""
Isolation Forest detector. Needs anomaly/train_model.py to have been run once.
Returns the same keys as detector.py: is_anomaly, score, reason (+ method).
"""
from pathlib import Path
import joblib
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parent / "model"
MODEL_PATH = MODEL_DIR / "anomaly_model.pkl"
ENCODER_PATH = MODEL_DIR / "category_encoder.pkl"
VENDOR_FREQ_PATH = MODEL_DIR / "vendor_frequency.pkl"


def model_available() -> bool:
    return MODEL_PATH.exists() and ENCODER_PATH.exists() and VENDOR_FREQ_PATH.exists()


def check_anomaly_ml(amount, category, vendor):
    if not model_available():
        return {"is_anomaly": False, "score": 0.0, "method": "isolation_forest",
                "reason": "ML model not trained yet", "error": "model_not_trained"}

    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)
    vendor_frequency = joblib.load(VENDOR_FREQ_PATH)

    try:
        category_encoded = encoder.transform([category])[0]
    except ValueError:
        category_encoded = -1  # category the model has never seen

    features = pd.DataFrame([{
        "amount": amount,
        "category_encoded": category_encoded,
        "vendor_frequency": vendor_frequency.get(vendor, 0),
    }])

    is_anomaly = model.predict(features)[0] == -1   # -1 = anomaly, 1 = normal
    score = round(float(model.decision_function(features)[0]), 4)  # lower = more unusual

    return {
        "is_anomaly": bool(is_anomaly),
        "score": score,
        "method": "isolation_forest",
        "reason": ("Isolation Forest flagged this invoice as unusual compared with historical invoices"
                   if is_anomaly else
                   "Invoice fits the historical pattern"),
    }