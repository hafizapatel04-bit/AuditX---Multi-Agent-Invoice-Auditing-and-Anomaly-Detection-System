"""
Trains the Isolation Forest model and saves it to anomaly/model/.
Run: venv\\Scripts\\python.exe anomaly\\train_model.py
"""
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

BASE_DIR = Path(__file__).resolve().parent
INVOICES_CSV = BASE_DIR.parent / "sample_data" / "invoices.csv"
MODEL_DIR = BASE_DIR / "model"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

CONTAMINATION = 0.05


def build_features(df):
    category_encoder = LabelEncoder()
    df = df.copy()
    df["category_encoded"] = category_encoder.fit_transform(df["category"])
    vendor_frequency = df["vendor"].value_counts().to_dict()
    df["vendor_frequency"] = df["vendor"].map(vendor_frequency)
    features = df[["amount", "category_encoded", "vendor_frequency"]]
    return features, category_encoder, vendor_frequency


def main():
    if not INVOICES_CSV.exists():
        raise FileNotFoundError(f"{INVOICES_CSV} not found. Run sample_data/make_history.py first.")

    df = pd.read_csv(INVOICES_CSV)
    print(f"Loaded {len(df)} historical invoices.")

    features, category_encoder, vendor_frequency = build_features(df)

    model = IsolationForest(n_estimators=200, contamination=CONTAMINATION, random_state=42)
    model.fit(features)

    joblib.dump(model, MODEL_DIR / "anomaly_model.pkl")
    joblib.dump(category_encoder, MODEL_DIR / "category_encoder.pkl")
    joblib.dump(vendor_frequency, MODEL_DIR / "vendor_frequency.pkl")

    flagged = (model.predict(features) == -1).sum()
    print(f"Saved model to {MODEL_DIR}")
    print(f"Flagged {flagged}/{len(df)} historical invoices (expected: roughly 5%).")


if __name__ == "__main__":
    main()