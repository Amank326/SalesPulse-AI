try:
    import pandas as pd
except Exception:
    pd = None

from typing import Tuple, List, Any


def clean_dataframe(df: Any):
    """Accepts a pandas.DataFrame or list-of-dicts. Returns a pandas.DataFrame if pandas available,
    otherwise returns a list-of-dicts cleaned."""
    if pd is not None and isinstance(df, pd.DataFrame):
        out = df.copy()
        out.dropna(axis=1, how='all', inplace=True)
        for c in out.select_dtypes(include=['object']).columns:
            out[c] = out[c].astype(str).str.strip()
        out.reset_index(drop=True, inplace=True)
        return out

    # handle list-of-dicts
    if isinstance(df, list):
        cleaned = []
        for row in df:
            newrow = {}
            for k, v in row.items():
                if isinstance(v, str):
                    newrow[k] = v.strip()
                else:
                    newrow[k] = v
            cleaned.append(newrow)
        return cleaned

    raise ValueError('Unsupported dataframe type')


def select_numeric_columns(df: Any) -> List[str]:
    if pd is not None and isinstance(df, pd.DataFrame):
        return df.select_dtypes(include=['number']).columns.tolist()
    if isinstance(df, list) and df:
        # infer numeric columns from first row
        first = df[0]
        return [k for k, v in first.items() if isinstance(v, (int, float))]
    return []
