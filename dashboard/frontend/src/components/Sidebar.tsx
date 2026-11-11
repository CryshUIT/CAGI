import { NavLink } from "react-router-dom";
import { LayoutDashboard, List, PlayCircle, Search, BarChart3, Settings, ShieldHalf } from "lucide-react";

const items = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/incidents", label: "Incidents", icon: List },
  { to: "/new-analysis", label: "New Analysis", icon: PlayCircle },
  { to: "/investigation", label: "Investigation", icon: Search },
  { to: "/explainability", label: "Explainability", icon: BarChart3 },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 bg-sidebar border-r border-border flex flex-col">
      <div className="flex items-center gap-2 px-5 py-5 border-b border-border">
        <ShieldHalf className="text-accent" size={26} />
        <div>
          <div className="font-semibold text-text leading-tight">CAGI-ED</div>
          <div className="text-[11px] text-textSecondary leading-tight">
            Cross-Chain Attack
            <br />
            Detection for DeFi
          </div>
        </div>
      </div>
      <nav className="flex-1 py-3">
        {items.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 mx-2 my-1 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? "bg-elevated text-accent border border-border"
                  : "text-textSecondary hover:bg-elevated/60 hover:text-text"
              }`
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-4 py-4 border-t border-border text-[11px] text-textSecondary leading-snug">
        <span className="font-medium text-text">Research Demo</span>
        <br />
        CPU only · No real-time monitoring.
        <br />
        Phân tích trên lịch sử giao dịch của seed, không phải giám sát
        thời gian thực.
      </div>
    </aside>
  );
}
