# Wind Forecast Monitor

Web app for a UK energy utility's day-ahead desk. It shows the latest national wind
forecast available at decision time and quantifies how accurate that forecast is.
Data: Elexon BMRS only (FUELHH actuals, WINDFOR forecasts), January 2026.

## Live app

- Frontend (Vercel): https://kjhwr-psi.vercel.app
- Backend API (Render): https://kjhwr-zd49.onrender.com/docs
  (free tier, first request can take 30-60 s to wake up)

## Key idea

For each target hour T on delivery day D, we use the latest forecast with
publishTime <= (D-1 at cutoff hour, UTC). The cutoff is a slider in the UI
(default 09:00 UTC). This avoids look-ahead: no forecast is used that was not
available at decision time. Forecasts are hourly and actuals are 30-minute, so the
comparison is done on the hours where both exist (744 points in January).

## Findings (cutoff 09:00 UTC)

- MAE 2127.5 MW (18.4% of mean wind), RMSE 2606.1 MW, bias +1851.5 MW
- Forecast over-predicts in 84.8% of hours and on 27 of 31 days
- Error grows with horizon: MAE about 1768 MW at 0-6 h vs 2409 MW at 42-48 h
- Moving the cutoff from 09:00 to 15:00 lowers MAE to 2005.2 MW

## Repo layout

- backend/app/core.py - data loading, decision-time forecast selection, metrics
- backend/app/main.py - FastAPI endpoints: /health, /api/forecast, /api/metrics, /api/horizon
- backend/data/ - cached raw Elexon JSON (Dec 15 2025 - Jan 2026)
- backend/scripts/ - fetch_data.py (download), explore.py, check_data.py
- backend/tests/ - pytest tests
- backend/Dockerfile, frontend/Dockerfile - containers
- frontend/src/App.jsx - React dashboard (Recharts)

## Run locally

Backend:

    cd backend
    python -m venv venv
    venv\Scripts\activate        (Mac/Linux: source venv/bin/activate)
    pip install -r requirements.txt pytest httpx
    uvicorn app.main:app --reload
    python -m pytest -v

Frontend:

    cd frontend
    npm install
    npm run dev                  (http://localhost:5173)

With Docker:

    docker build -t wind-backend ./backend
    docker run -p 8000:8000 wind-backend
    docker build -t wind-frontend ./frontend
    docker run -p 8080:80 wind-frontend    (http://localhost:8080)

Refresh data (optional): python backend/scripts/fetch_data.py

## Notes and limitations

- Data is cached in the repo so the demo does not depend on the live Elexon API.
- The persistent over-forecast may reflect definition differences between WINDFOR
  and FUELHH wind, or curtailment. This data alone cannot confirm the cause.
- Single month of data; results may not generalise.

## AI usage

I used an AI assistant (Claude) for guidance on structure and for code suggestions.
I ran, tested and verified everything myself: data download and cleaning, the
decision-time forecast logic, metrics checked against independent calculations,
pytest tests, Docker builds and deployment.
