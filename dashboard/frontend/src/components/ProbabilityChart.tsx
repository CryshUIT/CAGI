import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ReferenceLine, ResponsiveContainer,
} from "recharts";
import type { PrefixPoint } from "../types";

export default function ProbabilityChart({
  points,
  theta,
  eStar,
  firstAlertK,
}: {
  points: PrefixPoint[];
  theta: number;
  eStar: number | null;
  firstAlertK: number | null;
}) {
  const sorted = [...points].sort((a, b) => a.k - b.k);
  const data = sorted.map((p) => ({ k: p.k, M1: p.m1_cal, "B3'": p.b3_cal }));

  return (
    <div className="bg-card border border-border rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-text">Detection Probability p̂_k</h3>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#203650" strokeDasharray="3 3" />
          <XAxis dataKey="k" stroke="#93A9C4" fontSize={12} label={{ value: "k (prefix length)", position: "insideBottom", offset: -3, fill: "#93A9C4", fontSize: 11 }} />
          <YAxis domain={[0, 1]} stroke="#93A9C4" fontSize={12} />
          <Tooltip
            contentStyle={{ background: "#11243C", border: "1px solid #203650", borderRadius: 8, fontSize: 12 }}
            labelFormatter={(k) => `k = ${k}`}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: "#93A9C4" }} />
          <ReferenceLine y={theta} stroke="#FFBA36" strokeDasharray="6 4" label={{ value: `θ = ${theta}`, fill: "#FFBA36", fontSize: 11, position: "right" }} />
          {eStar !== null && (
            <ReferenceLine x={eStar} stroke="#FF5267" strokeDasharray="4 4" label={{ value: "exit", fill: "#FF5267", fontSize: 11, position: "top" }} />
          )}
          {firstAlertK !== null && (
            <ReferenceLine x={firstAlertK} stroke="#00D4F5" strokeDasharray="2 2" />
          )}
          <Line type="monotone" dataKey="M1" stroke="#00D4F5" strokeWidth={2} dot={{ r: 3 }} connectNulls />
          <Line type="monotone" dataKey="B3'" stroke="#1C9BFF" strokeWidth={2} dot={{ r: 3 }} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
