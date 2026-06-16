import { cn } from "./utils";

const STATUS_STYLES: Record<string, string> = {
  running: "border-blue-200 bg-blue-50 text-blue-800",
  pending: "border-slate-200 bg-slate-50 text-slate-700",
  completed: "border-emerald-200 bg-emerald-50 text-emerald-800",
  failed: "border-red-200 bg-red-50 text-red-800",
  cancelled: "border-amber-200 bg-amber-50 text-amber-800",
  discovered: "border-blue-200 bg-blue-50 text-blue-800",
  reviewed: "border-teal-200 bg-teal-50 text-teal-800",
  promoted: "border-emerald-200 bg-emerald-50 text-emerald-800",
  rejected: "border-red-200 bg-red-50 text-red-800"
};

export function StatusBadge({ value }: { value: string }) {
  const label = value.replace(/_/g, " ");
  return (
    <span className={cn("inline-flex rounded-sm border px-2 py-0.5 text-xs font-medium capitalize", STATUS_STYLES[value] ?? "border-border bg-muted text-foreground")}>
      {label}
    </span>
  );
}

export function ConfidenceBadge({ value }: { value: number | null }) {
  if (value === null || value === undefined) {
    return <span className="text-muted-foreground">-</span>;
  }
  const percent = Math.round(value * 100);
  return <span className="font-medium tabular-nums">{percent}%</span>;
}
