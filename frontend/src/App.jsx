import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const C = {
  navy: "#0f2742",
  blue: "#2563eb",
  orange: "#f97316",
  red: "#dc2626",
  green: "#16a34a",
  text: "#0f172a",
  muted: "#64748b",
  border: "#e2e8f0",
  bg: "#f1f5f9",
};

const panel = {
  background: "white",
  borderRadius: 14,
  padding: 20,
  border: `1px solid ${C.border}`,
  boxShadow: "0 1px 3px rgba(15,23,42,0.06)",
};

function Stat({ label, value, unit, hint, accent }) {
  return (
    <div style={{ ...panel, padding: 16, flex: "1 1 160px", borderTop: `3px solid ${accent}` }}>
      <div style={{ fontSize: 12, color: C.muted, textTransform: "uppercase", letterSpacing: 0.5 }}>
        {label}
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color: C.text, marginTop: 4 }}>
        {value} <span style={{ fontSize: 14, fontWeight: 500, color: C.muted }}>{unit}</span>
      </div>
      <div style={{ fontSize: 12, color: C.muted, marginTop: 2 }}>{hint}</div>
    </div>
  );
}

function Section({ title, subtitle, children, height }) {
  return (
    <div style={{ ...panel, marginTop: 20 }}>
      <div style={{ fontSize: 17, fontWeight: 600, color: C.text }}>{title}</div>
      <div style={{ fontSize: 13, color: C.muted, marginBottom: 12 }}>{subtitle}</div>
      <div style={{ height }}>{children}</div>
    </div>
  );
}

export default function App() {
  const [cutoff, setCutoff] = useState(9);
  const [metrics, setMetrics] = useState(null);
  const [series, setSeries] = useState([]);
  const [daily, setDaily] = useState([]);
  const [horizon, setHorizon] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/horizon`)
      .then((r) => r.json())
      .then(setHorizon)
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    setError(null);
    Promise.all([
      fetch(`${API}/api/metrics?cutoff_hour=${cutoff}`).then((r) => r.json()),
      fetch(`${API}/api/forecast?cutoff_hour=${cutoff}`).then((r) => r.json()),
    ])
      .then(([m, f]) => {
        setMetrics(m.overall);
        setDaily(m.daily.map((d) => ({ date: d.date.slice(5), Bias: d.bias })));
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
    <div style={{ background: C.bg, minHeight: "100vh", fontFamily: "Inter, system-ui, sans-serif" }}>
      <header style={{ background: C.navy, color: "white", padding: "22px 0" }}>
        <div style={{ maxWidth: 1150, margin: "0 auto", padding: "0 24px" }}>
          <div style={{ fontSize: 26, fontWeight: 700 }}>Wind Forecast Monitor</div>
          <div style={{ color: "#93c5fd", fontSize: 14, marginTop: 4 }}>
            Day-ahead wind forecast vs actual, UK national, January 2026 (UTC)
          </div>
        </div>
      </header>

      <main style={{ maxWidth: 1150, margin: "0 auto", padding: "24px" }}>
        <div style={panel}>
          <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
            <div>
              <div style={{ fontWeight: 600, color: C.text }}>Decision cutoff on D-1</div>
              <div style={{ fontSize: 13, color: C.muted }}>
                Only forecasts published before this time are used for the next day
              </div>
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: C.blue }}>
              {String(cutoff).padStart(2, "0")}:00 UTC
            </div>
          </div>
          <input
            type="range"
            min="0"
            max="23"
            value={cutoff}
            onChange={(e) => setCutoff(Number(e.target.value))}
            style={{ width: "100%", marginTop: 12, accentColor: C.blue }}
          />
        </div>

        {error && <p style={{ color: C.red }}>Error: {error}</p>}
        {!metrics && !error && (
          <p style={{ color: C.muted }}>Loading data (the server may take up to a minute to wake up)...</p>
        )}

        {metrics && (
          <>
            <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginTop: 20 }}>
              <Stat label="MAE" value={metrics.mae} unit="MW" hint="Average miss" accent={C.blue} />
              <Stat label="RMSE" value={metrics.rmse} unit="MW" hint="Penalises big misses" accent={C.blue} />
              <Stat label="Bias" value={metrics.bias} unit="MW" hint="Forecast minus actual" accent={C.red} />
              <Stat label="P90 error" value={metrics.p90_abs_error} unit="MW" hint="9 in 10 hours below this" accent={C.orange} />
              <Stat label="MAE / mean wind" value={metrics.mae_pct_of_mean_actual} unit="%" hint="Relative error" accent={C.green} />
              <Stat label="Over-forecast" value={metrics.pct_over_forecast} unit="%" hint="Share of hours" accent={C.red} />
            </div>

            <div
              style={{
                ...panel,
                marginTop: 20,
                background: "#eff6ff",
                borderColor: "#bfdbfe",
                color: C.text,
                fontSize: 14,
              }}
            >
              <b>Takeaway:</b> at a {String(cutoff).padStart(2, "0")}:00 cutoff the forecast is off by{" "}
              {metrics.mae} MW on average and is too high in {metrics.pct_over_forecast}% of hours. Consider
              buffering the wind forecast downward by about {Math.round(metrics.bias)} MW when sizing the
              day-ahead purchase.
            </div>
          </>
        )}

        <Section
          title="Actual vs forecast wind generation"
          subtitle="Forecast shown is the latest one available at the decision cutoff"
          height={380}
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={series}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
              <XAxis dataKey="t" minTickGap={70} tick={{ fontSize: 12 }} />
              <YAxis unit=" MW" width={85} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="Actual" stroke={C.blue} dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="Forecast" stroke={C.orange} dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Section>

        <Section
          title="Daily bias"
          subtitle="Above zero means the forecast was too high that day"
          height={280}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={daily}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis unit=" MW" width={85} tick={{ fontSize: 12 }} />
              <Tooltip />
              <ReferenceLine y={0} stroke={C.muted} />
              <Bar dataKey="Bias" fill={C.red} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section
          title="Error vs forecast horizon"
          subtitle="Hours between forecast publication and target time. Older forecasts are less accurate."
          height={280}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={horizon}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
              <XAxis dataKey="horizon" tick={{ fontSize: 12 }} />
              <YAxis unit=" MW" width={85} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="mae" name="MAE" fill={C.green} radius={[3, 3, 0, 0]} />
              <Bar dataKey="bias" name="Bias" fill={C.red} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <p style={{ color: C.muted, fontSize: 12, marginTop: 24 }}>
          Source: Elexon BMRS (FUELHH actuals, WINDFOR forecasts). Metrics computed on hours where both exist.
        </p>
      </main>
    </div>
  );
}