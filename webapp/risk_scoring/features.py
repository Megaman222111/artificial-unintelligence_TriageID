from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List

# Column order expected by the risk model pipeline (must match train.py ColumnTransformer).
FEATURE_NUMERIC_COLUMNS = [
    "age_years",
    "days_since_admission",
    "allergy_count",
    "medication_count",
    "prescription_count",
    "history_count",
    "past_history_count",
]
FEATURE_CATEGORICAL_COLUMNS = ["gender", "blood_type", "status", "insurance_mode"]
FEATURE_TEXT_COLUMN = "text"
FEATURE_COLUMN_ORDER: List[str] = (
    FEATURE_NUMERIC_COLUMNS + FEATURE_CATEGORICAL_COLUMNS + [FEATURE_TEXT_COLUMN]
)


def _safe_date(value: str) -> date | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _as_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                out.append(" ".join(str(v).strip() for v in item.values() if str(v).strip()))
            else:
                out.append(str(item).strip())
        return [x for x in out if x]
    return [str(value).strip()] if str(value).strip() else []


def patient_to_feature_dict(patient: Any, *, now_date: date | None = None) -> Dict[str, Any]:
    today = now_date or date.today()

    dob = _safe_date(getattr(patient, "date_of_birth", "") or "")
    admission = _safe_date(getattr(patient, "admission_date", "") or "")
    age_years = (today - dob).days // 365 if dob else None
    days_since_admission = (today - admission).days if admission else None

    allergies = _as_list(getattr(patient, "allergies", []))
    meds = _as_list(getattr(patient, "medications", []))
    current_rx = _as_list(getattr(patient, "current_prescriptions", []))
    history = _as_list(getattr(patient, "medical_history", []))
    past_history = _as_list(getattr(patient, "past_medical_history", []))
    notes = _as_list(getattr(patient, "notes", []))

    insurance_mode = "alberta" if bool(getattr(patient, "use_alberta_health_card", False)) else "insurance"

    return {
        "age_years": float(age_years) if age_years is not None and age_years >= 0 else 0.0,
        "days_since_admission": float(days_since_admission) if days_since_admission is not None else 0.0,
        "allergy_count": float(len(allergies)),
        "medication_count": float(len(meds)),
        "prescription_count": float(len(current_rx)),
        "history_count": float(len(history)),
        "past_history_count": float(len(past_history)),
        "gender": (getattr(patient, "gender", "") or "unknown").strip().lower() or "unknown",
        "blood_type": (getattr(patient, "blood_type", "") or "unknown").strip().upper() or "unknown",
        "status": (getattr(patient, "status", "") or "unknown").strip().lower() or "unknown",
        "insurance_mode": insurance_mode,
        "text": " ".join(
            [
                str(getattr(patient, "primary_diagnosis", "") or "").strip(),
                " ".join(history),
                " ".join(past_history),
                " ".join(notes),
            ]
        ).strip(),
    }


def heuristic_risk_score(feature_row: Dict[str, Any]) -> float:
    """Same rule-based score used when no trained model is available (0–1)."""
    score = 0.08
    if feature_row.get("status") == "critical":
        score += 0.30
    if (feature_row.get("days_since_admission") or 0) >= 14:
        score += 0.12
    if (feature_row.get("age_years") or 0) >= 75:
        score += 0.10
    if (feature_row.get("allergy_count") or 0) >= 3:
        score += 0.06
    if (feature_row.get("history_count") or 0) >= 3:
        score += 0.08
    if (feature_row.get("medication_count") or 0) == 0 and (feature_row.get("prescription_count") or 0) == 0:
        score -= 0.06
    return max(0.01, min(0.95, score))


def top_heuristic_factors(feature_row: Dict[str, Any], score: float) -> list[Dict[str, Any]]:
    factors: list[Dict[str, Any]] = []
    if feature_row["status"] == "critical":
        factors.append({"feature": "status=critical", "direction": "up", "contribution": 0.30})
    if feature_row["days_since_admission"] >= 14:
        factors.append({"feature": "days_since_admission>=14", "direction": "up", "contribution": 0.12})
    if feature_row["age_years"] >= 75:
        factors.append({"feature": "age>=75", "direction": "up", "contribution": 0.10})
    if feature_row["allergy_count"] >= 3:
        factors.append({"feature": "allergy_count>=3", "direction": "up", "contribution": 0.06})
    if feature_row["history_count"] >= 3:
        factors.append({"feature": "history_count>=3", "direction": "up", "contribution": 0.08})
    if feature_row["medication_count"] == 0 and feature_row["prescription_count"] == 0:
        factors.append({"feature": "no_medications_or_prescriptions", "direction": "down", "contribution": -0.06})

    if not factors:
        factors.append({"feature": "baseline_risk", "direction": "up", "contribution": round(score, 4)})
    return factors[:5]


def feature_dicts_to_dataframe(rows: List[Dict[str, Any]]):
    """Convert list of feature dicts to a DataFrame with columns in pipeline order."""
    import pandas as pd

    if not rows:
        return pd.DataFrame(columns=FEATURE_COLUMN_ORDER)
    df = pd.DataFrame(rows, columns=FEATURE_COLUMN_ORDER)
    # Ensure numeric columns are numeric (fill missing with 0)
    for col in FEATURE_NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)
    # Ensure text column is string
    if FEATURE_TEXT_COLUMN in df.columns:
        df[FEATURE_TEXT_COLUMN] = df[FEATURE_TEXT_COLUMN].fillna("").astype(str)
    return df

