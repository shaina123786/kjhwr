import json
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"

actuals = json.loads((D / "actuals_raw.json").read_text())
fc = json.loads((D / "forecasts_raw.json").read_text())

print("ACTUALS rows:", len(actuals))
print("Actuals sample:", actuals[:2])
print("Actuals fuelTypes:", {r.get("fuelType") for r in actuals})
print("Actuals startTime range:",
      min(r["startTime"] for r in actuals), "->",
      max(r["startTime"] for r in actuals))

print()
print("FORECAST rows:", len(fc))
print("Forecast sample:", fc[:2])
print("publishTime range:",
      min(r["publishTime"] for r in fc), "->",
      max(r["publishTime"] for r in fc))
print("startTime range:",
      min(r["startTime"] for r in fc), "->",
      max(r["startTime"] for r in fc))
print("Unique publishTimes:", len({r["publishTime"] for r in fc}))