import json
from pathlib import Path

import pandas as pd

D = Path(__file__).resolve().parent.parent / "data"
JAN_START = pd.Timestamp("2026-01-01", tz="UTC")
JAN_END = pd.Timestamp("2026-02-01", tz="UTC")

# ---------- 1. Actuals: duplicates hatao, sirf January ----------
a = pd.DataFrame(json.loads((D / "actuals_raw.json").read_text()))
a["startTime"] = pd.to_datetime(a["startTime"], utc=True)
a = a.drop_duplicates("startTime").sort_values("startTime")
a = a[(a.startTime >= JAN_START) & (a.startTime < JAN_END)]
a = a[["startTime", "generation"]].rename(columns={"generation": "actual"})
print("Actual rows:", len(a), "(expected 1488)")

# ---------- 2. Forecasts ----------
f = pd.DataFrame(json.loads((D / "forecasts_raw.json").read_text()))
f["startTime"] = pd.to_datetime(f["startTime"], utc=True)
f["publishTime"] = pd.to_datetime(f["publishTime"], utc=True)
f = f.drop_duplicates(["publishTime", "startTime"])
f = f.rename(columns={"generation": "forecast"})
f["horizon_h"] = (f.startTime - f.publishTime).dt.total_seconds() / 3600
print("Forecast rows:", len(f))
print("Horizon (hours) min/max:", f.horizon_h.min(), f.horizon_h.max())


# ---------- 3. Decision-time forecast (sabse important) ----------
def decision_forecast(f, cutoff_hour=9):
    """Delivery day D ke liye: D-1 ke cutoff_hour (UTC) tak jo latest forecast publish hua."""
    f = f.copy()
    f["delivery_date"] = f.startTime.dt.normalize()
    f["cutoff"] = f.delivery_date - pd.Timedelta(days=1) + pd.Timedelta(hours=cutoff_hour)
    ok = f[f.publishTime <= f.cutoff]
    ok = ok.sort_values("publishTime").groupby("startTime").tail(1)
    return ok[["startTime", "publishTime", "forecast", "horizon_h"]]


d = decision_forecast(f, cutoff_hour=9)
m = a.merge(d, on="startTime", how="inner")  # hourly points pe compare
m["error"] = m.forecast - m.actual

print()
print("Compared rows:", len(m), "(hourly points in Jan, ~744)")
print("Horizon range used:", m.horizon_h.min(), "->", m.horizon_h.max())
print("MAE  (MW):", round(m.error.abs().mean(), 1))
print("RMSE (MW):", round((m.error ** 2).mean() ** 0.5, 1))
print("Bias (MW):", round(m.error.mean(), 1))
print("P90 abs error:", round(m.error.abs().quantile(0.9), 1))
print()
print(m.head(5))
print()
print("---- Daily bias (MW) ----")
m["date"] = m.startTime.dt.date
daily = m.groupby("date").agg(
    actual_mean=("actual", "mean"),
    forecast_mean=("forecast", "mean"),
    bias=("error", "mean"),
    mae=("error", lambda x: x.abs().mean()),
).round(0)
print(daily.to_string())
print()
print("Days with positive bias:", (daily.bias > 0).sum(), "/", len(daily))