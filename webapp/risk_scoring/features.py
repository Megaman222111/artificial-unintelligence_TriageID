from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List

# Compact feature schema shared by training and live scoring.
# Keep this small and aligned with fields that exist in both the app and UCI training data.
FEATURE_NUMERIC_COLUMNS = [
    "age_years",
    "days_since_admission",
    "medication_count",
    "current_prescription_count",
    "allergy_count",
    "high_risk_allergy_count",
    "history_count",
    "high_risk_history_count",
    "past_history_count",
    "high_risk_prescription_count",
]
FEATURE_CATEGORICAL_COLUMNS = ["gender"]
FEATURE_COLUMN_ORDER: List[str] = FEATURE_NUMERIC_COLUMNS + FEATURE_CATEGORICAL_COLUMNS

SERIOUS_CONDITION_WEIGHTS: Dict[str, float] = {
    "sepsis": 18.0,
    "septic": 18.0,
    "stroke": 16.0,
    "myocardial infarction": 16.0,
    "heart failure": 16.0,
    "metastatic": 20.0,
    "cancer": 12.0,
    "renal failure": 12.0,
    "ckd": 10.0,
    "copd": 10.0,
    "pneumonia": 10.0,
}

HIGH_RISK_ALLERGY_KEYWORDS = (
    "penicillin",
    "cephalosporin",
    "sulfa",
    "latex",
    "iodine",
    "contrast",
    "peanut",
    "shellfish",
)

HIGH_RISK_PRESCRIPTION_KEYWORDS = (
    "warfarin",
    "heparin",
    "enoxaparin",
    "insulin",
    "morphine",
    "fentanyl",
    "oxycodone",
    "prednisone",
    "chemotherapy",
    "immunosuppress",
)

HIGH_RISK_HISTORY_KEYWORDS = tuple(SERIOUS_CONDITION_WEIGHTS.keys()) + (
    "aneurysm",
    "arrhythmia",
    "shock",
    "dka",
    "liver failure",
)


# Parse ISO-like date/datetime strings into a date; return None on empty/invalid.
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


# Normalize patient fields that may be scalar/list/dict into a clean list[str].
# This keeps downstream count features stable regardless of source shape.
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


def _serious_condition_score(entries: list[str]) -> float:
    if not entries:
        return 0.0
    joined = " ".join(entries).lower()
    score = 0.0
    for keyword, weight in SERIOUS_CONDITION_WEIGHTS.items():
        if keyword in joined:
            score += float(weight)
    return min(35.0, score)


def _keyword_hit_count(entries: list[str], keywords: tuple[str, ...]) -> int:
    if not entries:
        return 0
    hits = 0
    for item in entries:
        text = item.lower()
        if any(k in text for k in keywords):
            hits += 1
    return hits


# Build one model-ready feature row from a patient object.
# Computes bounded age/length-of-stay features, count features, and normalized categories.
def patient_to_feature_dict(patient: Any, *, now_date: date | None = None) -> Dict[str, Any]:
    today = now_date or date.today()

    dob = _safe_date(getattr(patient, "date_of_birth", "") or "")
    admission = _safe_date(getattr(patient, "admission_date", "") or "")
    age_years_raw = (today - dob).days // 365 if dob else None
    days_since_admission_raw = (today - admission).days if admission else None
    age_years = age_years_raw
    days_since_admission = days_since_admission_raw
    if age_years is not None:
        age_years = max(0, min(120, age_years))
    if days_since_admission is not None:
        days_since_admission = max(0, min(30, days_since_admission))

    allergies = _as_list(getattr(patient, "allergies", []))
    meds = _as_list(getattr(patient, "medications", []))
    prescriptions = _as_list(getattr(patient, "current_prescriptions", []))
    history = _as_list(getattr(patient, "medical_history", []))
    past_history = _as_list(getattr(patient, "past_medical_history", []))
    primary_diagnosis = str(getattr(patient, "primary_diagnosis", "") or "").strip()
    status = (getattr(patient, "status", "") or "unknown").strip().lower() or "unknown"
    combined_history = list(history) + list(past_history)
    if primary_diagnosis:
        combined_history.append(primary_diagnosis)
    high_risk_history_count = _keyword_hit_count(combined_history, HIGH_RISK_HISTORY_KEYWORDS)
    high_risk_allergy_count = _keyword_hit_count(allergies, HIGH_RISK_ALLERGY_KEYWORDS)
    high_risk_prescription_count = _keyword_hit_count(
        prescriptions, HIGH_RISK_PRESCRIPTION_KEYWORDS
    )
    serious_condition_score = _serious_condition_score(combined_history)
    serious_condition_score += (4.0 * high_risk_allergy_count) + (
        5.0 * high_risk_prescription_count
    )
    serious_condition_score = min(40.0, serious_condition_score)

    return {
        "age_years": float(age_years) if age_years is not None and age_years >= 0 else 0.0,
        "days_since_admission": float(days_since_admission) if days_since_admission is not None else 0.0,
        "medication_count": float(len(meds) + len(prescriptions)),
        "current_prescription_count": float(len(prescriptions)),
        "allergy_count": float(len(allergies)),
        "high_risk_allergy_count": float(high_risk_allergy_count),
        "history_count": float(len(history) + (1 if primary_diagnosis else 0)),
        "high_risk_history_count": float(high_risk_history_count),
        "past_history_count": float(len(past_history)),
        "high_risk_prescription_count": float(high_risk_prescription_count),
        "gender": (getattr(patient, "gender", "") or "unknown").strip().lower() or "unknown",
        "age_years_raw": float(age_years_raw) if age_years_raw is not None and age_years_raw >= 0 else 0.0,
        "days_since_admission_raw": (
            float(max(0, days_since_admission_raw))
            if days_since_admission_raw is not None
            else 0.0
        ),
        "serious_condition_score": float(serious_condition_score),
        # Status is not part of supervised features but is used by heuristic fallback.
        "status": status,
    }

# Compute a bounded fallback probability using transparent additive rules.
# Used when no trained model is available or model prediction fails.
def heuristic_risk_score(feature_row: Dict[str, Any]) -> float:
    """Same rule-based score used when no trained model is available (0–1)."""
    score = 0.08
    if feature_row.get("status") == "critical":
        score += 0.20
    if (feature_row.get("days_since_admission") or 0) >= 14:
        score += 0.10
    if (feature_row.get("age_years") or 0) >= 75:
        score += 0.08
    if (feature_row.get("history_count") or 0) >= 4:
        score += 0.06
    if (feature_row.get("past_history_count") or 0) >= 2:
        score += 0.04
    if (feature_row.get("medication_count") or 0) == 0:
        score -= 0.04
    if (feature_row.get("allergy_count") or 0) >= 2:
        score += 0.03
    if (feature_row.get("high_risk_allergy_count") or 0) >= 1:
        score += 0.06
    if (feature_row.get("current_prescription_count") or 0) >= 3:
        score += 0.04
    if (feature_row.get("high_risk_prescription_count") or 0) >= 1:
        score += 0.06
    if (feature_row.get("high_risk_history_count") or 0) >= 1:
        score += 0.08
    if (feature_row.get("days_since_admission_raw") or 0) >= 60:
        score += 0.05
    if (feature_row.get("days_since_admission_raw") or 0) >= 180:
        score += 0.05
    score += min(0.15, (feature_row.get("serious_condition_score") or 0.0) / 250.0)
    return max(0.01, min(0.95, score))


# Return up to 5 rule contributions explaining the heuristic score.
# Keeps explainability payload shape similar to supervised scoring mode.
def top_heuristic_factors(feature_row: Dict[str, Any], score: float) -> list[Dict[str, Any]]:
    factors: list[Dict[str, Any]] = []
    if feature_row["status"] == "critical":
        factors.append({"feature": "status=critical", "direction": "up", "contribution": 0.20})
    if feature_row["days_since_admission"] >= 14:
        factors.append({"feature": "days_since_admission>=14", "direction": "up", "contribution": 0.10})
    if feature_row["age_years"] >= 75:
        factors.append({"feature": "age>=75", "direction": "up", "contribution": 0.08})
    if feature_row["history_count"] >= 4:
        factors.append(
            {
                "feature": "medical_history_count>=4",
                "direction": "up",
                "contribution": 0.06,
            }
        )
    if feature_row["past_history_count"] >= 2:
        factors.append(
            {
                "feature": "past_medical_history_count>=2",
                "direction": "up",
                "contribution": 0.04,
            }
        )
    if feature_row["medication_count"] == 0:
        factors.append(
            {
                "feature": "medications_count=0",
                "direction": "down",
                "contribution": -0.04,
            }
        )
    if feature_row.get("allergy_count", 0) >= 2:
        factors.append(
            {"feature": "allergy_count>=2", "direction": "up", "contribution": 0.03}
        )
    if feature_row.get("high_risk_allergy_count", 0) >= 1:
        factors.append(
            {
                "feature": "high_risk_allergy_count>=1",
                "direction": "up",
                "contribution": 0.06,
            }
        )
    if feature_row.get("current_prescription_count", 0) >= 3:
        factors.append(
            {
                "feature": "current_prescription_count>=3",
                "direction": "up",
                "contribution": 0.04,
            }
        )
    if feature_row.get("high_risk_prescription_count", 0) >= 1:
        factors.append(
            {
                "feature": "high_risk_prescription_count>=1",
                "direction": "up",
                "contribution": 0.06,
            }
        )
    if feature_row.get("high_risk_history_count", 0) >= 1:
        factors.append(
            {
                "feature": "high_risk_history_count>=1",
                "direction": "up",
                "contribution": 0.08,
            }
        )
    if feature_row.get("days_since_admission_raw", 0) >= 60:
        factors.append(
            {
                "feature": "days_since_admission_raw>=60",
                "direction": "up",
                "contribution": 0.05,
            }
        )
    if feature_row.get("days_since_admission_raw", 0) >= 180:
        factors.append(
            {
                "feature": "days_since_admission_raw>=180",
                "direction": "up",
                "contribution": 0.05,
            }
        )
    severe_bonus = min(0.12, (feature_row.get("serious_condition_score") or 0.0) / 300.0)
    if severe_bonus > 0:
        factors.append(
            {
                "feature": "serious_conditions",
                "direction": "up",
                "contribution": round(severe_bonus, 4),
            }
        )

    if not factors:
        factors.append({"feature": "baseline_risk", "direction": "up", "contribution": round(score, 4)})
    return factors[:5]


# Convert feature dict rows into a DataFrame expected by the sklearn pipeline.
# Enforces column order and normalizes numeric/categorical dtypes.
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
    # Ensure categorical columns are normalized strings
    for col in FEATURE_CATEGORICAL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna("unknown").astype(str).str.strip().str.lower().replace("", "unknown")
    return df
