import type { OperationsEvent } from "../types/operations";

export function RecentActivityList({ events }: { events: OperationsEvent[] }) {
  return (
    <section className="rounded-md border border-border bg-card p-4">
      <h2 className="text-sm font-semibold">Recent Activity</h2>
      {events.length === 0 ? <p className="mt-2 text-sm text-muted-foreground">No recent operational events.</p> : null}
      <div className="mt-2 space-y-2">
        {events.slice(0, 8).map((event, index) => (
          <div key={`${event.timestamp}-${event.action}-${index}`} className="flex items-center justify-between gap-3 border-b border-border pb-2 text-sm last:border-b-0 last:pb-0">
            <span className="font-medium">{event.action}</span>
            <span className="text-muted-foreground">{event.entity_type} #{event.entity_id ?? "-"}</span>
            <span className="text-xs text-muted-foreground">{new Date(event.timestamp).toLocaleString()}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
