import { Loader2, AlertTriangle } from "lucide-react";

export function LoadingState({ label = "Đang tải dữ liệu..." }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-20 text-textSecondary">
      <Loader2 className="animate-spin" size={18} />
      {label}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-20 text-danger">
      <AlertTriangle size={24} />
      <div className="text-sm max-w-md text-center">{message}</div>
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-16 text-textSecondary border border-dashed border-border rounded-lg">
      <div className="text-sm max-w-md text-center">{message}</div>
    </div>
  );
}
