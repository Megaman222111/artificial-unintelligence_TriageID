from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from django.conf import settings

from .features import patient_to_feature_dict, top_heuristic_factors, feature_dicts_to_dataframe


@dataclass
class RiskPrediction:
    risk_probability: float
    risk_band: str
    model_version: str
    top_factors: List[Dict[str, Any]]
    scoring_mode: str


class RiskScoringService:
    def __init__(self):
        self.model_dir = Path(settings.BASE_DIR) / "risk_scoring" / "artifacts"

    @staticmethod
    def _to_band(prob: float) -> str:
        if prob >= 0.35:
            return "high"
        if prob >= 0.15:
            return "medium"
        return "low"

    def _heuristic_score(self, feature_row: Dict[str, Any]) -> float:
        score = 0.08
        if feature_row["status"] == "critical":
            score += 0.30
        if feature_row["days_since_admission"] >= 14:
            score += 0.12
        if feature_row["age_years"] >= 75:
            score += 0.10
        if feature_row["allergy_count"] >= 3:
            score += 0.06
        if feature_row["history_count"] >= 3:
            score += 0.08
        if feature_row["medication_count"] == 0 and feature_row["prescription_count"] == 0:
            score -= 0.06
        return max(0.01, min(0.95, score))

    def predict(self, patient: Any) -> RiskPrediction:
        feature_row = patient_to_feature_dict(patient)
        model_payload = self._load_latest_model_payload()
        if not model_payload:
            score = self._heuristic_score(feature_row)
            return RiskPrediction(
                risk_probability=round(score, 4),
                risk_band=self._to_band(score),
                model_version="heuristic-v1",
                top_factors=top_heuristic_factors(feature_row, score),
                scoring_mode="heuristic",
            )

        pipeline = model_payload["pipeline"]
        calibrator = model_payload.get("calibrator")
        X = feature_dicts_to_dataframe([feature_row])
        if calibrator:
            prob = calibrator.predict_proba(X)[:, 1][0]
        else:
            prob = pipeline.predict_proba(X)[:, 1][0]
        prob = float(max(0.0, min(1.0, prob)))

        factors = []
        top_names = model_payload.get("top_feature_names", [])
        top_weights = model_payload.get("top_feature_weights", [])
        for idx, name in enumerate(top_names[:5]):
            weight = float(top_weights[idx]) if idx < len(top_weights) else 0.0
            factors.append(
                {
                    "feature": str(name),
                    "direction": "up" if weight >= 0 else "down",
                    "contribution": round(weight, 4),
                }
            )

        return RiskPrediction(
            risk_probability=round(prob, 4),
            risk_band=self._to_band(prob),
            model_version=model_payload.get("model_version", "model-unknown"),
            top_factors=factors,
            scoring_mode="supervised",
        )

    def _load_latest_model_payload(self) -> Dict[str, Any] | None:
        if not self.model_dir.exists():
            return None
        model_files = sorted(self.model_dir.glob("risk_model_*.joblib"))
        if not model_files:
            return None
        latest = model_files[-1]
        try:
            import joblib
        except Exception:
            return None
        try:
            return joblib.load(latest)
        except Exception:
            return None
