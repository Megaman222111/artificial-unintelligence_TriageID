from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

from django.conf import settings
from django.utils import timezone

from nfc_users.models import Patient, PatientOutcomeEvent

from .features import (
    patient_to_feature_dict,
    feature_dicts_to_dataframe,
    heuristic_risk_score,
)
from .fit_pipeline import TrainingResult


def _build_training_rows(now=None) -> Tuple[List[Dict[str, Any]], List[int]]:
    now = now or timezone.now()
    horizon = now + timedelta(days=30)
    rows: List[Dict[str, Any]] = []
    labels: List[int] = []

    outcomes = PatientOutcomeEvent.objects.filter(
        event_type__in=[PatientOutcomeEvent.EventType.CRITICAL_DETERIORATION, PatientOutcomeEvent.EventType.DEATH]
    )
    by_patient: Dict[str, List[PatientOutcomeEvent]] = {}
    for event in outcomes:
        by_patient.setdefault(event.patient_id, []).append(event)

    for patient in Patient.objects.all():
        rows.append(patient_to_feature_dict(patient, now_date=now.date()))
        events = by_patient.get(patient.id, [])
        positive = any(now <= e.event_time <= horizon for e in events)
        labels.append(1 if positive else 0)

    return rows, labels


def train_and_save(min_rows: int = 25, min_positives: int = 5) -> TrainingResult:
    from .fit_pipeline import TrainingResult as FitResult
    from .fit_pipeline import fit_and_save_pipeline

    rows, labels = _build_training_rows()
    positives = int(sum(labels))

    # If we have enough rows but too few real outcome labels, use heuristic-based
    # synthetic labels so a model can still be trained (e.g. for demo / cold start).
    if len(rows) >= min_rows and positives < min_positives:
        labels = [1 if heuristic_risk_score(r) >= 0.35 else 0 for r in rows]
        positives = int(sum(labels))

    if len(rows) < min_rows:
        raise RuntimeError(
            f"Not enough patients to train: rows={len(rows)}, required>={min_rows}."
        )
    if positives < 1:
        raise RuntimeError(
            "Need at least one positive label (real outcome or heuristic-based)."
        )

    X = feature_dicts_to_dataframe(rows)
    model_dir = Path(settings.BASE_DIR) / "risk_scoring" / "artifacts"
    model_version = timezone.now().strftime("risk-v1-%Y%m%d%H%M%S")
    result = fit_and_save_pipeline(X, labels, model_dir, model_version=model_version)
    return TrainingResult(
        model_version=result.model_version,
        rows=result.rows,
        positives=result.positives,
        calibrator=result.calibrator,
    )
