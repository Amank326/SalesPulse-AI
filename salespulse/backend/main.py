"""
SalesPulse AI — FastAPI Backend
Run: uvicorn backend.main:app --reload --port 8000
"""

import datetime
import io
import os
import pathlib
import sys
from typing import Optional, List, Dict

from dotenv import load_dotenv
import jwt
import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Path setup — ensure repo root (`salespulse/`) is on sys.path so that
# `backend` and `ml` packages are importable regardless of CWD.
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.gemini_service import GeminiService
from ml.prediction import forecast_df

load_dotenv(ROOT / ".env")

# ---------------------------------------------------------------------------
# Security configuration
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    import secrets
    SECRET_KEY = secrets.token_urlsafe(48)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

# ---------------------------------------------------------------------------
# Password hashing — bcrypt with salt (production-grade)
# ---------------------------------------------------------------------------
try:
    import bcrypt

    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

except ImportError:
    import hashlib

    def hash_password(password: str) -> str:
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return salt.hex() + ":" + key.hex()

    def verify_password(password: str, hashed: str) -> bool:
        try:
            salt_hex, key_hex = hashed.split(":")
            salt = bytes.fromhex(salt_hex)
            key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
            return key.hex() == key_hex
        except Exception:
            return False


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(title="SalesPulse AI API", version="1.0.0")

# CORS — configurable via CORS_ORIGINS env var (comma-separated), with sensible defaults
_default_origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]
_env_origins = os.environ.get("CORS_ORIGINS", "")
_allowed_origins = [o.strip() for o in _env_origins.split(",") if o.strip()] if _env_origins else _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static file mounts
# ---------------------------------------------------------------------------
# Serve ML artifacts (plots, etc.) at /ml
ML_DIR = ROOT / "ml"
if ML_DIR.exists():
    app.mount("/ml", StaticFiles(directory=str(ML_DIR)), name="ml_static")

# Serve frontend at /app (HTML, JS, CSS)
FRONTEND_DIR = ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

security = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# In-memory "database" — suitable for development & demo
# Production: replace with SQLite / PostgreSQL
# ---------------------------------------------------------------------------
USERS_DB: dict = {}
FORECASTS_DB: dict = {}


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ForecastRequest(BaseModel):
    months: int = 30


class InsightRequest(BaseModel):
    report_type: str = "summary"  # summary, executive, marketing, inventory, risk, revenue


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def _utcnow() -> datetime.datetime:
    """Timezone-aware UTC now (avoids deprecated datetime.utcnow)."""
    return datetime.datetime.now(datetime.timezone.utc)


def create_access_token(email: str, expires_delta: Optional[datetime.timedelta] = None) -> str:
    expire = _utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    if email not in USERS_DB:
        raise HTTPException(status_code=401, detail="User not found")
    return email


# ═══════════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/register")
def register(req: RegisterRequest):
    if req.email in USERS_DB:
        raise HTTPException(status_code=400, detail="Email already registered")
    USERS_DB[req.email] = {
        "name": req.name,
        "email": req.email,
        "password": hash_password(req.password),
        "created_at": _utcnow().isoformat(),
    }
    token = create_access_token(req.email)
    return {"message": "Account created successfully", "token": token, "name": req.name, "email": req.email}


@app.post("/api/login")
def login(req: LoginRequest):
    user = USERS_DB.get(req.email)
    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(req.email)
    return {"token": token, "name": user["name"], "email": user["email"]}


@app.get("/api/me")
def get_me(email: str = Depends(get_current_user)):
    user = USERS_DB[email]
    return {"name": user["name"], "email": user["email"]}


# ═══════════════════════════════════════════════════════════════════════════
# DATA UPLOAD & CLEANING
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), email: str = Depends(get_current_user)):
    contents = await file.read()
    try:
        if file.filename and file.filename.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {e}")

    # Auto-clean
    before_rows = len(df)
    df = df.drop_duplicates()
    df = df.dropna(how="all")

    # Auto-detect date column
    date_col = None
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
                date_col = col
                break
            except Exception:
                pass

    # Auto-detect revenue / sales column
    rev_col = None
    for col in df.columns:
        if any(k in col.lower() for k in ["bill", "revenue", "sales", "amount", "price", "total"]):
            rev_col = col
            break

    # Store cleaned data for user
    FORECASTS_DB[email] = {
        "data": df.to_json(orient="records", date_format="iso"),
        "date_col": date_col,
        "rev_col": rev_col,
        "rows": len(df),
        "cols": list(df.columns),
        "cleaned_rows": before_rows - len(df),
        "uploaded_at": _utcnow().isoformat(),
    }

    return {
        "success": True,
        "rows": len(df),
        "columns": list(df.columns),
        "date_column": date_col,
        "revenue_column": rev_col,
        "rows_cleaned": before_rows - len(df),
        "preview": df.head(5).to_dict(orient="records"),
    }


# ═══════════════════════════════════════════════════════════════════════════
# FORECAST
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/forecast")
def run_forecast(req: ForecastRequest, email: str = Depends(get_current_user)):
    """Runs enterprise-grade forecasting matching LR vs RF recursively."""
    if email not in FORECASTS_DB:
        raise HTTPException(status_code=400, detail="No data uploaded yet. Upload a CSV first.")

    stored = FORECASTS_DB[email]
    df = pd.read_json(io.StringIO(stored["data"]), orient="records")
    
    try:
        # Run forecasting script recursively
        result = forecast_df(df, target_col=stored.get("rev_col"), periods=req.months)
        # Store last result for Gemini context
        FORECASTS_DB[email]["last_result"] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting calculation failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/analytics")
def get_analytics(email: str = Depends(get_current_user)):
    """Returns summary analytics for the dashboard."""
    if email not in FORECASTS_DB:
        return {
            "total_revenue": 9157,
            "total_orders": 20,
            "avg_order": 457.85,
            "cancellation_rate": 25.0,
            "top_product": "Chicken Biryani",
            "top_hotel": "Spice Paradise",
            "revenue_by_hotel": {"Pizza Palace": 2296, "Spice Paradise": 2398, "Burger Bistro": 1663},
            "revenue_by_payment": {"Card": 2045, "COD": 2046, "UPI": 1860},
            "delivery_status": {"Delivered": 14, "Cancelled": 4, "In Progress": 3},
            "daily_revenue": {
                "Oct 1": 1599, "Oct 2": 1800, "Oct 3": 1416,
                "Oct 4": 1798, "Oct 5": 899, "Oct 6": 498,
            },
            "data_source": "demo",
        }

    stored = FORECASTS_DB[email]
    df = pd.read_json(io.StringIO(stored["data"]), orient="records")
    rev_col = stored.get("rev_col")
    date_col = stored.get("date_col")

    analytics = {
        "total_rows": len(df),
        "columns": list(df.columns),
        "data_source": "uploaded",
    }
    
    # Calculate key metrics
    if rev_col and rev_col in df.columns:
        analytics["total_revenue"] = round(float(df[rev_col].sum()), 2)
        analytics["avg_value"] = round(float(df[rev_col].mean()), 2)
        analytics["max_value"] = round(float(df[rev_col].max()), 2)
        analytics["min_value"] = round(float(df[rev_col].min()), 2)
        
    # Calculate monthly summary if forecast was run
    if "last_result" in stored:
        analytics["forecast_total"] = stored["last_result"]["forecast"]["values"]
        analytics["predicted"] = round(float(sum(stored["last_result"]["forecast"]["values"])), 2)

    return analytics


# ═══════════════════════════════════════════════════════════════════════════
# AI INSIGHTS & CHAT (Gemini integration)
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/ai-insights")
def ai_insights(req: InsightRequest, email: str = Depends(get_current_user)):
    """Generate professional AI business reports based on the forecast results."""
    if email not in FORECASTS_DB or "last_result" not in FORECASTS_DB[email]:
        raise HTTPException(status_code=400, detail="Please upload data and run forecast first.")

    data_context = FORECASTS_DB[email]["last_result"]
    try:
        svc = GeminiService()
        report = svc.generate_report(req.report_type, data_context)
        return report
    except RuntimeError as e:
        return JSONResponse(status_code=501, content={"detail": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai-chat")
def ai_chat(req: ChatRequest, email: str = Depends(get_current_user)):
    """Chat overlay route for context-aware natural language conversation."""
    if email not in FORECASTS_DB or "last_result" not in FORECASTS_DB[email]:
        raise HTTPException(status_code=400, detail="Please upload data and run forecast first.")

    data_context = FORECASTS_DB[email]["last_result"]
    try:
        svc = GeminiService()
        reply = svc.chat_with_data(req.message, data_context, req.history)
        return {"reply": reply}
    except RuntimeError as e:
        return JSONResponse(status_code=501, content={"detail": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# HEALTH & ROOT
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0", "service": "SalesPulse AI"}


@app.get("/")
def root():
    return {"message": "SalesPulse AI API is running", "docs": "/docs", "frontend": "/app/index.html"}
