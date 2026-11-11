import type { Outcome } from "../types";
import { OUTCOME_LABEL, OUTCOME_COLOR } from "../classify";

export function OutcomeBadge({ outcome }: { outcome: Outcome }) {
  const color = OUTCOME_COLOR[outcome];
  return (
    <span
      className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold border"
      style={{ color, borderColor: color + "55", backgroundColor: color + "15" }}
    >
      {OUTCOME_LABEL[outcome]}
    </span>
  );
}

export function ProvenanceBadge() {
  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-accent2/15 text-accent2 border border-accent2/40">
      Trong tập dữ liệu (out-of-fold)
    </span>
  );
}

export function DataProvenanceNotice() {
  return (
    <div className="flex items-center gap-2 px-4 py-2.5 rounded-md bg-elevated border border-border text-xs text-textSecondary">
      Phân tích trên lịch sử giao dịch của seed, không phải giám sát thời
      gian thực.
    </div>
  );
}
