from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

from django.conf import settings
from django.utils import timezone

from nfc_users.models import Patient, PatientOutcomeEvent

from .features import (
    patient_to_feature_dict,
    feature_dicts_to_dataframe,
)
from .fit_pipeline import TrainingResult


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


def _build_training_rows(now=None) -> Tuple[List[Dict[str, Any]], List[int]]:
    """
    Build labeled rows from observed outcomes in each patient's first 30 days since admission.
    Positive label: deterioration/death event within [admission_date, admission_date + 30 days].
    Negative label: no such event and at least 30 days have elapsed since admission.
    """
    now = now or timezone.now()
    now_date = now.date()
    rows: List[Dict[str, Any]] = []
    labels: List[int] = []

    outcomes = PatientOutcomeEvent.objects.filter(
        event_type__in=[PatientOutcomeEvent.EventType.CRITICAL_DETERIORATION, PatientOutcomeEvent.EventType.DEATH]
    )
    by_patient: Dict[str, List[PatientOutcomeEvent]] = {}
    for event in outcomes:
        by_patient.setdefault(event.patient_id, []).append(event)

    for patient in Patient.objects.all():
        admission_date = _safe_date(getattr(patient, "admission_date", "") or "")
        if not admission_date:
            continue

        events = by_patient.get(patient.id, [])
        horizon_end = admission_date + timedelta(days=30)
        positive_event_dates = sorted(
            e.event_time.date()
            for e in events
            if admission_date <= e.event_time.date() <= horizon_end
        )
        positive = bool(positive_event_dates)
        negative_observed = (not positive) and (now_date >= horizon_end)

        if not (positive or negative_observed):
            # Skip unresolved examples where the 30-day window has not elapsed.
            continue

        # Build each feature row at a clinically meaningful point in time:
        # - positives: first observed deterioration/death in the 30-day window
        # - negatives: end of 30-day window
        snapshot_date = positive_event_dates[0] if positive else horizon_end
        rows.append(patient_to_feature_dict(patient, now_date=snapshot_date))
        labels.append(1 if positive else 0)

    return rows, labels


def train_and_save(
    min_rows: int = 25,
    min_positives: int = 5,
    *,
    allow_low_positives: bool = False,
) -> TrainingResult:
    from .fit_pipeline import fit_and_save_pipeline

    rows, labels = _build_training_rows()
    positives = int(sum(labels))

    if len(rows) < min_rows:
        raise RuntimeError(
            f"Not enough patients to train: rows={len(rows)}, required>={min_rows}."
        )
    if positives < 1:
        raise RuntimeError(
            "Need at least one positive label from real outcomes."
        )
    if positives < min_positives and not allow_low_positives:
        raise RuntimeError(
            f"Not enough positive labels from real outcomes: positives={positives}, "
            f"required>={min_positives}. Add outcome events or lower --min-positives."
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
        metrics=result.metrics,
    )
