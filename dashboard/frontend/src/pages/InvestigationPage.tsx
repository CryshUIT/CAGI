import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { AlertTriangle, LogOut, Clock, Tag, Copy } from "lucide-react";
import Header from "../components/Header";
import { OutcomeBadge, ProvenanceBadge, DataProvenanceNotice } from "../components/Badge";
import { LoadingState, ErrorState, EmptyState } from "../components/LoadingState";
import ProbabilityChart from "../components/ProbabilityChart";
import TransactionTimeline from "../components/TransactionTimeline";
import FlowGraph from "../components/FlowGraph";
import ShapBars from "../components/ShapBars";
import { AADAPT_TECHNIQUES } from "../aadapt";
import { useIncidentDetail, useIncidentList } from "../hooks";
import { useTheta } from "../ThetaContext";
import { classifyIncident } from "../classify";

type Tab = "overview" | "timeline" | "flow" | "shap" | "aadapt";
const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "timeline", label: "Transaction Timeline" },
  { id: "flow", label: "Flow Graph" },
  { id: "shap", label: "Explainability (SHAP)" },
  { id: "aadapt", label: "AADAPT" },
];

export default function InvestigationPage() {
  const { incidentId } = useParams();
  const navigate = useNavigate();
  const { data: list } = useIncidentList();
  const { theta, model } = useTheta();
  const [tab, setTab] = useState<Tab>("overview");

  const effectiveId = incidentId ?? list?.[0]?.incident_id;
  const { data: incident, isLoading, isError } = useIncidentDetail(effectiveId);

  if (!effectiveId) {
    return (
      <div>
        <Header title="Investigation" />
        <div className="p-8">
          <EmptyState message="Chưa có incident nào được chọn. Vào Incidents để chọn 1 case." />
        </div>
      </div>
    );
  }
  if (isLoading) return <div><Header title="Investigation" /><div className="p-8"><LoadingState /></div></div>;
  if (isError || !incident) return <div><Header title="Investigation" /><div className="p-8"><ErrorState message="Không tải được chi tiết incident." /></div></div>;

  const classification = classifyIncident(incident, theta, model);
  const alertPoint = incident.prefix_points.find((p) => p.k === classification.firstAlertK);
  const alertProb = model === "m1_cal" ? alertPoint?.m1_cal : alertPoint?.b3_cal;
  const shapForAlert = alertPoint ? (model === "m1_cal" ? alertPoint.m1_top_shap : alertPoint.b3_top_shap) : [];
  const exitAction = incident.actions.find((a) => a.idx === incident.e_star);

  return (
    <div>
      <Header title={incident.incident_id} subtitle={incident.name} />
      <div className="p-8 space-y-5">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3 flex-wrap">
            <select
              value={effectiveId}
              onChange={(e) => navigate(`/investigation/${e.target.value}`)}
              className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-text"
            >
              {list?.map((i) => (
                <option key={i.incident_id} value={i.incident_id}>{i.incident_id}</option>
              ))}
            </select>
            <span className="text-xs uppercase text-textSecondary bg-elevated px-2.5 py-1 rounded-md border border-border">
              {incident.chain}
            </span>
            <span className="font-mono text-xs text-textSecondary bg-elevated px-2.5 py-1 rounded-md border border-border flex items-center gap-1">
              {incident.seed_address?.slice(0, 10)}...
              <Copy size={11} className="cursor-pointer" onClick={() => navigator.clipboard.writeText(incident.seed_address)} />
            </span>
            <ProvenanceBadge />
          </div>
          <OutcomeBadge outcome={classification.outcome} />
        </div>

        <DataProvenanceNotice />

        <div className="flex gap-1 border-b border-border">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
                tab === t.id ? "border-accent text-accent" : "border-transparent text-textSecondary hover:text-text"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === "overview" && (
          <div className="space-y-5">
            <ProbabilityChart
              points={incident.prefix_points}
              theta={theta}
              eStar={incident.e_star}
              firstAlertK={classification.firstAlertK}
            />
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <SummaryCard
                icon={AlertTriangle}
                label="First Alert"
                value={classification.firstAlertK !== null ? `k = ${classification.firstAlertK}` : "—"}
                sub={
                  classification.firstAlertK !== null
                    ? `p̂=${alertProb?.toFixed(3)} (θ=${theta})`
                    : classification.outcome === "not_feasible"
                    ? "Không có prefix trước exit"
                    : classification.outcome === "not_evaluable"
                    ? "Chưa xác nhận endpoint"
                    : "Không vượt ngưỡng"
                }
                color="#FF5267"
              />
              <SummaryCard
                icon={LogOut}
                label="Exit Point"
                value={incident.e_star !== null ? `k = ${incident.e_star}` : "N/A"}
                sub={exitAction ? `${exitAction.event_type}${exitAction.protocol ? " · " + exitAction.protocol : ""}` : "Chưa xác nhận endpoint"}
                color="#1C9BFF"
              />
              <SummaryCard
                icon={Clock}
                label="Lead Time"
                value={
                  classification.leadTimeHours !== null
                    ? `${classification.leadTimeHours >= 0 ? "+" : ""}${classification.leadTimeHours.toFixed(2)} h`
                    : "N/A"
                }
                sub={
                  classification.leadTimeHours === null
                    ? classification.outcome === "no_alert"
                      ? "Không có alert để tính"
                      : classification.outcome === "not_feasible"
                      ? "e* ≤ 2 — không có prefix trước exit để tính lead time"
                      : classification.outcome === "not_evaluable"
                      ? "Chưa xác nhận endpoint"
                      : "Không có exit quan sát được"
                    : classification.leadTimeHours >= 0
                    ? "Phát hiện trước exit"
                    : "Phát hiện sau exit"
                }
                color="#18D6A3"
              />
              <SummaryCard
                icon={Tag}
                label="AADAPT (top SHAP)"
                value={shapForAlert[0]?.aadapt_ids[0] ?? "—"}
                sub={shapForAlert[0]?.aadapt_ids[0] ? AADAPT_TECHNIQUES[shapForAlert[0].aadapt_ids[0]]?.name : "Chưa có alert/SHAP"}
                color="#FFBA36"
              />
            </div>
          </div>
        )}

        {tab === "timeline" && (
          <TransactionTimeline actions={incident.actions} chain={incident.chain} eStar={incident.e_star} firstAlertK={classification.firstAlertK} />
        )}

        {tab === "flow" && (
          <FlowGraph actions={incident.actions} eStar={incident.e_star} firstAlertK={classification.firstAlertK} />
        )}

        {tab === "shap" && (
          <div className="bg-card border border-border rounded-xl p-5">
            <h3 className="text-sm font-semibold text-text mb-1">
              Top-3 TreeSHAP {classification.firstAlertK !== null ? `(tại k=${classification.firstAlertK}, điểm alert đầu tiên)` : "(chưa có alert)"}
            </h3>
            <p className="text-xs text-textSecondary mb-4">Model fold-specific (out-of-fold), không dùng model đã đóng băng.</p>
            {classification.firstAlertK === null ? (
              <EmptyState message="Không có alert nào để giải thích (xem lý do ở tab Overview)." />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <ShapBars contributions={alertPoint?.m1_top_shap ?? []} title="M1 (Ours)" />
                <ShapBars contributions={alertPoint?.b3_top_shap ?? []} title="B3' (Baseline)" />
              </div>
            )}
          </div>
        )}

        {tab === "aadapt" && (
          <div className="bg-card border border-border rounded-xl p-5">
            <h3 className="text-sm font-semibold text-text mb-4">AADAPT Technique Mapping (tại điểm alert)</h3>
            {classification.firstAlertK === null ? (
              <EmptyState message="Không có alert để ánh xạ AADAPT." />
            ) : (
              <div className="space-y-3">
                {(shapForAlert ?? []).flatMap((s) => s.aadapt_ids).length === 0 ? (
                  <EmptyState message="Top-3 feature SHAP tại điểm alert không map được AADAPT ID nào." />
                ) : (
                  Array.from(new Set(shapForAlert.flatMap((s) => s.aadapt_ids))).map((id) => (
                    <div key={id} className="border border-border rounded-lg p-4 bg-elevated">
                      <div className="flex items-center gap-2">
                        <span className="text-accent2 font-mono text-sm font-semibold">{id}</span>
                        <span className="text-text text-sm">{AADAPT_TECHNIQUES[id]?.name}</span>
                      </div>
                      <p className="text-xs text-textSecondary mt-1">
                        Mapped behavior: {AADAPT_TECHNIQUES[id]?.observable}
                      </p>
                      <p className="text-xs text-textSecondary mt-1">
                        Supporting feature(s): {shapForAlert.filter((s) => s.aadapt_ids.includes(id)).map((s) => s.feature).join(", ")}
                      </p>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function SummaryCard({ icon: Icon, label, value, sub, color }: { icon: any; label: string; value: string; sub: string; color: string }) {
  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="flex items-center gap-2 text-xs text-textSecondary mb-2">
        <Icon size={14} style={{ color }} />
        {label}
      </div>
      <div className="text-lg font-semibold text-text">{value}</div>
      <div className="text-xs text-textSecondary mt-0.5">{sub}</div>
    </div>
  );
}
