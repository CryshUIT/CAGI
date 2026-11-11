import { useNavigate } from "react-router-dom";
import { Layers, PlayCircle, AlertTriangle, Clock, XCircle } from "lucide-react";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import Header from "../components/Header";
import KpiCard from "../components/KpiCard";
import { OutcomeBadge, DataProvenanceNotice } from "../components/Badge";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { useClassifiedIncidents, useMeta } from "../hooks";
import { OUTCOME_COLOR, OUTCOME_LABEL } from "../classify";
import type { Outcome } from "../types";
import { useTheta } from "../ThetaContext";

const OUTCOME_ORDER: Outcome[] = ["early", "late", "not_feasible", "no_alert", "not_evaluable"];

export default function OverviewPage() {
  const { data: incidents, isLoading, isError } = useClassifiedIncidents();
  const { data: meta } = useMeta();
  const { theta, setTheta, model, setModel } = useTheta();
  const navigate = useNavigate();

  const counts: Record<Outcome, number> = {
    early: 0, late: 0, not_feasible: 0, no_alert: 0, not_evaluable: 0,
  };
  incidents.forEach((i) => counts[i.outcome]++);
  const total = incidents.length;

  const donutData = OUTCOME_ORDER.filter((o) => counts[o] > 0).map((o) => ({
    name: OUTCOME_LABEL[o],
    value: counts[o],
    color: OUTCOME_COLOR[o],
    key: o,
  }));

  return (
    <div>
      <Header
        title="Security Operations Center"
        subtitle="Early Warning for Cross-Chain Money Laundering after DeFi Exploits"
      />
      <div className="p-8 space-y-6">
        <DataProvenanceNotice />

        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2 text-sm text-textSecondary">
            Model:
            <select
              value={model}
              onChange={(e) => setModel(e.target.value as "m1_cal" | "b3_cal")}
              className="bg-elevated border border-border rounded-md px-2 py-1 text-text"
            >
              <option value="m1_cal">M1 (Ours)</option>
              <option value="b3_cal">B3' (Baseline)</option>
            </select>
          </div>
          <div className="flex items-center gap-2 text-sm text-textSecondary">
            θ:
            {[0.5, 0.7, 0.9].map((t) => (
              <button
                key={t}
                onClick={() => setTheta(t)}
                className={`px-2.5 py-1 rounded-md border text-xs font-medium ${
                  theta === t
                    ? "bg-accent/15 border-accent text-accent"
                    : "bg-elevated border-border text-textSecondary hover:text-text"
                }`}
              >
                {t}
              </button>
            ))}
            {meta && (
              <button
                onClick={() => setTheta(model === "m1_cal" ? meta.m1_theta_oof : meta.b3_theta_oof)}
                className={`px-2.5 py-1 rounded-md border text-xs font-medium ${
                  theta === (model === "m1_cal" ? meta.m1_theta_oof : meta.b3_theta_oof)
                    ? "bg-accent/15 border-accent text-accent"
                    : "bg-elevated border-border text-textSecondary hover:text-text"
                }`}
              >
                θ_frozen ({(model === "m1_cal" ? meta.m1_theta_oof : meta.b3_theta_oof).toFixed(3)})
              </button>
            )}
          </div>
        </div>

        {isLoading && <LoadingState label="Đang tải 36 incident out-of-fold..." />}
        {isError && <ErrorState message="Không tải được dữ liệu. Đã chạy scripts/dashboard/generate_oof_dashboard_data.py chưa?" />}

        {!isLoading && !isError && (
          <>
            <div className="flex gap-4 flex-wrap">
              <KpiCard icon={Layers} label="Incidents (Out-of-Fold)" value={total} accentColor="#1C9BFF" />
              <KpiCard icon={PlayCircle} label="Analyses in Cache" value={total} accentColor="#00D4F5" />
              <KpiCard
                icon={AlertTriangle}
                label={`Early Warning (${total ? Math.round((counts.early / total) * 100) : 0}%)`}
                value={counts.early}
                accentColor="#18D6A3"
              />
              <KpiCard
                icon={Clock}
                label={`Late Detection (${total ? Math.round((counts.late / total) * 100) : 0}%)`}
                value={counts.late}
                accentColor="#FFBA36"
              />
              <KpiCard
                icon={XCircle}
                label={`Not Evaluable/Feasible (${total ? Math.round(((counts.not_feasible + counts.not_evaluable + counts.no_alert) / total) * 100) : 0}%)`}
                value={counts.not_feasible + counts.not_evaluable + counts.no_alert}
                accentColor="#91A6C2"
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-6">
              <div className="bg-card border border-border rounded-xl p-5">
                <h2 className="text-sm font-semibold text-text mb-4">Incident Library ({total})</h2>
                <div className="overflow-y-auto max-h-[480px]">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-textSecondary border-b border-border">
                        <th className="pb-2 font-medium">Incident</th>
                        <th className="pb-2 font-medium">Chain</th>
                        <th className="pb-2 font-medium">Result</th>
                      </tr>
                    </thead>
                    <tbody>
                      {incidents.map((i) => (
                        <tr
                          key={i.incident_id}
                          onClick={() => navigate(`/investigation/${i.incident_id}`)}
                          className="border-b border-border/50 cursor-pointer hover:bg-elevated/50"
                        >
                          <td className="py-2.5 text-text">{i.incident_id}</td>
                          <td className="py-2.5 text-textSecondary uppercase text-xs">{i.chain}</td>
                          <td className="py-2.5">
                            <OutcomeBadge outcome={i.outcome} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="bg-card border border-border rounded-xl p-5">
                <h2 className="text-sm font-semibold text-text mb-4">Detection Outcomes ({total})</h2>
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie data={donutData} dataKey="value" nameKey="name" innerRadius={65} outerRadius={95} paddingAngle={2}>
                      {donutData.map((d) => (
                        <Cell key={d.key} fill={d.color} stroke="#0D1B30" />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: "#11243C", border: "1px solid #203650", borderRadius: 8, fontSize: 12 }}
                    />
                    <Legend
                      layout="vertical"
                      verticalAlign="middle"
                      align="right"
                      formatter={(v) => <span className="text-xs text-textSecondary">{v}</span>}
                    />
                  </PieChart>
                </ResponsiveContainer>
                {meta && (
                  <div className="mt-3 text-[11px] text-textSecondary leading-snug border-t border-border pt-3">
                    Pooled PR-AUC (OOF, 36 incident): M1={meta.pooled_pr_auc_m1.toFixed(4)}, B3'=
                    {meta.pooled_pr_auc_b3.toFixed(4)}
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
