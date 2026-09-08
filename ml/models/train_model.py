"""
Model Training Script for Train Delay Prediction.
Trains, evaluates, and compares 4 candidate regression models, selects the best model,
calculates feature importances, and serializes artifacts.
"""

import json
import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
)
from sklearn.inspection import permutation_importance

from ml.config import (
    DATASET_PATH,
    MODEL_PATH,
    PREPROCESSOR_PATH,
    METADATA_PATH,
    RANDOM_STATE,
    TEST_SPLIT_RATIO,
    SYNTHETIC_DATASET_SIZE,
)
from ml.features import ALL_FEATURES, TARGET, NUMERICAL_FEATURES, CATEGORICAL_FEATURES
from ml.data.generate_dataset import generate_synthetic_dataset
from ml.data.preprocessing import (
    build_preprocessing_pipeline,
    fit_and_save_preprocessor,
    get_feature_names,
)
from ml.models.evaluate_model import (
    evaluate_predictions,
    format_evaluation_table,
    select_best_model,
)


def get_candidate_models() -> Dict[str, Any]:
    """Instantiates candidate regression models with reproducible hyperparameter seeds."""
    return {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(
            n_estimators=100,
            max_depth=14,
            min_samples_split=4,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=120,
            max_depth=5,
            learning_rate=0.08,
            random_state=RANDOM_STATE,
        ),
        "HistGradientBoosting": HistGradientBoostingRegressor(
            max_iter=120,
            max_depth=6,
            learning_rate=0.08,
            random_state=RANDOM_STATE,
        ),
    }


def extract_feature_importances(
    model: Any,
    model_name: str,
    feature_names: List[str],
    X_test_trans: np.ndarray,
    y_test: np.ndarray
) -> List[Dict[str, Any]]:
    """
    Computes top feature importances using native tree attribute or permutation importance.
    Returns ranked list of { "feature": str, "importance": float, "percentage": float }.
    """
    importances = None
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_)
    else:
        # Model-agnostic permutation importance
        perm = permutation_importance(
            model, X_test_trans, y_test, n_repeats=5, random_state=RANDOM_STATE, n_jobs=-1
        )
        importances = perm.importances_mean

    total = np.sum(importances) if np.sum(importances) > 0 else 1.0
    ranked = []
    for name, imp in zip(feature_names, importances):
        pct = round(float((imp / total) * 100.0), 2)
        # Clean up feature name formatting
        clean_name = name.replace("num__", "").replace("cat__", "").replace("_", " ").title()
        ranked.append({
            "feature": clean_name,
            "raw_name": name,
            "importance": round(float(imp), 4),
            "percentage": pct,
        })

    # Sort descending
    ranked.sort(key=lambda x: x["importance"], reverse=True)
    return ranked


def train_and_evaluate_all() -> Tuple[Any, Dict[str, Any]]:
    """
    Main pipeline:
    1. Ensure dataset exists.
    2. Train/test split.
    3. Fit & save preprocessing pipeline.
    4. Train all candidate models.
    5. Evaluate & select best model.
    6. Extract feature importance.
    7. Save best model and metadata.
    """
    print("[*] Starting Machine Learning Delay Prediction training pipeline...")

    # 1. Dataset loading / generation
    if not DATASET_PATH.exists():
        print(f"[*] Dataset not found at {DATASET_PATH}. Generating synthetic dataset...")
        df = generate_synthetic_dataset(num_samples=SYNTHETIC_DATASET_SIZE)
    else:
        print(f"[*] Loading dataset from {DATASET_PATH}...")
        df = pd.read_csv(DATASET_PATH)

    print(f"[*] Dataset loaded successfully: {len(df)} records, {len(df.columns)} columns.")

    # 2. Features and Target
    X = df[ALL_FEATURES]
    y = df[TARGET].values

    # Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SPLIT_RATIO, random_state=RANDOM_STATE
    )
    print(f"[*] Data split: {len(X_train)} train samples, {len(X_test)} test samples.")

    # 3. Fit preprocessing pipeline
    print("[*] Fitting preprocessing pipeline on training features...")
    preprocessor = fit_and_save_preprocessor(X_train, PREPROCESSOR_PATH)
    X_train_trans = preprocessor.transform(X_train)
    X_test_trans = preprocessor.transform(X_test)
    feature_names = get_feature_names(preprocessor)

    # 4. Train candidates
    candidates = get_candidate_models()
    model_results: Dict[str, Dict[str, Any]] = {}

    for name, model in candidates.items():
        print(f"[*] Training candidate model: {name}...")
        model.fit(X_train_trans, y_train)
        y_pred = model.predict(X_test_trans)
        metrics = evaluate_predictions(y_test, y_pred)
        model_results[name] = {
            "model": model,
            "metrics": metrics,
        }
        print(f"    -> MAE: {metrics['MAE']:.3f} min | RMSE: {metrics['RMSE']:.3f} min | R²: {metrics['R2']:.4f}")

    # 5. Display comparison table
    summary_metrics = {name: data["metrics"] for name, data in model_results.items()}
    table_str = format_evaluation_table(summary_metrics)
    print("\n" + "=" * 62)
    print("      MODEL BENCHMARK COMPARISON REPORT (Phase 6)")
    print("=" * 62 + table_str)

    # 6. Select best model
    best_name = select_best_model(model_results)
    best_data = model_results[best_name]
    best_model = best_data["model"]
    best_metrics = best_data["metrics"]

    print(f"\n[+] Selected Best Model: '{best_name}' (Lowest Test RMSE: {best_metrics['RMSE']} min, R²: {best_metrics['R2']})")

    # 7. Feature importance
    ranked_features = extract_feature_importances(
        best_model, best_name, feature_names, X_test_trans, y_test
    )

    print("\n[+] Top 6 Influential Features for Delay Prediction:")
    for idx, f in enumerate(ranked_features[:6], 1):
        print(f"    {idx}. {f['feature']:<30} {f['percentage']}% importance")

    # 8. Save best model and metadata
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    print(f"\n[*] Best model serialized to: {MODEL_PATH}")

    metadata = {
        "model_name": best_name,
        "training_date": datetime.datetime.now().isoformat(),
        "dataset_size": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "features": ALL_FEATURES,
        "numerical_features": NUMERICAL_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "metrics": best_metrics,
        "all_model_comparison": summary_metrics,
        "feature_importances": ranked_features[:12],
        "version": "1.0.0",
        "random_state": RANDOM_STATE,
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[*] Model metadata saved to: {METADATA_PATH}")

    return best_model, metadata


if __name__ == "__main__":
    train_and_evaluate_all()

