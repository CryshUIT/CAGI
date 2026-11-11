import { useState } from "react";
import { ArrowRightLeft, Download, GitMerge, Split, ArrowRight, Repeat, Landmark, ShieldOff, HelpCircle } from "lucide-react";
import type { ActionEvent } from "../types";
import { EmptyState } from "./LoadingState";

const ICONS: Record<string, any> = {
  transfer: ArrowRightLeft,
  swap: Repeat,
  split: Split,
  merge: GitMerge,
  bridge_deposit: ArrowRight,
  bridge_withdraw: ArrowRight,
  lending_deposit: Landmark,
  lending_withdraw: Landmark,
  mixer_or_exit: ShieldOff,
};

function IconFor({ type }: { type: string }) {
  const Icon = ICONS[type] ?? HelpCircle;
  return <Icon size={15} />;
}

const EXPLORER: Record<string, string> = {
  eth: "https://etherscan.io/tx/",
  bsc: "https://bscscan.com/tx/",
  arbitrum: "https://arbiscan.io/tx/",
};

export default function TransactionTimeline({
  actions,
  chain,
  eStar,
  firstAlertK,
}: {
  actions: ActionEvent[];
  chain: string;
  eStar: number | null;
  firstAlertK: number | null;
}) {
  const [selected, setSelected] = useState<ActionEvent | null>(null);

  if (actions.length === 0) {
    return <EmptyState message="Không có dữ liệu trace cho incident này." />;
  }

  return (
    <div className="bg-card border border-border rounded-xl p-5">
      <h3 className="text-sm font-semibold text-text mb-4">Transaction Timeline ({actions.length} action)</h3>
      <div className="overflow-x-auto">
        <div className="flex items-stretch gap-0 min-w-max pb-2">
          {actions.map((a, idx) => {
            const isAlert = a.idx === firstAlertK;
            const isExit = a.idx === eStar;
            return (
              <div key={a.idx} className="flex items-center">
                <button
                  onClick={() => setSelected(a)}
                  className={`flex flex-col items-center gap-1.5 px-3 py-2 rounded-lg border min-w-[92px] transition-colors ${
                    isExit
                      ? "border-danger bg-danger/10"
                      : isAlert
                      ? "border-accent bg-accent/10"
                      : "border-border bg-elevated hover:bg-elevated/70"
                  }`}
                  title={a.event_type}
                >
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center"
                    style={{
                      color: isExit ? "#FF5267" : isAlert ? "#00D4F5" : "#93A9C4",
                      backgroundColor: (isExit ? "#FF5267" : isAlert ? "#00D4F5" : "#93A9C4") + "22",
                    }}
                  >
                    <IconFor type={a.event_type} />
                  </div>
                  <span className="text-[10px] text-textSecondary">k={a.idx}</span>
                  <span className="text-[10px] text-text font-medium truncate max-w-[80px]">{a.event_type}</span>
                  {isAlert && <span className="text-[9px] text-accent font-semibold">ALERT</span>}
                  {isExit && <span className="text-[9px] text-danger font-semibold">EXIT</span>}
                </button>
                {idx < actions.length - 1 && <div className="w-5 h-px bg-border" />}
              </div>
            );
          })}
        </div>
      </div>

      {selected && (
        <div className="mt-4 border-t border-border pt-4 text-sm space-y-1.5">
          <div className="flex justify-between"><span className="text-textSecondary">Action #</span><span>{selected.idx} — {selected.event_type}</span></div>
          <div className="flex justify-between"><span className="text-textSecondary">Timestamp</span><span>{selected.timestamp}</span></div>
          <div className="flex justify-between"><span className="text-textSecondary">From</span><span className="font-mono">{selected.src}</span></div>
          <div className="flex justify-between"><span className="text-textSecondary">To</span><span className="font-mono">{selected.dst}</span></div>
          <div className="flex justify-between"><span className="text-textSecondary">Token</span><span>{selected.token ?? "—"}</span></div>
          <div className="flex justify-between"><span className="text-textSecondary">Protocol</span><span>{selected.protocol ?? "—"}</span></div>
          {selected.tx_hash && (
            <div className="flex justify-between">
              <span className="text-textSecondary">Tx hash</span>
              <a
                className="text-accent hover:underline flex items-center gap-1 font-mono"
                href={`${EXPLORER[chain] ?? EXPLORER.eth}${selected.tx_hash}`}
                target="_blank" rel="noreferrer"
              >
                {selected.tx_hash.slice(0, 18)}... <Download size={12} />
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
