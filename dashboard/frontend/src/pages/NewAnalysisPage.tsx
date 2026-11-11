import { PlayCircle } from "lucide-react";
import Header from "../components/Header";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

export default function NewAnalysisPage() {
  const { data } = useQuery({ queryKey: ["new-analysis"], queryFn: api.getNewAnalysisStatus });
  return (
    <div>
      <Header title="New Analysis" subtitle="Phân tích incident hoàn toàn mới (Phần 2)" />
      <div className="p-8">
        <div className="bg-card border border-dashed border-border rounded-xl p-10 flex flex-col items-center gap-3 text-center">
          <PlayCircle size={32} className="text-textSecondary" />
          <h2 className="text-text font-medium">Chưa được bật trong bản build này</h2>
          <p className="text-sm text-textSecondary max-w-md">
            {data?.message ?? "Tính năng này thuộc Phần 2 của dự án — sẽ dùng model đã đóng băng (M1_FROZEN_final_N36 / B3prime_FROZEN_final_N36) để dự đoán incident hoàn toàn mới, qua API đã thiết kế sẵn ở /api/new-analysis."}
          </p>
        </div>
      </div>
    </div>
  );
}
