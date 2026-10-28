import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const API = "http://127.0.0.1:8000";

const card = {
  background: "white",
  borderRadius: 8,
  padding: 16,
  boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
  minWidth: 150,
};

function Card({ label, value, unit }) {
  return (
    <div style={card}>
      <div style={{ fontSize: 13, color: "#667" }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700 }}>
        {value} <span style={{ fontSize: 14, fontWeight: 400 }}>{unit}</span>
      </div>
    </div>
  );
}

export default function App() {
  const [cutoff, setCutoff] = useState(9);
  const [metrics, setMetrics] = useState(null);
  const [series, setSeries] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    setError(null);
    Promise.all([
      fetch(`${API}/api/metrics?cutoff_hour=${cutoff}`).then((r) => r.json()),
      fetch(`${API}/api/forecast?cutoff_hour=${cutoff}`).then((r) => r.json()),
    ])
      .then(([m, f]) => {
        setMetrics(m.overall);
        setSeries(
          f.map((p) => ({
            t: p.time.slice(5, 16).replace("T", " "),
            Actual: p.actual,
            Forecast: p.forecast,
          }))
        );
      })
      .catch((e) => setError(e.message));
  }, [cutoff]);

  return (
    <div style={{ padding: 24, fontFamily: "sans-serif", maxWidth: 1100, margin: "0 auto" }}>
      <h1>Wind Forecast Monitor</h1>
      <p style={{ color: "#667" }}>
        Day-ahead wind forecast vs actual, January 2026 (national, UTC)
      </p>

      <label>
        Decision cutoff (UTC hour on D-1): <b>{cutoff}:00</b>
        <br />
        <input
          type="range"
          min="0"
          max="23"
          value={cutoff}
          onChange={(e) => setCutoff(Number(e.target.value))}
          style={{ width: 300 }}
        />
      </label>

      {error && <p style={{ color: "red" }}>Error: {error}</p>}
      {!metrics && !error && <p>Loading...</p>}

      {metrics && (
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", margin: "20px 0" }}>
          <Card label="MAE" value={metrics.mae} unit="MW" />
          <Card label="RMSE" value={metrics.rmse} unit="MW" />
          <Card label="Bias (forecast - actual)" value={metrics.bias} unit="MW" />
          <Card label="P90 abs error" value={metrics.p90_abs_error} unit="MW" />
          <Card label="MAE % of mean wind" value={metrics.mae_pct_of_mean_actual} unit="%" />
          <Card label="Hours over-forecast" value={metrics.pct_over_forecast} unit="%" />
        </div>
      )}

      <div style={{ ...card, height: 420 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={series}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="t" minTickGap={60} />
            <YAxis unit=" MW" width={80} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="Actual" stroke="#1f77b4" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey="Forecast" stroke="#ff7f0e" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}