# SalesPulse AI — Sales Forecasting System
### By Aman Kumar Gupta · B.Tech Final Year IT

---

## Project Structure

```
salespulse/
├── frontend/           ← Website (open in browser directly)
│   ├── index.html      ← Landing page
│   ├── (login removed) ← Sign in handled via register/dashboard
│   ├── register.html   ← Sign up
│   ├── dashboard.html  ← Analytics dashboard
│   ├── upload.html     ← Upload your data
│   ├── style.css       ← All styles
│   └── main.js         ← All frontend logic
│
├── backend/            ← Python API server
│   ├── main.py         ← FastAPI backend
│   └── requirements.txt
│
└── ml/                 ← Machine Learning
    ├── forecasting.py  ← ML model (run independently)
    └── forecast_output.png
```

---

## How to Run

### Option A — Frontend only (simplest, works offline)
1. Open `frontend/index.html` in any browser
2. That's it! No server needed.
3. Register → Upload CSV → See Dashboard (login page removed; dashboard accessible)

### Option B — With Python backend
```bash
# Install dependencies
pip install fastapi uvicorn pandas openpyxl scikit-learn

# Start backend server
cd backend
uvicorn main:app --reload --port 8000

# Open frontend
open frontend/index.html
```
Backend API runs at: http://localhost:8000
API Docs at: http://localhost:8000/docs

### Option C — Run ML model directly
```bash
pip install pandas numpy scikit-learn matplotlib

cd ml
python forecasting.py
```

---

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Frontend   | HTML5, CSS3, Vanilla JS, Chart.js   |
| Backend    | Python, FastAPI, Uvicorn            |
| ML Models  | Linear Regression, Random Forest    |
| Database   | LocalStorage (frontend) / In-memory |
| Charts     | Chart.js (dashboard), Matplotlib    |

---

## Features

- Register / Login with session management
- Drag & drop CSV/Excel upload
- Auto data cleaning (duplicates, missing values)
- AI Sales Forecast (Linear Regression + Random Forest)
- Interactive dashboard with 5 chart types
- AI Recommendations panel
- Fully responsive design

---

## GitHub Upload Steps

```bash
git init
git add .
git commit -m "SalesPulse AI - Sales Forecasting Project"
git remote add origin https://github.com/YOUR_USERNAME/salespulse-ai
git push -u origin main
```

---

*Made with ♥ for Data Analytics submission — July 2026*
