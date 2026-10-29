import logging
from typing import Tuple, List, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def clean_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, str, str, str]:
    """
    Validates, cleans and automatically resamples the input sales dataset.
    Returns:
        Tuple[cleaned_df, date_col_name, revenue_col_name, detected_frequency]
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input data must be a pandas DataFrame")

    df_clean = df.copy()

    # 1. Automatic Date Column Detection
    date_col = None
    for col in df_clean.columns:
        col_str = str(col).lower()
        if "date" in col_str or "time" in col_str or "period" in col_str:
            try:
                df_clean[col] = pd.to_datetime(df_clean[col])
                date_col = col
                break
            except Exception:
                pass

    if date_col is None:
        # Fallback: find any column that can be successfully converted to datetime
        for col in df_clean.columns:
            try:
                parsed = pd.to_datetime(df_clean[col])
                # Ensure it's not all NaNs/nulls after conversion
                if parsed.notna().sum() > 0:
                    df_clean[col] = parsed
                    date_col = col
                    break
            except Exception:
                pass

    if date_col is None:
        raise ValueError("Could not auto-detect a valid date or datetime column in the dataset.")

    # 2. Automatic Target Column Detection (Sales / Revenue)
    rev_col = None
    # Priority 1: Keywords matching target columns
    for col in df_clean.columns:
        col_str = str(col).lower()
        if any(k in col_str for k in ["sales", "revenue", "bill", "amount", "price", "total_revenue"]):
            # Try to convert to float
            try:
                df_clean[col] = pd.to_numeric(df_clean[col].astype(str).str.replace(r'[^\d\.]', '', regex=True), errors='coerce')
                if df_clean[col].notna().sum() > 0:
                    rev_col = col
                    break
            except Exception:
                pass

    # Priority 2: Fallback to the first numeric column that is not the date
    if rev_col is None:
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != date_col]
        if numeric_cols:
            rev_col = numeric_cols[0]

    # Priority 3: Fallback to any non-date column that can be coerced to numeric
    if rev_col is None:
        for col in df_clean.columns:
            if col != date_col:
                try:
                    coerced = pd.to_numeric(df_clean[col].astype(str).str.replace(r'[^\d\.]', '', regex=True), errors='coerce')
                    if coerced.notna().sum() > 0:
                        df_clean[col] = coerced
                        rev_col = col
                        break
                except Exception:
                    pass

    if rev_col is None:
        raise ValueError("Could not auto-detect a valid numeric sales or revenue column in the dataset.")

    # Keep only date and target, plus optional metadata columns if wanted
    df_clean = df_clean[[date_col, rev_col]].copy()
    df_clean.rename(columns={date_col: 'ds', rev_col: 'y'}, inplace=True)

    # 3. Clean Missing Values & Duplicate Date Removal
    df_clean.dropna(subset=['ds'], inplace=True)
    df_clean = df_clean.sort_values('ds').reset_index(drop=True)
    
    # Remove duplicate dates by aggregating target values (summing sales on the same date)
    df_clean = df_clean.groupby('ds', as_index=False)['y'].sum()

    # 4. Auto-detect Frequency & Resample to fill gaps
    if len(df_clean) < 3:
        # Minimum data length to infer frequency
        freq = "D"
        df_clean.set_index('ds', inplace=True)
        df_clean = df_clean.resample(freq).asfreq()
    else:
        # Infer frequency
        inferred = pd.infer_freq(df_clean['ds'])
        if inferred is None:
            # Fallback heuristic based on median time delta
            deltas = df_clean['ds'].diff().dropna()
            median_days = deltas.dt.days.median()
            if median_days >= 28:
                freq = "MS"  # Monthly start
            elif median_days >= 6:
                freq = "W"   # Weekly
            else:
                freq = "D"   # Daily
        else:
            freq = inferred

        df_clean.set_index('ds', inplace=True)
        df_clean = df_clean.resample(freq).asfreq()

    # 5. Handle missing values introduced by resampling or original NaNs using linear interpolation
    df_clean['y'] = df_clean['y'].interpolate(method='linear')
    # If there are still NaNs at the start/end, bfill/ffill them
    df_clean['y'] = df_clean['y'].bfill().ffill()

    # Reset index back so 'ds' is a regular column
    df_clean = df_clean.reset_index()

    logger.info(f"Cleaned dataset: detected date={date_col}, revenue={rev_col}, frequency={freq}. Row count: {len(df_clean)}")
    return df_clean, str(date_col), str(rev_col), freq
