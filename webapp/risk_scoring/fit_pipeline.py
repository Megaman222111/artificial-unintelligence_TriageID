"""
Pipeline fit-and-save logic with no Django dependency.
Used by train.py (DB data) and by external-dataset training scripts.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from .features import (
    FEATURE_CATEGORICAL_COLUMNS,
    FEATURE_NUMERIC_COLUMNS,
    FEATURE_TEXT_COLUMN,
)


@dataclass
class TrainingResult:
    model_version: str
    rows: int
    positives: int
    calibrator: str


def fit_and_save_pipeline(
    X,
    labels: List[int],
    model_dir: Path,
    model_version: str | None = None,
) -> TrainingResult:
    """
    Build pipeline, fit on X/labels, optionally calibrate, save joblib to model_dir.
    X must be a DataFrame with columns matching FEATURE_* in features.py.
    """
    import time

    try:
        import joblib
        import numpy as np
        import pandas as pd
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.compose import ColumnTransformer
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler
    except ImportError as exc:
        raise RuntimeError("scikit-learn, joblib, and pandas are required.") from exc

    if not isinstance(X, pd.DataFrame):
        raise TypeError("X must be a pandas DataFrame")
    n = len(X)
    positives = int(sum(labels))
    if n < 3:
        raise ValueError(f"Need at least 3 rows, got {n}")
    if positives < 1:
        raise ValueError("Need at least one positive label")

    preprocess = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(with_mean=False), FEATURE_NUMERIC_COLUMNS),
            ("cat", OneHotEncoder(handle_unknown="ignore"), FEATURE_CATEGORICAL_COLUMNS),
            (
                "txt",
                TfidfVectorizer(max_features=300, ngram_range=(1, 2)),
                FEATURE_TEXT_COLUMN,
            ),
        ]
    )
    base_model = LogisticRegression(class_weight="balanced", penalty="l2", max_iter=1000)
    pipeline = Pipeline(
        steps=[
            ("preprocess", preprocess),
            ("model", base_model),
        ]
    )
    pipeline.fit(X, labels)

    calibrated = None
    calibrator_method = "none"
    if positives >= 3:
        calibrator_method = "sigmoid" if positives < 30 else "isotonic"
        cv = min(3, positives)
        if cv >= 2:
            calibrated = CalibratedClassifierCV(
                estimator=pipeline, method=calibrator_method, cv=cv
            )
            calibrated.fit(X, labels)

    if not model_version:
        model_version = f"risk-v1-{int(time.time())}"
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    path = model_dir / f"risk_model_{model_version}.joblib"

    top_feature_names: List[str] = []
    top_feature_weights: List[float] = []
    try:
        final = pipeline.named_steps["model"]
        coefs = final.coef_[0]
        order = np.argsort(np.abs(coefs))[::-1][:12]
        names = pipeline.named_steps["preprocess"].get_feature_names_out()
        top_feature_names = [str(names[i]) for i in order]
        top_feature_weights = [float(coefs[i]) for i in order]
    except Exception:
        pass

    payload = {
        "model_version": model_version,
        "pipeline": pipeline,
        "calibrator": calibrated,
        "top_feature_names": top_feature_names,
        "top_feature_weights": top_feature_weights,
    }
    joblib.dump(payload, path)
    return TrainingResult(
        model_version=model_version,
        rows=n,
        positives=positives,
        calibrator=calibrator_method,
    )
