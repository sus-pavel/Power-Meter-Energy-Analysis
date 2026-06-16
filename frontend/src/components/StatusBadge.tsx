import type { OperationalDeviceStatus, PollingReadiness } from "../types/operations";
import { cn } from "./utils";

const STATUS_STYLES: Record<OperationalDeviceStatus | PollingReadiness, string> = {
  online: "border-emerald-200 bg-emerald-50 text-emerald-800",
  offline: "border-red-200 bg-red-50 text-red-800",
  unknown: "border-slate-200 bg-slate-50 text-slate-700",
  disabled: "border-zinc-200 bg-zinc-50 text-zinc-700",
  error: "border-red-200 bg-red-50 text-red-800",
  ready: "border-emerald-200 bg-emerald-50 text-emerald-800",
  no_registers: "border-amber-200 bg-amber-50 text-amber-800"
};

export function OperationalStatusBadge({ value }: { value: OperationalDeviceStatus | PollingReadiness }) {
  return (
    <span className={cn("inline-flex rounded-sm border px-2 py-0.5 text-xs font-medium capitalize", STATUS_STYLES[value])}>
      {value.replace(/_/g, " ")}
    </span>
  );
}
