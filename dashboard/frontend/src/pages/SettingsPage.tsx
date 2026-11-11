import Header from "../components/Header";
import { useTheta } from "../ThetaContext";
import { useMeta } from "../hooks";

export default function SettingsPage() {
  const { theta, setTheta, model, setModel } = useTheta();
  const { data: meta } = useMeta();

  return (
    <div>
      <Header title="Settings" subtitle="Chỉ các tùy chọn có tác dụng thật" />
      <div className="p-8 max-w-xl space-y-6">
        <div className="bg-card border border-border rounded-xl p-5 space-y-4">
          <div>
            <label className="text-sm text-text font-medium block mb-1">Default model</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value as "m1_cal" | "b3_cal")}
              className="bg-elevated border border-border rounded-md px-3 py-2 text-sm text-text w-full"
            >
              <option value="m1_cal">M1 (Ours)</option>
              <option value="b3_cal">B3' (Baseline)</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-text font-medium block mb-1">Default θ (threshold)</label>
            <input
              type="number"
              step={0.01}
              min={0}
              max={1}
              value={theta}
              onChange={(e) => setTheta(Number(e.target.value))}
              className="bg-elevated border border-border rounded-md px-3 py-2 text-sm text-text w-full"
            />
          </div>
          {meta && (
            <p className="text-xs text-textSecondary border-t border-border pt-3">
              θ_frozen đã dùng khi đóng băng model: M1={meta.m1_theta_oof}, B3'={meta.b3_theta_oof}
              <br />
              (out-of-fold, target_fpr={meta.target_fpr}, seed={meta.seed})
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
