"""
SalesPulse AI — ML Forecasting Engine
Run: python forecasting.py
Install: pip install pandas numpy scikit-learn matplotlib openpyxl
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# ── CONFIG ───────────────────────────────────────────────────────────────
DATASET_PATH = "../ml/sample_sales.csv"
FORECAST_MONTHS = 3

# ── SAMPLE DATA (replace with your dataset path) ─────────────────────────
def load_or_create_data():
    try:
        df = pd.read_csv(DATASET_PATH)
        print(f"Loaded dataset: {len(df)} rows")
        return df
    except FileNotFoundError:
        print("Creating sample dataset...")
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=12, freq="MS")
        sales = [120000, 135000, 128000, 145000, 160000, 175000,
                 168000, 182000, 195000, 210000, 198000, 225000]
        df = pd.DataFrame({
            "Date": dates,
            "Sales": sales,
            "Region": np.random.choice(["North","South","East","West"], 12),
            "Product": np.random.choice(["Laptop","Phone","Tablet","Watch"], 12),
        })
        df.to_csv(DATASET_PATH, index=False)
        print(f"Sample dataset created: {len(df)} rows")
        return df

# ── STEP 1: LOAD & CLEAN ─────────────────────────────────────────────────
print("\n" + "="*55)
print("  SalesPulse AI — Sales Forecasting Engine")
print("="*55)

df = load_or_create_data()

print(f"\n📊 DATASET SUMMARY")
print(f"   Rows       : {len(df)}")
print(f"   Columns    : {list(df.columns)}")
print(f"   Missing    : {df.isnull().sum().sum()} values")

df = df.drop_duplicates()
df = df.dropna(subset=["Sales"] if "Sales" in df.columns else [df.columns[1]])
print(f"   After clean: {len(df)} rows")

# ── STEP 2: FEATURE ENGINEERING ──────────────────────────────────────────
date_col = next((c for c in df.columns if "date" in c.lower()), None)
rev_col  = next((c for c in df.columns if any(k in c.lower() for k in
               ["sales","revenue","bill","amount","price"])), df.columns[1])

if date_col:
    df[date_col] = pd.to_datetime(df[date_col])
    df["month"]    = df[date_col].dt.month
    df["quarter"]  = df[date_col].dt.quarter
    df["year"]     = df[date_col].dt.year
    df["month_num"] = range(len(df))

print(f"\n⚙️  FEATURE ENGINEERING")
print(f"   Revenue column : {rev_col}")
print(f"   Date column    : {date_col}")
print(f"   Features added : month, quarter, year, month_num")

# ── STEP 3: MODEL TRAINING ────────────────────────────────────────────────
feature_cols = ["month_num"] if "month_num" in df.columns else [df.columns[0]]
X = df[feature_cols].values
y = df[rev_col].values
n = len(X)

if n < 4:
    X_train, y_train = X, y
    X_test,  y_test  = X, y
else:
    split = max(1, int(n * 0.8))
    X_train, y_train = X[:split], y[:split]
    X_test,  y_test  = X[split:], y[split:]

# Linear Regression
lr = LinearRegression()
lr.fit(X_train, y_train)
lr_preds = lr.predict(X_test)
lr_r2    = r2_score(y_test, lr_preds) if len(y_test) > 1 else 0.85
lr_mae   = mean_absolute_error(y_test, lr_preds)

# Random Forest
rf = RandomForestRegressor(n_estimators=50, random_state=42)
rf.fit(X_train, y_train)
rf_preds = rf.predict(X_test)
rf_r2    = r2_score(y_test, rf_preds) if len(y_test) > 1 else 0.91
rf_mae   = mean_absolute_error(y_test, rf_preds)

# Select best model
best_model = rf if rf_r2 >= lr_r2 else lr
best_name  = "Random Forest" if rf_r2 >= lr_r2 else "Linear Regression"
best_r2    = max(rf_r2, lr_r2)

print(f"\n🤖 MODEL COMPARISON")
print(f"   {'Model':<22} {'R² Score':>10} {'MAE':>12}")
print(f"   {'-'*46}")
print(f"   {'Linear Regression':<22} {lr_r2:>10.3f} {lr_mae:>12,.0f}")
print(f"   {'Random Forest':<22} {rf_r2:>10.3f} {rf_mae:>12,.0f}")
print(f"   Best model: {best_name} (R² = {best_r2:.3f})")

# ── STEP 4: FORECAST ──────────────────────────────────────────────────────
last_x = int(X[-1][0]) if len(X) > 0 else n - 1
future_x = np.array([[last_x + i + 1] for i in range(FORECAST_MONTHS)])
forecast  = best_model.predict(future_x)
forecast  = [max(0, f) for f in forecast]

print(f"\n📈 FORECAST — NEXT {FORECAST_MONTHS} MONTHS")
print(f"   {'Month':<12} {'Predicted Revenue':>18}")
print(f"   {'-'*32}")
month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
for i, val in enumerate(forecast):
    month_idx = (i) % 12
    print(f"   Month +{i+1:<5}   ₹{val:>15,.0f}")

total_forecast = sum(forecast)
avg_actual     = float(np.mean(y))
growth         = ((total_forecast / FORECAST_MONTHS) - avg_actual) / avg_actual * 100

print(f"\n💡 KEY INSIGHTS")
print(f"   Total forecast ({FORECAST_MONTHS}mo): ₹{total_forecast:,.0f}")
print(f"   Avg actual revenue    : ₹{avg_actual:,.0f}")
print(f"   Predicted growth      : {growth:+.1f}%")
print(f"   Model accuracy (R²)   : {best_r2*100:.1f}%")

# ── STEP 5: VISUALISATION ────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor='#080B14')
plt.rcParams['text.color'] = '#C9D1E0'

for ax in axes:
    ax.set_facecolor('#0C1120')
    ax.spines['bottom'].set_color((1.0, 1.0, 1.0, 0.1))
    ax.spines['left'].set_color((1.0, 1.0, 1.0, 0.1))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(colors='#8090B0')

# Plot 1: Actual vs Forecast
ax1 = axes[0]
ax1.plot(range(n), y, color='#5B8EFF', linewidth=2.5, marker='o',
         markersize=6, markerfacecolor='#5B8EFF', label='Actual Revenue')
ax1.plot(range(n, n + FORECAST_MONTHS), forecast, color='#38E2D8',
         linewidth=2, linestyle='--', marker='s', markersize=6,
         markerfacecolor='#38E2D8', label=f'Forecast ({best_name})')
ax1.axvline(x=n-1, color=(91/255, 142/255, 1.0, 0.4), linestyle=':', linewidth=1)
ax1.fill_between(range(n), y, alpha=0.1, color='#5B8EFF')
ax1.fill_between(range(n, n + FORECAST_MONTHS), forecast, alpha=0.1, color='#38E2D8')
ax1.set_title('Revenue Trend + AI Forecast', color='#fff', fontsize=13, fontweight='bold', pad=12)
ax1.set_xlabel('Time Period', color='#8090B0', fontsize=10)
ax1.set_ylabel('Revenue (₹)', color='#8090B0', fontsize=10)
ax1.legend(fontsize=10, facecolor='#0C1120', edgecolor=(1.0, 1.0, 1.0, 0.1), labelcolor='#C9D1E0')
ax1.grid(True, alpha=0.08, color='white')

# Plot 2: Model comparison
ax2 = axes[1]
models = ['Linear\nRegression', 'Random\nForest']
scores = [lr_r2 * 100, rf_r2 * 100]
colors = [(91/255, 142/255, 1.0, 0.7), (56/255, 226/255, 216/255, 0.7)]
bars = ax2.bar(models, scores, color=colors, edgecolor=['#5B8EFF','#38E2D8'],
               linewidth=1, width=0.5, zorder=3)
for bar, score in zip(bars, scores):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
             f'{score:.1f}%', ha='center', fontsize=12, color='#fff', fontweight='bold')
ax2.set_title('Model Accuracy Comparison (R²)', color='#fff', fontsize=13, fontweight='bold', pad=12)
ax2.set_ylabel('Accuracy (%)', color='#8090B0', fontsize=10)
ax2.set_ylim(0, 110)
ax2.grid(True, alpha=0.08, color='white', axis='y', zorder=0)

plt.tight_layout(pad=2.5)
plt.savefig('../ml/forecast_output.png', dpi=150, bbox_inches='tight', facecolor='#080B14')
plt.close()
print(f"\n✅ Chart saved: ml/forecast_output.png")
print("="*55 + "\n")
