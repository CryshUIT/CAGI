import { useMemo } from "react";
import ReactFlow, { Background, Controls, type Edge, type Node } from "reactflow";
import "reactflow/dist/style.css";
import type { ActionEvent } from "../types";
import { EmptyState } from "./LoadingState";

function short(addr: string) {
  return addr ? addr.slice(0, 6) + "…" + addr.slice(-4) : addr;
}

export default function FlowGraph({ actions, eStar, firstAlertK }: { actions: ActionEvent[]; eStar: number | null; firstAlertK: number | null }) {
  const { nodes, edges } = useMemo(() => {
    if (actions.length === 0) return { nodes: [], edges: [] };
    const addrSet = new Map<string, number>();
    actions.forEach((a) => {
      if (!addrSet.has(a.src)) addrSet.set(a.src, addrSet.size);
      if (!addrSet.has(a.dst)) addrSet.set(a.dst, addrSet.size);
    });
    const cols = Math.ceil(Math.sqrt(addrSet.size));
    const nodes: Node[] = Array.from(addrSet.entries()).map(([addr], idx) => ({
      id: addr,
      position: { x: (idx % cols) * 220, y: Math.floor(idx / cols) * 110 },
      data: { label: short(addr) },
      style: {
        background: "#11243C",
        color: "#F3F7FC",
        border: "1px solid #203650",
        borderRadius: 8,
        fontSize: 11,
        padding: 6,
        width: 150,
      },
    }));

    const edges: Edge[] = actions.map((a) => {
      const isAlert = a.idx === firstAlertK;
      const isExit = a.idx === eStar;
      const color = isExit ? "#FF5267" : isAlert ? "#00D4F5" : "#203650";
      return {
        id: `e${a.idx}`,
        source: a.src,
        target: a.dst,
        label: `k=${a.idx} ${a.event_type}`,
        animated: isAlert || isExit,
        style: { stroke: color, strokeWidth: isAlert || isExit ? 2 : 1 },
        labelStyle: { fill: "#93A9C4", fontSize: 9 },
        labelBgStyle: { fill: "#0D1B30" },
      };
    });

    return { nodes, edges };
  }, [actions, eStar, firstAlertK]);

  if (nodes.length === 0) {
    return <EmptyState message="Không có dữ liệu trace để vẽ flow graph." />;
  }

  return (
    <div className="bg-card border border-border rounded-xl p-2 h-[480px]">
      <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }}>
        <Background color="#203650" gap={18} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
