import { FormEvent, useEffect, useState } from "react";
import { Edit, Plus, Trash2 } from "lucide-react";
import type { RegisterMapEntry, RegisterPayload } from "../types/device";

const EMPTY_REGISTER: RegisterPayload = {
  metric: "",
  function_code: "holding",
  address: 40001,
  data_type: "float32",
  scale: 1,
  unit: "",
  description: "",
  enabled: true
};

interface RegisterMapTableProps {
  registers: RegisterMapEntry[];
  canManage: boolean;
  onCreate: (payload: RegisterPayload) => void;
  onUpdate: (registerId: number, payload: Partial<RegisterPayload>) => void;
  onDelete: (registerId: number) => void;
}

export function RegisterMapTable({ registers, canManage, onCreate, onUpdate, onDelete }: RegisterMapTableProps) {
  const [editing, setEditing] = useState<RegisterMapEntry | null>(null);
  const [form, setForm] = useState<RegisterPayload>(EMPTY_REGISTER);

  useEffect(() => {
    if (editing) {
      setForm({
        metric: editing.metric,
        function_code: editing.function_code,
        address: editing.address,
        data_type: editing.data_type,
        scale: editing.scale,
        unit: editing.unit ?? "",
        description: editing.description ?? "",
        enabled: editing.enabled
      });
    }
  }, [editing]);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (editing) {
      onUpdate(editing.id, form);
      setEditing(null);
    } else {
      onCreate(form);
    }
    setForm(EMPTY_REGISTER);
  }

  return (
    <div className="space-y-4">
      {canManage ? (
        <form onSubmit={submit} className="rounded-md border border-border bg-card p-4">
          <div className="grid gap-3 lg:grid-cols-4">
            <input placeholder="Metric" className="h-9 rounded-md border border-border px-3 text-sm" value={form.metric} onChange={(e) => setForm({ ...form, metric: e.target.value })} />
            <input placeholder="Function" className="h-9 rounded-md border border-border px-3 text-sm" value={form.function_code} onChange={(e) => setForm({ ...form, function_code: e.target.value })} />
            <input type="number" placeholder="Address" className="h-9 rounded-md border border-border px-3 text-sm" value={form.address} onChange={(e) => setForm({ ...form, address: Number(e.target.value) })} />
            <input placeholder="Data Type" className="h-9 rounded-md border border-border px-3 text-sm" value={form.data_type} onChange={(e) => setForm({ ...form, data_type: e.target.value })} />
            <input type="number" step="0.01" placeholder="Scale" className="h-9 rounded-md border border-border px-3 text-sm" value={form.scale} onChange={(e) => setForm({ ...form, scale: Number(e.target.value) })} />
            <input placeholder="Unit" className="h-9 rounded-md border border-border px-3 text-sm" value={form.unit ?? ""} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
            <input placeholder="Description" className="h-9 rounded-md border border-border px-3 text-sm" value={form.description ?? ""} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.enabled} onChange={(e) => setForm({ ...form, enabled: e.target.checked })} /> Enabled</label>
          </div>
          <button type="submit" className="mt-3 inline-flex h-9 items-center rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground">
            <Plus className="mr-2 h-4 w-4" />{editing ? "Update Register" : "Add Register"}
          </button>
          {editing ? <button type="button" className="ml-2 h-9 rounded-md border border-border px-3 text-sm" onClick={() => { setEditing(null); setForm(EMPTY_REGISTER); }}>Cancel</button> : null}
        </form>
      ) : null}
      <div className="overflow-hidden rounded-md border border-border bg-card">
        <table className="w-full min-w-[860px] text-left text-sm">
          <thead className="bg-muted text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-3 py-2">Metric</th>
              <th className="px-3 py-2">Function</th>
              <th className="px-3 py-2">Address</th>
              <th className="px-3 py-2">Data Type</th>
              <th className="px-3 py-2">Scale</th>
              <th className="px-3 py-2">Unit</th>
              <th className="px-3 py-2">Enabled</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {registers.map((register) => (
              <tr key={register.id}>
                <td className="px-3 py-2 font-medium">{register.metric}</td>
                <td className="px-3 py-2">{register.function_code}</td>
                <td className="px-3 py-2">{register.address}</td>
                <td className="px-3 py-2">{register.data_type}</td>
                <td className="px-3 py-2">{register.scale}</td>
                <td className="px-3 py-2">{register.unit ?? "-"}</td>
                <td className="px-3 py-2">{register.enabled ? "Yes" : "No"}</td>
                <td className="px-3 py-2">
                  {canManage ? (
                    <div className="flex gap-1">
                      <button className="rounded-md border border-border p-2 hover:bg-muted" onClick={() => setEditing(register)}><Edit className="h-4 w-4" /></button>
                      <button className="rounded-md border border-border p-2 text-red-700 hover:bg-red-50" onClick={() => onDelete(register.id)}><Trash2 className="h-4 w-4" /></button>
                    </div>
                  ) : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
