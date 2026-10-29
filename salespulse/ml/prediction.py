import os
import pathlib
import logging
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ml.preprocessing import clean_dataframe
from ml.training import train_and_select_best_model, build_features, load_model_package

logger = logging.getLogger(__name__)
_MODULE_DIR = pathlib.Path(__file__).resolve().parent


def recursive_forecast(
    model: Any,
    history_df: pd.DataFrame,
    features: List[str],
    freq: str,
    steps: int
) -> Tuple[List[pd.Timestamp], List[float]]:
    """
    Performs recursive multi-step forecasting.
    Re-calculates lag and rolling features iteratively using predicted values.
    """
    df_forecast = history_df.copy()
    
    # Identify date column and target column
    # Clean dataframe always returns 'ds' and 'y'
    last_date = df_forecast['ds'].iloc[-1]
    
    predictions = []
    future_dates = []

    # Generate dates
    current_date = last_date
    for _ in range(steps):
        # Determine next date
        if freq == 'MS':
            # Monthly start
            current_date = current_date + pd.DateOffset(months=1)
        elif freq == 'W':
            # Weekly
            current_date = current_date + pd.DateOffset(weeks=1)
        else:
            # Daily or default
            current_date = current_date + pd.DateOffset(days=1)
        future_dates.append(current_date)

    # Recursive forecasting loop
    for i in range(steps):
        next_date = future_dates[i]
        
        # 1. Create a dummy row for the next date
        new_row = pd.DataFrame({'ds': [next_date], 'y': [np.nan]})
        df_forecast = pd.concat([df_forecast, new_row], ignore_index=True)
        
        # 2. Build features for the entire dataframe (including our dummy row)
        df_temp, built_features = build_features(df_forecast, freq)
        
        # 3. Pull out the feature vector for the dummy row (last row)
        X_next = df_temp[features].iloc[-1].values.reshape(1, -1)
        
        # 4. Predict next target value
        y_pred = float(model.predict(X_next)[0])
        # Ensure predicted revenue is never negative
        y_pred = max(0.0, y_pred)
        
        # 5. Update the dummy row in df_forecast with the predicted value
        df_forecast.loc[df_forecast.index[-1], 'y'] = y_pred
        
        predictions.append(y_pred)

    return future_dates, predictions


def forecast_df(df: pd.DataFrame, target_col: str = None, periods: int = 30) -> Dict[str, Any]:
    """
    High-level API: Takes any raw DataFrame, validates/cleans it, trains the best ML model,
    performs recursive multi-step forecasting for the specified periods, and plots the results.
    """
    # 1. Automatic validation & cleaning
    df_clean, orig_date_col, orig_rev_col, freq = clean_dataframe(df)
    
    # 2. Train best model dynamically
    model, metrics, features = train_and_select_best_model(df_clean, freq)

    # If fallback simple trend model was used
    if metrics.get("fallback", False):
        n = len(df_clean)
        future_x = np.arange(n, n + periods).reshape(-1, 1)
        forecast_vals = model.predict(future_x).tolist()
        forecast_vals = [max(0.0, float(v)) for v in forecast_vals]
        
        # Generate dates
        last_date = df_clean['ds'].iloc[-1]
        future_dates = []
        current_date = last_date
        for _ in range(periods):
            if freq == 'MS':
                current_date = current_date + pd.DateOffset(months=1)
            elif freq == 'W':
                current_date = current_date + pd.DateOffset(weeks=1)
            else:
                current_date = current_date + pd.DateOffset(days=1)
            future_dates.append(current_date)
    else:
        # 3. Perform recursive forecast
        future_dates, forecast_vals = recursive_forecast(model, df_clean, features, freq, periods)

    # Format dates
    history_dates_str = df_clean['ds'].dt.strftime('%Y-%m-%d').tolist()
    future_dates_str = [d.strftime('%Y-%m-%d') for d in future_dates]
    history_values = df_clean['y'].tolist()

    # 4. Generate & Save actual vs forecast plot (Beautiful theme)
    plt.figure(figsize=(10, 4.5), facecolor='#080B14')
    ax = plt.axes()
    ax.set_facecolor('#0C1120')
    
    # Style borders
    ax.spines['bottom'].set_color((1.0, 1.0, 1.0, 0.1))
    ax.spines['left'].set_color((1.0, 1.0, 1.0, 0.1))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(colors='#8090B0')
    
    # Plot history
    plt.plot(df_clean['ds'], df_clean['y'], color='#00D9FF', linewidth=2.5, marker='o', markersize=4, label='Historical Sales')
    
    # Plot forecast
    plt.plot(future_dates, forecast_vals, color='#7B3FF2', linewidth=2, linestyle='--', marker='s', markersize=4, label='AI Forecast')
    
    # Split indicator line
    plt.axvline(x=df_clean['ds'].iloc[-1], color=(0.0, 0.85, 1.0, 0.4), linestyle=':', linewidth=1)
    
    # Fill shadows
    plt.fill_between(df_clean['ds'], df_clean['y'], alpha=0.08, color='#00D9FF')
    plt.fill_between(future_dates, forecast_vals, alpha=0.05, color='#7B3FF2')
    
    # Labels
    plt.title('Revenue Trend & AI Forecast', color='#fff', fontsize=12, fontweight='bold', pad=12)
    plt.xlabel('Date', color='#8090B0', fontsize=9)
    plt.ylabel('Revenue / Sales', color='#8090B0', fontsize=9)
    plt.legend(facecolor='#0C1120', edgecolor=(1.0, 1.0, 1.0, 0.1), labelcolor='#C9D1E0', fontsize=9)
    plt.grid(True, alpha=0.05, color='white')
    
    out_path = str(_MODULE_DIR / 'forecast_output.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, facecolor='#080B14')
    plt.close()

    result = {
        "success": True,
        "date_col": orig_date_col,
        "revenue_col": orig_rev_col,
        "freq": freq,
        "history": {
            "dates": history_dates_str,
            "values": [round(float(v), 2) for v in history_values]
        },
        "forecast": {
            "dates": future_dates_str,
            "values": [round(float(v), 2) for v in forecast_vals]
        },
        "metrics": metrics,
        "plot": "/ml/forecast_output.png"
    }
    return result
