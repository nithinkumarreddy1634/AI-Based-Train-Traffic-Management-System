"""
Reproducible data preprocessing pipeline for train delay prediction.
"""

from pathlib import Path
from typing import List, Optional
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

from ml.config import PREPROCESSOR_PATH
from ml.features import NUMERICAL_FEATURES, CATEGORICAL_FEATURES


def build_preprocessing_pipeline() -> ColumnTransformer:
    """
    Constructs a reproducible scikit-learn ColumnTransformer:
    - Numerical features: Median imputation + StandardScaler
    - Categorical features: Most-frequent imputation + OneHotEncoder
    """
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERICAL_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )

    return preprocessor


def fit_and_save_preprocessor(
    X: pd.DataFrame,
    save_path: Optional[Path] = None
) -> ColumnTransformer:
    """Fits the preprocessing pipeline on training features and serializes to disk."""
    preprocessor = build_preprocessing_pipeline()
    preprocessor.fit(X)

    out_file = save_path or PREPROCESSOR_PATH
    out_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, out_file)
    print(f"[*] Preprocessing pipeline saved to {out_file}")

    return preprocessor


def load_preprocessor(load_path: Optional[Path] = None) -> ColumnTransformer:
    """Loads the fitted preprocessor from disk."""
    path = load_path or PREPROCESSOR_PATH
    if not path.exists():
        raise FileNotFoundError(f"Preprocessing pipeline not found at {path}")
    return joblib.load(path)


def get_feature_names(preprocessor: ColumnTransformer) -> List[str]:
    """Extracts output feature names after transformation (useful for feature importances)."""
    try:
        return list(preprocessor.get_feature_names_out())
    except Exception:
        # Fallback names
        names = list(NUMERICAL_FEATURES)
        try:
            cat_encoder = preprocessor.named_transformers_["cat"].named_steps["onehot"]
            cat_names = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES)
            names.extend(list(cat_names))
        except Exception:
            pass
        return names

