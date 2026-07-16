SalesPulse AI — Local development (dev guide)

Prereqs:
- Python 3.11 or 3.10
- (Recommended on Windows) Conda to avoid building heavy packages from source
- Docker (optional)

Quick dev (Python virtualenv):

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
# or
source .venv/bin/activate  # macOS/Linux
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload --port 8000
# If you are on Windows and pip fails installing `pandas`, use the dev requirements which avoid pandas:
pip install -r backend/requirements-dev.txt
cd backend
uvicorn main:app --reload --port 8000
```

Open the frontend files with a simple static server (VS Code Live Server or `python -m http.server 5500` at the repo root) and visit `http://127.0.0.1:5500/register.html`.

Docker (optional):

```bash
docker build -t salespulse:dev .
docker run --rm -p 8000:8000 -e SECRET_KEY=change_me salespulse:dev
# or with compose
docker-compose up --build
```

Notes:
- Copy `.env.example` to `.env` and set `SECRET_KEY` and `GEMINI_API_KEY` for production.
- The backend serves ML plot at `/ml/forecast_output.png` after a forecast run.
