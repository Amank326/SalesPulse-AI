import os
from typing import Tuple, Any
import numpy as np
import joblib

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

MODEL_DIR = os.path.join('ml', 'saved_models')
os.makedirs(MODEL_DIR, exist_ok=True)

def train_linear_model(X, y, model_name: str = 'linear_default') -> Tuple[Any, dict]:
    model = LinearRegression()
    model.fit(X, y)
    preds = model.predict(X)
    metrics = {
        'mse': float(mean_squared_error(y, preds)),
        'r2': float(r2_score(y, preds))
    }
    path = os.path.join(MODEL_DIR, f'{model_name}.joblib')
    joblib.dump({'model': model}, path)
    return model, {**metrics, 'path': path}

def load_model(model_name: str = 'linear_default'):
    path = os.path.join(MODEL_DIR, f'{model_name}.joblib')
    if not os.path.exists(path):
        return None
    data = joblib.load(path)
    return data.get('model')
