import { FormEvent, useState } from "react";
import type { PromoteCandidatePayload } from "../types/candidate";

interface PromotionDialogProps {
  open: boolean;
  defaultName: string;
  onCancel: () => void;
  onSubmit: (payload: PromoteCandidatePayload) => void;
  submitting?: boolean;
}

export function PromotionDialog({ open, defaultName, onCancel, onSubmit, submitting }: PromotionDialogProps) {
  const [deviceName, setDeviceName] = useState(defaultName);
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");

  if (!open) {
    return null;
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    onSubmit({ device_name: deviceName, location, description });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
      <form onSubmit={submit} className="w-full max-w-lg rounded-md border border-border bg-card p-5 shadow-lg">
        <h2 className="text-base font-semibold">Promote Candidate</h2>
        <div className="mt-4 grid gap-3">
          <label className="text-sm font-medium">Device Name<input className="mt-1 h-9 w-full rounded-md border border-border px-3" value={deviceName} onChange={(e) => setDeviceName(e.target.value)} /></label>
          <label className="text-sm font-medium">Location<input className="mt-1 h-9 w-full rounded-md border border-border px-3" value={location} onChange={(e) => setLocation(e.target.value)} /></label>
          <label className="text-sm font-medium">Description<textarea className="mt-1 min-h-20 w-full rounded-md border border-border px-3 py-2" value={description} onChange={(e) => setDescription(e.target.value)} /></label>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button type="button" className="h-9 rounded-md border border-border px-3 text-sm hover:bg-muted" onClick={onCancel}>Cancel</button>
          <button type="submit" disabled={submitting || !deviceName.trim()} className="h-9 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground disabled:opacity-60">Promote</button>
        </div>
      </form>
    </div>
  );
}
