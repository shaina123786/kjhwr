import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
JAN_START = pd.Timestamp("2026-01-01", tz="UTC")
JAN_END = pd.Timestamp("2026-02-01", tz="UTC")


@lru_cache
def load_actuals() -> pd.DataFrame:
    a = pd.DataFrame(json.loads((DATA_DIR / "actuals_raw.json").read_text()))
    a["startTime"] = pd.to_datetime(a["startTime"], utc=True)
    a = a.drop_duplicates("startTime").sort_values("startTime")
    a = a[(a.startTime >= JAN_START) & (a.startTime < JAN_END)]
    return a[["startTime", "generation"]].rename(columns={"generation": "actual"})


@lru_cache
def load_forecasts() -> pd.DataFrame:
    f = pd.DataFrame(json.loads((DATA_DIR / "forecasts_raw.json").read_text()))
    f["startTime"] = pd.to_datetime(f["startTime"], utc=True)
    f["publishTime"] = pd.to_datetime(f["publishTime"], utc=True)
    f = f.drop_duplicates(["publishTime", "startTime"])
    f = f.rename(columns={"generation": "forecast"})
    f["horizon_h"] = (f.startTime - f.publishTime).dt.total_seconds() / 3600
    return f


def decision_forecast(f: pd.DataFrame, cutoff_hour: int) -> pd.DataFrame:
    """For each target time, the latest forecast published by D-1 at cutoff_hour UTC."""
    f = f.copy()
    delivery_date = f.startTime.dt.normalize()
    f["cutoff"] = delivery_date - pd.Timedelta(days=1) + pd.Timedelta(hours=cutoff_hour)
    ok = f[f.publishTime <= f.cutoff]
    ok = ok.sort_values("publishTime").groupby("startTime").tail(1)
    return ok[["startTime", "publishTime", "forecast", "horizon_h"]]


def build_comparison(cutoff_hour: int) -> pd.DataFrame:
    d = decision_forecast(load_forecasts(), cutoff_hour)
    m = load_actuals().merge(d, on="startTime", how="inner").sort_values("startTime")
    m["error"] = m.forecast - m.actual
    return m


def compute_metrics(m: pd.DataFrame) -> dict:
    if m.empty:
        return {"n": 0}
    abs_err = m.error.abs()
    return {
        "n": int(len(m)),
        "mae": round(float(abs_err.mean()), 1),
        "rmse": round(float((m.error ** 2).mean() ** 0.5), 1),
        "bias": round(float(m.error.mean()), 1),
        "p90_abs_error": round(float(abs_err.quantile(0.9)), 1),
        "p99_abs_error": round(float(abs_err.quantile(0.99)), 1),
        "mae_pct_of_mean_actual": round(float(abs_err.mean() / m.actual.mean() * 100), 1),
        "pct_over_forecast": round(float((m.error > 0).mean() * 100), 1),
    }
def horizon_metrics() -> list[dict]:
    """Error by forecast horizon, using every published forecast (not just decision-time ones)."""
    f = load_forecasts()
    a = load_actuals()
    m = f.merge(a, on="startTime", how="inner")
    m = m[(m.horizon_h >= 0) & (m.horizon_h <= 48)]
    m["error"] = m.forecast - m.actual
    m["bucket"] = (m.horizon_h // 6 * 6).astype(int)
    out = []
    for b, g in m.groupby("bucket"):
        out.append(
            {
                "horizon": f"{b}-{b + 6}h",
                "n": int(len(g)),
                "mae": round(float(g.error.abs().mean()), 1),
                "bias": round(float(g.error.mean()), 1),
            }
        )
    return out