import { Activity, BarChart3, Database, Server } from "lucide-react";
import type { DesktopDiagnostics } from "../types/desktop";

interface DesktopStatusStripProps {
  diagnostics: DesktopDiagnostics | null;
}

export function DesktopStatusStrip({ diagnostics }: DesktopStatusStripProps) {
  if (!diagnostics?.desktop_mode) {
    return null;
  }

  const items = [
    { label: "Local backend", value: `:${diagnostics.backend_port}`, icon: Server },
    { label: "Database", value: diagnostics.database_ok ? "OK" : "Check", icon: Database },
    { label: "Polling", value: "Local", icon: Activity },
    { label: "Analytics", value: "Local", icon: BarChart3 },
  ];

  return (
    <div className="hidden items-center gap-2 lg:flex">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <div key={item.label} className="flex h-8 items-center gap-1.5 rounded-md border border-border bg-background px-2 text-xs text-muted-foreground">
            <Icon className="h-3.5 w-3.5 text-primary" />
            <span>{item.label}</span>
            <span className="font-medium text-foreground">{item.value}</span>
          </div>
        );
      })}
    </div>
  );
}
