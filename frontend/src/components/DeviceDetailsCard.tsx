import { FormEvent, useEffect, useState } from "react";
import type { Device, DeviceUpdatePayload } from "../types/device";

interface DeviceDetailsCardProps {
  device: Device;
  canManage: boolean;
  onSave: (payload: DeviceUpdatePayload) => void;
  saving?: boolean;
}

export function DeviceDetailsCard({ device, canManage, onSave, saving }: DeviceDetailsCardProps) {
  const [name, setName] = useState(device.name);
  const [location, setLocation] = useState(device.location ?? "");
  const [description, setDescription] = useState(device.description ?? "");
  const [enabled, setEnabled] = useState(device.enabled);
  const [pollInterval, setPollInterval] = useState(device.poll_interval_sec);

  useEffect(() => {
    setName(device.name);
    setLocation(device.location ?? "");
    setDescription(device.description ?? "");
    setEnabled(device.enabled);
    setPollInterval(device.poll_interval_sec);
  }, [device]);

  function submit(event: FormEvent) {
    event.preventDefault();
    onSave({ name, location, description, enabled, poll_interval_sec: pollInterval });
  }

  return (
    <form onSubmit={submit} className="rounded-md border border-border bg-card p-4">
      <div className="grid gap-4 lg:grid-cols-3">
        <label className="text-sm font-medium">Name<input disabled={!canManage} className="mt-1 h-9 w-full rounded-md border border-border px-3 disabled:bg-muted" value={name} onChange={(e) => setName(e.target.value)} /></label>
        <label className="text-sm font-medium">Location<input disabled={!canManage} className="mt-1 h-9 w-full rounded-md border border-border px-3 disabled:bg-muted" value={location} onChange={(e) => setLocation(e.target.value)} /></label>
        <label className="flex items-end gap-2 text-sm font-medium"><input disabled={!canManage} type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} /> Enabled</label>
        <div className="text-sm"><span className="text-muted-foreground">Host</span><p className="font-medium">{device.host}</p></div>
        <div className="text-sm"><span className="text-muted-foreground">Port</span><p className="font-medium">{device.port}</p></div>
        <div className="text-sm"><span className="text-muted-foreground">Unit ID</span><p className="font-medium">{device.unit_id}</p></div>
        <label className="text-sm font-medium">
          Polling Interval
          <select disabled={!canManage} className="mt-1 h-9 w-full rounded-md border border-border px-3 disabled:bg-muted" value={pollInterval} onChange={(e) => setPollInterval(Number(e.target.value))}>
            {[10, 30, 60, 300, 600].map((value) => <option key={value} value={value}>{value} sec</option>)}
          </select>
        </label>
      </div>
      <label className="mt-4 block text-sm font-medium">Description<textarea disabled={!canManage} className="mt-1 min-h-20 w-full rounded-md border border-border px-3 py-2 disabled:bg-muted" value={description} onChange={(e) => setDescription(e.target.value)} /></label>
      {canManage ? <button disabled={saving} className="mt-4 h-9 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground disabled:opacity-60" type="submit">Save Device</button> : null}
    </form>
  );
}
