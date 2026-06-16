import { Link } from "react-router-dom";
import type { OperationalDevice } from "../types/operations";
import { LastSeenIndicator } from "./LastSeenIndicator";
import { OperationalStatusBadge } from "./StatusBadge";

export function DeviceStatusTable({ devices, showReadiness = false }: { devices: OperationalDevice[]; showReadiness?: boolean }) {
  return (
    <div className="overflow-hidden rounded-md border border-border bg-card">
      <table className="w-full min-w-[980px] text-left text-sm">
        <thead className="bg-muted text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2">Name</th>
            <th className="px-3 py-2">Host</th>
            <th className="px-3 py-2">Unit ID</th>
            <th className="px-3 py-2">Enabled</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Last Seen</th>
            <th className="px-3 py-2">Registers</th>
            {showReadiness ? <th className="px-3 py-2">Polling Readiness</th> : null}
            <th className="px-3 py-2">Last Error</th>
            <th className="px-3 py-2">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {devices.map((device) => (
            <tr key={device.id} className="hover:bg-muted/40">
              <td className="px-3 py-2 font-medium">{device.name}</td>
              <td className="px-3 py-2">{device.host}:{device.port}</td>
              <td className="px-3 py-2">{device.unit_id}</td>
              <td className="px-3 py-2">{device.enabled ? "Yes" : "No"}</td>
              <td className="px-3 py-2"><OperationalStatusBadge value={device.status} /></td>
              <td className="px-3 py-2"><LastSeenIndicator value={device.last_seen_at} /></td>
              <td className="px-3 py-2">{device.registers_enabled}</td>
              {showReadiness ? <td className="px-3 py-2"><OperationalStatusBadge value={device.polling_readiness} /></td> : null}
              <td className="px-3 py-2">{device.last_error ?? "-"}</td>
              <td className="px-3 py-2"><Link className="rounded-md border border-border px-2 py-1 hover:bg-muted" to={`/devices/${device.id}`}>View Device</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
