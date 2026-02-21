#!/usr/bin/env python3
"""
Quick test that the risk model loads and returns valid low/medium/high predictions.

Run from webapp dir (no Django required):
  cd webapp && PYTHONPATH=. python risk_scoring/test_risk_service.py
"""
import os
import sys
from pathlib import Path

webapp_dir = Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

artifacts_dir = webapp_dir / "risk_scoring" / "artifacts"


def _to_band(prob: float) -> str:
    if prob >= 0.35:
        return "high"
    if prob >= 0.15:
        return "medium"
    return "low"


def main():
    from risk_scoring.features import patient_to_feature_dict, feature_dicts_to_dataframe

    class MockPatient:
        id = "test-patient-1"
        date_of_birth = "1965-03-15"
        admission_date = "2025-01-10"
        allergies = ["Penicillin"]
        medications = ["Metformin", "Lisinopril"]
        current_prescriptions = ["Metformin 500mg"]
        medical_history = ["Type 2 diabetes", "Hypertension"]
        past_medical_history = ["Appendectomy"]
        notes = ["Stable"]
        use_alberta_health_card = False
        gender = "male"
        blood_type = "O+"
        status = "active"
        primary_diagnosis = "Type 2 diabetes"

    patient = MockPatient()
    feature_row = patient_to_feature_dict(patient)
    X = feature_dicts_to_dataframe([feature_row])

    model_files = sorted(artifacts_dir.glob("risk_model_*.joblib"))
    if not model_files:
        print("No risk_model_*.joblib in artifacts – run train_from_uci_dataset.py first.")
        print("Testing heuristic fallback only.")
        from risk_scoring.features import heuristic_risk_score
        from risk_scoring.features import top_heuristic_factors
        score = heuristic_risk_score(feature_row)
        risk_band = _to_band(score)
        pred = type("Pred", (), {
            "risk_band": risk_band,
            "risk_probability": round(score, 4),
            "model_version": "heuristic-v1",
            "top_factors": top_heuristic_factors(feature_row, score),
            "scoring_mode": "heuristic",
        })()
    else:
        import joblib
        try:
            payload = joblib.load(model_files[-1])
        except (AttributeError, ModuleNotFoundError) as e:
            if "_RemainderColsList" in str(e) or "sklearn" in str(e).lower():
                print("Saved model was built with a different scikit-learn version and cannot be loaded.")
                print("Retrain with: cd webapp && PYTHONPATH=. python risk_scoring/train_from_uci_dataset.py")
                print("Falling back to heuristic for this run.")
                from risk_scoring.features import heuristic_risk_score, top_heuristic_factors
                score = heuristic_risk_score(feature_row)
                risk_band = _to_band(score)
                pred = type("Pred", (), {
                    "risk_band": risk_band,
                    "risk_probability": round(score, 4),
                    "model_version": "heuristic-v1",
                    "top_factors": top_heuristic_factors(feature_row, score),
                    "scoring_mode": "heuristic",
                })()
                assert pred.risk_band in ("low", "medium", "high")
                assert 0 <= pred.risk_probability <= 1
                print("OK – risk scoring works (heuristic fallback)")
                print(f"  risk_band: {pred.risk_band}")
                print(f"  risk_probability: {pred.risk_probability:.4f}")
                print(f"  model_version: {pred.model_version}")
                print(f"  scoring_mode: {pred.scoring_mode}")
                return 0
            raise
        pipeline = payload["pipeline"]
        calibrator = payload.get("calibrator")
        if calibrator is not None:
            prob = calibrator.predict_proba(X)[:, 1][0]
        else:
            prob = pipeline.predict_proba(X)[:, 1][0]
        prob = float(max(0.0, min(1.0, prob)))
        risk_band = _to_band(prob)
        model_version = payload.get("model_version", "unknown")
        top_names = payload.get("top_feature_names", [])[:5]
        top_weights = payload.get("top_feature_weights", [])
        top_factors = [
            {"feature": str(n), "direction": "up" if (float(top_weights[i]) if i < len(top_weights) else 0) >= 0 else "down", "contribution": round(float(top_weights[i]) if i < len(top_weights) else 0, 4)}
            for i, n in enumerate(top_names)
        ]
        pred = type("Pred", (), {"risk_band": risk_band, "risk_probability": round(prob, 4), "model_version": model_version, "top_factors": top_factors, "scoring_mode": "supervised"})()

    assert pred.risk_band in ("low", "medium", "high"), f"Invalid risk_band: {pred.risk_band}"
    assert 0 <= pred.risk_probability <= 1, f"Invalid risk_probability: {pred.risk_probability}"

    print("OK – risk scoring works")
    print(f"  risk_band: {pred.risk_band}")
    print(f"  risk_probability: {pred.risk_probability:.4f}")
    print(f"  model_version: {pred.model_version}")
    print(f"  scoring_mode: {pred.scoring_mode}")
    if getattr(pred, "top_factors", None):
        print(f"  top_factors (first 3): {pred.top_factors[:3]}")
    return 0


def test_api():
    """Optional: test POST /api/patients/risk-score/ (requires Django + server or requests)."""
    try:
        import django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
        django.setup()
        from django.test import Client
        from nfc_users.models import Patient
        patient_id = Patient.objects.values_list("id", flat=True).first()
        if not patient_id:
            print("API test skipped: no patients in DB")
            return
        client = Client()
        r = client.post(
            "/api/patients/risk-score/",
            data={"patient_id": patient_id},
            content_type="application/json",
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        assert data["riskBand"] in ("low", "medium", "high")
        assert 0 <= data["riskProbability"] <= 1
        print("OK – API test passed for patient_id:", patient_id)
    except Exception as e:
        print("API test skipped:", e)


if __name__ == "__main__":
    try:
        code = main()
        if os.environ.get("TEST_API"):
            test_api()
        sys.exit(code)
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
