import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search } from "lucide-react";
import Header from "../components/Header";
import { OutcomeBadge } from "../components/Badge";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { useClassifiedIncidents } from "../hooks";
import type { Outcome } from "../types";

const CHAINS = ["eth", "bsc", "arbitrum"];
const OUTCOMES: Outcome[] = ["early", "late", "not_feasible", "no_alert", "not_evaluable"];

export default function IncidentsPage() {
  const { data: incidents, isLoading, isError } = useClassifiedIncidents();
  const [search, setSearch] = useState("");
  const [chainFilter, setChainFilter] = useState<string | null>(null);
  const [outcomeFilter, setOutcomeFilter] = useState<Outcome | null>(null);
  const navigate = useNavigate();

  const filtered = useMemo(() => {
    return incidents.filter((i) => {
      if (search && !i.incident_id.toLowerCase().includes(search.toLowerCase()) && !i.name.toLowerCase().includes(search.toLowerCase())) return false;
      if (chainFilter && i.chain !== chainFilter) return false;
      if (outcomeFilter && i.outcome !== outcomeFilter) return false;
      return true;
    });
  }, [incidents, search, chainFilter, outcomeFilter]);

  return (
    <div>
      <Header title="Incidents" subtitle={`${incidents.length} incident trong tập out-of-fold (N=36)`} />
      <div className="p-8 space-y-5">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 bg-card border border-border rounded-lg px-3 py-2 w-72">
            <Search size={15} className="text-textSecondary" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm incident..."
              className="bg-transparent outline-none text-sm text-text placeholder:text-textSecondary w-full"
            />
          </div>
          <select
            value={chainFilter ?? ""}
            onChange={(e) => setChainFilter(e.target.value || null)}
            className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-text"
          >
            <option value="">Mọi chain</option>
            {CHAINS.map((c) => (
              <option key={c} value={c}>{c.toUpperCase()}</option>
            ))}
          </select>
          <select
            value={outcomeFilter ?? ""}
            onChange={(e) => setOutcomeFilter((e.target.value || null) as Outcome | null)}
            className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-text"
          >
            <option value="">Mọi kết quả</option>
            {OUTCOMES.map((o) => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>
        </div>

        {isLoading && <LoadingState />}
        {isError && <ErrorState message="Không tải được danh sách incident." />}

        {!isLoading && !isError && (
          <div className="bg-card border border-border rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-textSecondary bg-elevated/50 border-b border-border">
                  <th className="px-4 py-3 font-medium">Incident</th>
                  <th className="px-4 py-3 font-medium">Chain</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                  <th className="px-4 py-3 font-medium">Endpoint confirmed</th>
                  <th className="px-4 py-3 font-medium">Result</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((i) => (
                  <tr
                    key={i.incident_id}
                    onClick={() => navigate(`/investigation/${i.incident_id}`)}
                    className="border-b border-border/50 cursor-pointer hover:bg-elevated/50"
                  >
                    <td className="px-4 py-3 text-text">{i.incident_id}</td>
                    <td className="px-4 py-3 text-textSecondary uppercase text-xs">{i.chain}</td>
                    <td className="px-4 py-3 text-textSecondary">{i.n_actions_total}</td>
                    <td className="px-4 py-3 text-textSecondary">{i.endpoint_confirmed ? "Có" : "Không"}</td>
                    <td className="px-4 py-3"><OutcomeBadge outcome={i.outcome} /></td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-textSecondary">
                      Không có incident khớp bộ lọc.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
