import type { DeviceStatus } from "../types/device";
import { LastSeenIndicator } from "./LastSeenIndicator";
import { OperationalStatusBadge } from "./StatusBadge";

export function DeviceStatusCard({ status }: { status: DeviceStatus }) {
  return (
    <section className="rounded-md border border-border bg-card p-4">
      <h2 className="text-sm font-semibold">Device Status</h2>
      <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-muted-foreground">Current Status</dt>
          <dd className="mt-1"><OperationalStatusBadge value={status.status} /></dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Last Seen</dt>
          <dd className="font-medium"><LastSeenIndicator value={status.last_success_at} /></dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Last Error</dt>
          <dd className="font-medium">{status.last_error_at ? new Date(status.last_error_at).toLocaleString() : "-"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Error Message</dt>
          <dd className="font-medium">{status.last_error_message ?? "-"}</dd>
        </div>
      </dl>
    </section>
  );
}
