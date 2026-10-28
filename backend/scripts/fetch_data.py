"""Download Jan 2026 wind actuals (FUELHH) and forecasts (WINDFOR) from Elexon."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def chunks(start, end, days):
    """Split a date range into small windows (API limits big ranges)."""
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%MZ")


def fetch_actuals():
    # Jan 2026 targets (a bit of buffer at the end)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 2, 1, tzinfo=timezone.utc)
    rows = []
    for a, b in chunks(start, end, 7):
        params = {
            "settlementDateFrom": a.strftime("%Y-%m-%d"),
            "settlementDateTo": b.strftime("%Y-%m-%d"),
            "fuelType": "WIND",
            "format": "json",
        }
        r = requests.get(f"{BASE}/FUELHH/stream", params=params, timeout=60)
        r.raise_for_status()
        part = r.json()
        print(f"actuals {a.date()} -> {b.date()}: {len(part)} rows")
        rows.extend(part)
    (DATA_DIR / "actuals_raw.json").write_text(json.dumps(rows))
    print("Total actual rows:", len(rows))


def fetch_forecasts():
    # Forecasts for Jan are published from ~mid Dec onwards
    start = datetime(2025, 12, 15, tzinfo=timezone.utc)
    end = datetime(2026, 2, 1, tzinfo=timezone.utc)
    rows = []
    for a, b in chunks(start, end, 3):
        params = {
            "publishDateTimeFrom": iso(a),
            "publishDateTimeTo": iso(b),
            "format": "json",
        }
        r = requests.get(f"{BASE}/WINDFOR/stream", params=params, timeout=120)
        r.raise_for_status()
        part = r.json()
        print(f"forecasts published {a.date()} -> {b.date()}: {len(part)} rows")
        rows.extend(part)
    (DATA_DIR / "forecasts_raw.json").write_text(json.dumps(rows))
    print("Total forecast rows:", len(rows))


if __name__ == "__main__":
    fetch_actuals()
    fetch_forecasts()