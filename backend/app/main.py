from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .core import build_comparison, compute_metrics, horizon_metrics

app = FastAPI(title="Wind Forecast Monitor")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CutoffHour = Query(9, ge=0, le=23, description="D-1 decision cutoff hour (UTC)")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/forecast")
def forecast(cutoff_hour: int = CutoffHour):
    m = build_comparison(cutoff_hour)
    return [
        {
            "time": r.startTime.isoformat(),
            "actual": int(r.actual),
            "forecast": int(r.forecast),
            "error": int(r.error),
            "publish_time": r.publishTime.isoformat(),
            "horizon_h": r.horizon_h,
        }
        for r in m.itertuples()
    ]


@app.get("/api/metrics")
def metrics(cutoff_hour: int = CutoffHour):
    m = build_comparison(cutoff_hour)
    m["date"] = m.startTime.dt.strftime("%Y-%m-%d")
    daily = [
        {"date": d, **compute_metrics(g)} for d, g in m.groupby("date")
    ]
    return {"cutoff_hour": cutoff_hour, "overall": compute_metrics(m), "daily": daily}
@app.get("/api/horizon")
def horizon():
    return horizon_metrics()