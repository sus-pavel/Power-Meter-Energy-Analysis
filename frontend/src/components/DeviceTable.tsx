import { Link } from "react-router-dom";
import { Edit, Eye, Trash2 } from "lucide-react";
import type { Device } from "../types/device";

interface DeviceTableProps {
  devices: Device[];
  canManage: boolean;
  onDelete: (device: Device) => void;
}

export function DeviceTable({ devices, canManage, onDelete }: DeviceTableProps) {
  return (
    <div className="overflow-hidden rounded-md border border-border bg-card">
      <table className="w-full min-w-[860px] text-left text-sm">
        <thead className="bg-muted text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2">Name</th>
            <th className="px-3 py-2">Host</th>
            <th className="px-3 py-2">Port</th>
            <th className="px-3 py-2">Unit ID</th>
            <th className="px-3 py-2">Location</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Created</th>
            <th className="px-3 py-2">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {devices.map((device) => (
            <tr key={device.id} className="hover:bg-muted/40">
              <td className="px-3 py-2 font-medium">{device.name}</td>
              <td className="px-3 py-2">{device.host}</td>
              <td className="px-3 py-2">{device.port}</td>
              <td className="px-3 py-2">{device.unit_id}</td>
              <td className="px-3 py-2">{device.location ?? "-"}</td>
              <td className="px-3 py-2">{device.enabled ? "Enabled" : "Disabled"}</td>
              <td className="px-3 py-2">{new Date(device.created_at).toLocaleString()}</td>
              <td className="px-3 py-2">
                <div className="flex gap-1">
                  <Link className="rounded-md border border-border p-2 hover:bg-muted" to={`/devices/${device.id}`} title="View"><Eye className="h-4 w-4" /></Link>
                  {canManage ? <Link className="rounded-md border border-border p-2 hover:bg-muted" to={`/devices/${device.id}`} title="Edit"><Edit className="h-4 w-4" /></Link> : null}
                  {canManage ? <button className="rounded-md border border-border p-2 text-red-700 hover:bg-red-50" onClick={() => onDelete(device)} title="Delete"><Trash2 className="h-4 w-4" /></button> : null}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
