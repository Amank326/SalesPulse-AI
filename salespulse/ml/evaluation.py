from sklearn.metrics import mean_squared_error, r2_score

def evaluate_regression(y_true, y_pred):
    return {
        'mse': float(mean_squared_error(y_true, y_pred)),
        'r2': float(r2_score(y_true, y_pred))
    }
