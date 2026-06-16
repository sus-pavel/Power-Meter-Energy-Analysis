import { AlertTriangle, CheckCircle2, Clock, Gauge, HelpCircle, Server, WifiOff } from "lucide-react";
import type { OperationsStatus } from "../types/operations";
import { StatusCard } from "./StatusCard";

export function OperationalStatusCards({ status }: { status: OperationsStatus }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-7">
      <StatusCard label="Configured Devices" value={status.configured_devices} icon={<Server className="h-5 w-5" />} />
      <StatusCard label="Enabled Devices" value={status.enabled_devices} icon={<CheckCircle2 className="h-5 w-5" />} />
      <StatusCard label="Online" value={status.online_devices} icon={<Gauge className="h-5 w-5" />} />
      <StatusCard label="Offline" value={status.offline_devices} icon={<WifiOff className="h-5 w-5" />} />
      <StatusCard label="Unknown" value={status.unknown_devices} icon={<HelpCircle className="h-5 w-5" />} />
      <StatusCard label="Pending Candidates" value={status.pending_candidates} icon={<AlertTriangle className="h-5 w-5" />} />
      <StatusCard label="Recent Measurements" value={status.recent_measurements_available ? "Yes" : "No"} icon={<Clock className="h-5 w-5" />} />
    </div>
  );
}
