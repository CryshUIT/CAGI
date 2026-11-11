export default function Header({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <header className="flex items-center justify-between px-8 py-5 border-b border-border bg-bg/80 backdrop-blur sticky top-0 z-10">
      <div>
        <h1 className="text-xl font-semibold text-text">{title}</h1>
        {subtitle && <p className="text-sm text-textSecondary mt-0.5">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-2">
        <span className="px-2.5 py-1 rounded-md bg-elevated border border-border text-xs text-accent font-medium">
          Demo
        </span>
        <span className="px-2.5 py-1 rounded-md bg-elevated border border-border text-xs text-textSecondary">
          CAGI-ED v1.0 (Research Demo)
        </span>
      </div>
    </header>
  );
}
