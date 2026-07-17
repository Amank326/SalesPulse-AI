import os
from typing import Dict, Any

try:
    import pandas as pd
except Exception:
    pd = None
import numpy as np
import matplotlib.pyplot as plt

from salespulse.ml.preprocessing import clean_dataframe, select_numeric_columns
from salespulse.ml.training import train_linear_model, load_model


def forecast_df(df: pd.DataFrame, target_col: str = None, periods: int = 7) -> Dict[str, Any]:
    df_clean = clean_dataframe(df)
    if target_col is None:
        numeric_cols = select_numeric_columns(df_clean)
        if not numeric_cols:
            raise ValueError('No numeric columns found for forecasting')
        target_col = numeric_cols[0]

    # build numeric series
    if pd is not None and isinstance(df_clean, pd.DataFrame):
        series = df_clean[target_col].dropna().astype(float).reset_index(drop=True)
    else:
        # list-of-dicts fallback
        series = [float(r.get(target_col, 0) or 0) for r in df_clean]
    X = np.arange(len(series)).reshape(-1, 1)
    y = np.array(series)

    # try to load existing model
    model = load_model('linear_default')
    metrics = None
    if model is None:
        model, metrics = train_linear_model(X, y, model_name='linear_default')
    preds = model.predict(np.arange(len(series), len(series) + periods).reshape(-1, 1))

    # create and persist plot
    plt.figure(figsize=(6, 3))
    plt.plot(np.arange(len(series)), y, label='history')
    plt.plot(np.arange(len(series), len(series) + periods), preds, label='forecast')
    plt.legend()
    os.makedirs('ml', exist_ok=True)
    out_path = os.path.join('ml', 'forecast_output.png')
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

    result = {
        'target_col': target_col,
        'history_len': int(len(series)),
        'forecast_periods': int(periods),
        'predictions': [float(x) for x in preds],
        'plot': out_path
    }
    if metrics:
        result.update(metrics)
    return result
