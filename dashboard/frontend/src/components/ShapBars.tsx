import type { ShapContribution } from "../types";
import { EmptyState } from "./LoadingState";

export default function ShapBars({ contributions, title }: { contributions: ShapContribution[]; title: string }) {
  if (!contributions || contributions.length === 0) {
    return (
      <div>
        <h4 className="text-xs font-semibold text-textSecondary mb-2 uppercase tracking-wide">{title}</h4>
        <EmptyState message="Không có dữ liệu SHAP tại prefix này (không khớp 1 dòng OOF, hoặc fold model không dùng XGBoost)." />
      </div>
    );
  }
  const maxAbs = Math.max(...contributions.map((c) => Math.abs(c.contribution)), 0.001);
  return (
    <div>
      <h4 className="text-xs font-semibold text-textSecondary mb-2 uppercase tracking-wide">{title}</h4>
      <div className="space-y-2.5">
        {contributions.map((c) => {
          const pct = (Math.abs(c.contribution) / maxAbs) * 100;
          const positive = c.contribution >= 0;
          return (
            <div key={c.feature}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-text font-mono">{c.feature}</span>
                <span className={positive ? "text-danger" : "text-accent"}>
                  {c.contribution >= 0 ? "+" : ""}
                  {c.contribution.toFixed(4)}
                </span>
              </div>
              <div className="h-2 rounded-full bg-elevated overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{ width: `${pct}%`, backgroundColor: positive ? "#FF5267" : "#00D4F5" }}
                />
              </div>
              {c.aadapt_ids.length > 0 && (
                <div className="mt-1 flex gap-1 flex-wrap">
                  {c.aadapt_ids.map((id) => (
                    <span key={id} className="text-[10px] px-1.5 py-0.5 rounded bg-accent2/15 text-accent2 border border-accent2/30">
                      {id}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
