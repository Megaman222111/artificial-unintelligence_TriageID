#!/usr/bin/env python3
"""
Train the patient risk model using the UCI Diabetes 130-US Hospitals dataset.

Dataset: Diabetes 130-US hospitals for years 1999-2008
URL: https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008
Paper: Strack et al., "Impact of HbA1c Measurement on Hospital Readmission Rates",
       BioMed Research International, 2014. CC BY 4.0.

Outcome: 30-day readmission (readmitted == '<30' -> high risk).

Run from repo root:
  PYTHONPATH=webapp python webapp/risk_scoring/train_from_uci_dataset.py

Or from webapp dir:
  PYTHONPATH=. python risk_scoring/train_from_uci_dataset.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

# Ensure we can import risk_scoring
_webapp = Path(__file__).resolve().parent.parent
if _webapp.name == "risk_scoring":
    _webapp = _webapp.parent
if str(_webapp) not in sys.path:
    sys.path.insert(0, str(_webapp))

from risk_scoring.features import (
    FEATURE_COLUMN_ORDER,
    feature_dicts_to_dataframe,
)
from risk_scoring.fit_pipeline import fit_and_save_pipeline

UCI_DATASET_URL = "https://archive.ics.uci.edu/static/public/296/diabetes+130-us+hospitals+for+years+1999-2008.zip"
UCI_DATASET_NAME = "Diabetes 130-US Hospitals for Years 1999-2008"
UCI_DATASET_REF = "https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008"


def _age_bracket_to_years(age_str: str) -> float:
    """Map UCI age brackets like '[0-10)' to midpoint years."""
    if not age_str or not isinstance(age_str, str):
        return 45.0
    m = re.match(r"\[(\d+)-(\d+)\)", age_str.strip())
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return float((lo + hi) // 2)
    return 45.0


def load_uci_diabetes_csv(csv_path: Path) -> pd.DataFrame:
    """Load diabetic_data.csv; download zip if csv_path does not exist."""
    if csv_path.exists():
        return pd.read_csv(csv_path)
    # Download
    import urllib.request
    import zipfile

    zip_path = csv_path.parent / "diabetes_uci.zip"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {UCI_DATASET_NAME} from UCI...")
    urllib.request.urlretrieve(UCI_DATASET_URL, zip_path)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extract("diabetic_data.csv", path=csv_path.parent)
    return pd.read_csv(csv_path)


def uci_to_feature_rows(df: pd.DataFrame) -> tuple[list[dict], list[int]]:
    """Map UCI diabetic_data.csv to our feature dicts and binary labels (1 = readmitted <30)."""
    rows = []
    labels = []
    for _, r in df.iterrows():
        age_years = _age_bracket_to_years(str(r.get("age", "")))
        time_in_hospital = int(r.get("time_in_hospital", 0)) if pd.notna(r.get("time_in_hospital")) else 0
        num_medications = int(r.get("num_medications", 0)) if pd.notna(r.get("num_medications")) else 0
        number_diagnoses = int(r.get("number_diagnoses", 0)) if pd.notna(r.get("number_diagnoses")) else 0
        number_inpatient = int(r.get("number_inpatient", 0)) if pd.notna(r.get("number_inpatient")) else 0
        number_outpatient = int(r.get("number_outpatient", 0)) if pd.notna(r.get("number_outpatient")) else 0
        number_emergency = int(r.get("number_emergency", 0)) if pd.notna(r.get("number_emergency")) else 0
        gender = (str(r.get("gender", "Unknown")).strip().lower() or "unknown")[:20]
        if gender not in ("male", "female", "unknown"):
            gender = "unknown"

        rows.append({
            "age_years": float(age_years),
            "days_since_admission": float(time_in_hospital),
            "medication_count": float(num_medications),
            "history_count": float(number_diagnoses),
            "past_history_count": float(number_inpatient + number_outpatient + number_emergency),
            "gender": gender,
        })
        # Label: 1 if readmitted within 30 days
        readmitted = str(r.get("readmitted", "NO")).strip()
        labels.append(1 if readmitted == "<30" else 0)
    return rows, labels


def main():
    # Use webapp/risk_scoring/artifacts by default; allow override
    base = _webapp
    if base.name != "webapp":
        base = base / "webapp"
    model_dir = base / "risk_scoring" / "artifacts"
    data_dir = base / "risk_scoring" / "data"
    csv_path = data_dir / "diabetic_data.csv"

    df = load_uci_diabetes_csv(csv_path)
    # Cap rows for faster training (optional; remove to use full 100k+)
    max_rows = 50_000
    if len(df) > max_rows:
        df = df.sample(n=max_rows, random_state=42).reset_index(drop=True)
        print(f"Using subsample of {len(df)} rows for faster training.")
    print(f"Loaded {len(df)} rows from {csv_path.name}")

    rows, labels = uci_to_feature_rows(df)
    positives = sum(labels)
    print(f"Positives (readmitted <30): {positives} ({100.0 * positives / len(labels):.1f}%)")

    X = feature_dicts_to_dataframe(rows)
    if not all(c in X.columns for c in FEATURE_COLUMN_ORDER):
        raise ValueError("Feature columns mismatch")
    model_version = f"uci-simple-{len(X)}rows-{positives}pos"
    result = fit_and_save_pipeline(X, labels, model_dir, model_version=model_version)
    print(f"Saved model: {model_dir / ('risk_model_' + result.model_version + '.joblib')}")
    print(f"  rows={result.rows} positives={result.positives} calibrator={result.calibrator}")
    print("")
    print("Dataset used:")
    print(f"  {UCI_DATASET_NAME}")
    print(f"  {UCI_DATASET_REF}")
    print("  Outcome: 30-day readmission (readmitted == '<30').")
    return 0


if __name__ == "__main__":
    sys.exit(main())
