# Machine Learning Train Delay Prediction System (Phase 6)

## Overview
This subsystem provides real-time predictive forecasting of train delays across the railway corridor.
It uses domain-grounded operating conditions (track speed, section utilization, queuing trains, dwell duration, remaining distance, priority) to project arrival delays before congestion compounds.

## Architecture
```text
ml/
├── data/
│   ├── generate_dataset.py   # Generates 6,500 domain-grounded synthetic samples
│   └── preprocessing.py      # ColumnTransformer with StandardScaler and OneHotEncoder
├── models/
│   ├── train_model.py        # Trains 4 candidate regressors, evaluates, and selects best
│   ├── evaluate_model.py     # MAE, RMSE, R² metrics calculation and reporting
│   └── predict.py            # Low-latency inference service with in-memory caching
├── saved_models/
│   ├── delay_prediction_model.pkl
│   ├── preprocessing_pipeline.pkl
│   └── model_metadata.json
├── features.py               # Feature schemas and valid categories
├── config.py                 # Filepaths and configuration constants
└── README.md
```

## Candidate Models Evaluated
1. **Linear Regression**: Baseline parametric model
2. **Random Forest Regressor**: Non-linear ensemble with bootstrap aggregation
3. **Gradient Boosting Regressor**: Sequential stage-wise loss minimization
4. **HistGradientBoostingRegressor**: Fast bin-based gradient boosting

## Retraining Command
```powershell
.venv\Scripts\python.exe -m ml.models.train_model
```

## Synthetic Data Disclaimer
The dataset used in this prototype is synthetically generated using deterministic railway physics, queuing models, and scheduling dynamics. It is intended for software research, demonstration, and architectural prototyping.
