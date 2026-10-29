import os
import pathlib
import logging
from typing import Tuple, Dict, Any, List
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)
_MODULE_DIR = pathlib.Path(__file__).resolve().parent
MODEL_DIR = str(_MODULE_DIR / "saved_models")
os.makedirs(MODEL_DIR, exist_ok=True)


def build_features(df: pd.DataFrame, freq: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    Build time-series features (time calendar features, lags, rolling windows, growth rate).
    Dynamically adjusts lags and windows based on the dataset size to prevent empty datasets.
    """
    df_feat = df.copy()
    n_samples = len(df_feat)

    # 1. Calendar/Calendar Time Features
    df_feat['month'] = df_feat['ds'].dt.month
    df_feat['quarter'] = df_feat['ds'].dt.quarter
    df_feat['year'] = df_feat['ds'].dt.year
    df_feat['dayofweek'] = df_feat['ds'].dt.dayofweek
    df_feat['dayofyear'] = df_feat['ds'].dt.dayofyear

    calendar_features = ['month', 'quarter', 'year', 'dayofweek', 'dayofyear']
    lag_features = []
    rolling_features = []

    # 2. Lag and Rolling Window Features (Heuristics based on Frequency and size)
    if 'D' in freq or 'H' in freq:
        # Daily or sub-daily frequency
        # Adjust maximum lag to avoid empty dataframes
        lags = [1, 2]
        if n_samples > 10:
            lags.append(7)
        if n_samples > 40:
            lags.append(30)

        for lag in lags:
            col_name = f'lag_{lag}'
            df_feat[col_name] = df_feat['y'].shift(lag)
            lag_features.append(col_name)

        # Rolling average windows
        windows = [3]
        if n_samples > 12:
            windows.append(7)
        if n_samples > 45:
            windows.append(30)

        for window in windows:
            mean_col = f'rolling_mean_{window}'
            std_col = f'rolling_std_{window}'
            df_feat[mean_col] = df_feat['y'].shift(1).rolling(window=window).mean()
            df_feat[std_col] = df_feat['y'].shift(1).rolling(window=window).std()
            rolling_features.extend([mean_col, std_col])
    else:
        # Weekly, Monthly, or coarser frequency
        lags = [1, 2]
        if n_samples > 6:
            lags.append(3)
        if n_samples > 24:
            # Only use seasonal monthly lag if we have more than 2 years of history
            lags.append(12)

        for lag in lags:
            col_name = f'lag_{lag}'
            df_feat[col_name] = df_feat['y'].shift(lag)
            lag_features.append(col_name)

        # Rolling average windows
        windows = [2]
        if n_samples > 6:
            windows.append(3)
        if n_samples > 12:
            windows.append(6)

        for window in windows:
            mean_col = f'rolling_mean_{window}'
            std_col = f'rolling_std_{window}'
            df_feat[mean_col] = df_feat['y'].shift(1).rolling(window=window).mean()
            df_feat[std_col] = df_feat['y'].shift(1).rolling(window=window).std()
            rolling_features.extend([mean_col, std_col])

    # 3. Period-over-period growth rate
    df_feat['growth_rate'] = df_feat['y'].shift(1).pct_change(periods=1).replace([np.inf, -np.inf], 0).fillna(0)

    feature_cols = calendar_features + lag_features + rolling_features + ['growth_rate']
    return df_feat, feature_cols


def train_and_select_best_model(
    df: pd.DataFrame, 
    freq: str, 
    model_name_prefix: str = "salespulse_forecast"
) -> Tuple[Any, Dict[str, Any], List[str]]:
    """
    Builds features, splits dataset temporally, trains multiple models,
    evaluates on MAE/RMSE/R2, selects the best model, and saves it.
    
    Returns:
        Tuple[best_fitted_model, evaluation_metrics, list_of_features]
    """
    # 1. Feature Engineering
    df_feat, feature_cols = build_features(df, freq)

    # Clean NaNs introduced by shift/rolling
    df_clean = df_feat.dropna(subset=feature_cols).reset_index(drop=True)

    if len(df_clean) < 4:
        # Fallback to simple time_idx trend model if complex features are unviable
        logger.warning("Dataset too small for time-series features. Falling back to linear trend only.")
        df_feat = df.copy()
        df_feat['time_idx'] = np.arange(len(df_feat))
        X = df_feat[['time_idx']].values
        y = df_feat['y'].values
        
        lr = LinearRegression()
        lr.fit(X, y)
        metrics = {
            "best_model": "Linear Regression (Simple Trend)",
            "val_mae": 0.0,
            "val_rmse": 0.0,
            "val_r2": 1.0,
            "all_metrics": {},
            "fallback": True
        }
        model_payload = {
            "model": lr,
            "features": ['time_idx'],
            "freq": freq,
            "metrics": metrics,
            "fallback": True
        }
        joblib.dump(model_payload, os.path.join(MODEL_DIR, f"{model_name_prefix}.joblib"))
        return lr, metrics, ['time_idx']

    X = df_clean[feature_cols].values
    y = df_clean['y'].values

    # 2. Chronological/Time-Series Train-Test Split (e.g. 80-20 split)
    split_idx = int(len(X) * 0.8)
    if len(X) - split_idx < 1:
        split_idx = len(X) - 1

    X_train, y_train = X[:split_idx], y[:split_idx]
    X_val, y_val = X[split_idx:], y[split_idx:]

    # 3. Train models
    # Model A: Linear Regression
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    lr_preds = lr.predict(X_val)

    # Model B: Random Forest
    rf = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_val)

    # 4. Evaluation helper
    def calculate_metrics(y_true, y_pred) -> Dict[str, float]:
        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred)) if len(y_true) > 1 else 0.0
        return {"mae": mae, "rmse": rmse, "r2": r2}

    lr_metrics = calculate_metrics(y_val, lr_preds)
    rf_metrics = calculate_metrics(y_val, rf_preds)

    # 5. Selection (prefer lower MAE)
    all_models = {
        "Linear Regression": (lr, lr_metrics),
        "Random Forest": (rf, rf_metrics)
    }

    best_model_name = "Linear Regression"
    if rf_metrics["mae"] < lr_metrics["mae"]:
        best_model_name = "Random Forest"

    best_model, best_metrics = all_models[best_model_name]

    summary_metrics = {
        "best_model": best_model_name,
        "val_mae": round(best_metrics["mae"], 2),
        "val_rmse": round(best_metrics["rmse"], 2),
        "val_r2": round(best_metrics["r2"], 4),
        "all_metrics": {
            "linear_regression": lr_metrics,
            "random_forest": rf_metrics
        },
        "fallback": False
    }

    # 6. Re-fit on full data for optimal forecasting
    best_model.fit(X, y)

    # 7. Save model package
    model_payload = {
        "model": best_model,
        "features": feature_cols,
        "freq": freq,
        "metrics": summary_metrics,
        "fallback": False
    }
    path = os.path.join(MODEL_DIR, f"{model_name_prefix}.joblib")
    joblib.dump(model_payload, path)

    logger.info(f"Trained and saved best model package ({best_model_name}) with val MAE: {summary_metrics['val_mae']}")
    return best_model, summary_metrics, feature_cols


def load_model_package(model_name_prefix: str = "salespulse_forecast") -> Dict[str, Any]:
    """Loads the model package dictionary containing estimator, features and metrics."""
    path = os.path.join(MODEL_DIR, f"{model_name_prefix}.joblib")
    if not os.path.exists(path):
        return None
    return joblib.load(path)
