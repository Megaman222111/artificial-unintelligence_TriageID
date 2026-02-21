"""
Pipeline fit-and-save logic with no Django dependency.
Used by train.py (DB data) and by external-dataset training scripts.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .features import (
    FEATURE_CATEGORICAL_COLUMNS,
    FEATURE_NUMERIC_COLUMNS,
    FEATURE_COLUMN_ORDER,
)


@dataclass
class TrainingResult:
    model_version: str
    rows: int
    positives: int
    calibrator: str
    metrics: Dict[str, float]


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
        import sklearn
        from sklearn.compose import ColumnTransformer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
        from sklearn.model_selection import train_test_split
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

    if not all(col in X.columns for col in FEATURE_COLUMN_ORDER):
        missing = [col for col in FEATURE_COLUMN_ORDER if col not in X.columns]
        raise ValueError(f"Missing required feature columns: {missing}")

    def _build_pipeline():
        preprocess = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), FEATURE_NUMERIC_COLUMNS),
                ("cat", OneHotEncoder(handle_unknown="ignore"), FEATURE_CATEGORICAL_COLUMNS),
            ],
            remainder="drop",
        )
        return Pipeline(
            steps=[
                ("preprocess", preprocess),
                ("model", LogisticRegression(max_iter=1000)),
            ]
        )

    pipeline = _build_pipeline()
    pipeline.fit(X, labels)

    calibrated = None
    calibrator_method = "none"

    metrics: Dict[str, float] = {}
    if positives >= 10 and (n - positives) >= 10 and n >= 200:
        X_train, X_valid, y_train, y_valid = train_test_split(
            X,
            labels,
            test_size=0.2,
            random_state=42,
            stratify=labels,
        )
        eval_pipeline = _build_pipeline()
        eval_pipeline.fit(X_train, y_train)
        valid_prob = eval_pipeline.predict_proba(X_valid)[:, 1]
        metrics["roc_auc"] = float(roc_auc_score(y_valid, valid_prob))
        metrics["avg_precision"] = float(average_precision_score(y_valid, valid_prob))
        metrics["brier"] = float(brier_score_loss(y_valid, valid_prob))

    base_rate = float(positives / n)
    medium_threshold = max(0.08, min(0.20, base_rate))
    high_threshold = max(medium_threshold + 0.05, min(0.35, base_rate * 2.0))

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
        "feature_columns": FEATURE_COLUMN_ORDER,
        "band_thresholds": {
            "medium": round(float(medium_threshold), 4),
            "high": round(float(high_threshold), 4),
        },
        "training_metrics": metrics,
        "base_rate": round(base_rate, 4),
        "sklearn_version": sklearn.__version__,
    }
    joblib.dump(payload, path)
    return TrainingResult(
        model_version=model_version,
        rows=n,
        positives=positives,
        calibrator=calibrator_method,
        metrics=metrics,
    )
