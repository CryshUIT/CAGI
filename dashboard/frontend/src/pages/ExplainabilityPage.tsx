import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { LoadingState, ErrorState, EmptyState } from "../components/LoadingState";
import { useClassifiedIncidents } from "../hooks";
import { useTheta } from "../ThetaContext";
import { AADAPT_TECHNIQUES } from "../aadapt";

export default function ExplainabilityPage() {
  const { data: incidents, isLoading, isError } = useClassifiedIncidents();
  const { model } = useTheta();
  const navigate = useNavigate();

  const aadaptFrequency = useMemo(() => {
    const freq: Record<string, { count: number; incidents: string[] }> = {};
    incidents.forEach((inc) => {
      if (inc.firstAlertK === null) return;
      const point = inc.prefix_points.find((p) => p.k === inc.firstAlertK);
      const shap = point ? (model === "m1_cal" ? point.m1_top_shap : point.b3_top_shap) : [];
      const ids = new Set(shap.flatMap((s) => s.aadapt_ids));
      ids.forEach((id) => {
        if (!freq[id]) freq[id] = { count: 0, incidents: [] };
        freq[id].count++;
        freq[id].incidents.push(inc.incident_id);
      });
    });
    return Object.entries(freq).sort((a, b) => b[1].count - a[1].count);
  }, [incidents, model]);

  return (
    <div>
      <Header title="Explainability" subtitle="Tổng hợp TreeSHAP + AADAPT trên các alert đã phát hiện (out-of-fold)" />
      <div className="p-8 space-y-5">
        {isLoading && <LoadingState />}
        {isError && <ErrorState message="Không tải được dữ liệu explainability." />}
        {!isLoading && !isError && (
          <div className="bg-card border border-border rounded-xl p-5">
            <h3 className="text-sm font-semibold text-text mb-4">
              Tần suất AADAPT technique xuất hiện trong top-3 SHAP tại điểm alert
            </h3>
            {aadaptFrequency.length === 0 ? (
              <EmptyState message="Chưa có alert nào để tổng hợp (hoặc chưa incident nào vượt ngưỡng hiện tại)." />
            ) : (
              <div className="space-y-3">
                {aadaptFrequency.map(([id, info]) => (
                  <div key={id} className="border border-border rounded-lg p-4 bg-elevated">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-accent2 font-mono text-sm font-semibold">{id}</span>
                        <span className="text-text text-sm">{AADAPT_TECHNIQUES[id]?.name}</span>
                      </div>
                      <span className="text-xs text-textSecondary">{info.count} incident</span>
                    </div>
                    <div className="mt-2 flex gap-1.5 flex-wrap">
                      {info.incidents.map((iid) => (
                        <button
                          key={iid}
                          onClick={() => navigate(`/investigation/${iid}`)}
                          className="text-[11px] px-2 py-0.5 rounded bg-card border border-border text-textSecondary hover:text-accent hover:border-accent"
                        >
                          {iid}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
