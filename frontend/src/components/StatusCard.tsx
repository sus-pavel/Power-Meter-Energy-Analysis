import type { ReactNode } from "react";

interface StatusCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  detail?: string;
}

export function StatusCard({ label, value, icon, detail }: StatusCardProps) {
  return (
    <div className="rounded-md border border-border bg-card p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
          <p className="mt-2 text-2xl font-semibold text-foreground">{value}</p>
        </div>
        {icon ? <div className="text-primary">{icon}</div> : null}
      </div>
      {detail ? <p className="mt-2 text-sm text-muted-foreground">{detail}</p> : null}
    </div>
  );
}
