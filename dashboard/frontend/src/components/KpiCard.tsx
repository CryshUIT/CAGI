import type { LucideIcon } from "lucide-react";

export default function KpiCard({
  icon: Icon,
  label,
  value,
  accentColor,
}: {
  icon: LucideIcon;
  label: string;
  value: string | number;
  accentColor?: string;
}) {
  return (
    <div className="flex items-center gap-3 bg-card border border-border rounded-xl px-5 py-4 flex-1 min-w-[170px]">
      <div
        className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
        style={{ backgroundColor: (accentColor ?? "#1C9BFF") + "22", color: accentColor ?? "#1C9BFF" }}
      >
        <Icon size={19} />
      </div>
      <div>
        <div className="text-xs text-textSecondary">{label}</div>
        <div className="text-xl font-semibold text-text leading-tight">{value}</div>
      </div>
    </div>
  );
}
