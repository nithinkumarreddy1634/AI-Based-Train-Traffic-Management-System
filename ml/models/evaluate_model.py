"""
Model evaluation utilities: MAE, RMSE, R-squared, and comparison reporting.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Computes MAE, RMSE, and R^2 for a regression model."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(root_mean_squared_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))

    return {
        "MAE": round(mae, 3),
        "RMSE": round(rmse, 3),
        "R2": round(r2, 4),
    }


def format_evaluation_table(results: Dict[str, Dict[str, float]]) -> str:
    """Formats model evaluation metrics as a clean text table."""
    headers = ["Model", "MAE (min)", "RMSE (min)", "R² Score"]
    rows = []
    for model_name, metrics in results.items():
        rows.append(
            f"{model_name:<28} {metrics['MAE']:<10.3f} {metrics['RMSE']:<12.3f} {metrics['R2']:<8.4f}"
        )

    header_line = f"{headers[0]:<28} {headers[1]:<10} {headers[2]:<12} {headers[3]:<8}"
    separator = "-" * len(header_line)
    return "\n" + separator + "\n" + header_line + "\n" + separator + "\n" + "\n".join(rows) + "\n" + separator


def select_best_model(results: Dict[str, Dict[str, Any]]) -> str:
    """
    Selects the best model based on lowest test RMSE,
    breaking ties with higher R^2 score.
    """
    best_name = None
    best_rmse = float("inf")
    best_r2 = -float("inf")

    for name, data in results.items():
        rmse = data["metrics"]["RMSE"]
        r2 = data["metrics"]["R2"]

        if rmse < best_rmse or (rmse == best_rmse and r2 > best_r2):
            best_rmse = rmse
            best_r2 = r2
            best_name = name

    return best_name

