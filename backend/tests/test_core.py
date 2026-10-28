from fastapi.testclient import TestClient

from app.core import build_comparison, compute_metrics
from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_no_lookahead():
    """Every forecast used must be published before the D-1 cutoff."""
    m = build_comparison(9)
    cutoff = m.startTime.dt.normalize() - __import__("pandas").Timedelta(days=1) \
        + __import__("pandas").Timedelta(hours=9)
    assert (m.publishTime <= cutoff).all()


def test_overall_mae_matches_exploration():
    m = build_comparison(9)
    assert compute_metrics(m)["mae"] == 2127.5


def test_metrics_endpoint():
    r = client.get("/api/metrics?cutoff_hour=9")
    assert r.status_code == 200
    assert r.json()["overall"]["n"] == 744


def test_invalid_cutoff_rejected():
    assert client.get("/api/metrics?cutoff_hour=30").status_code == 422