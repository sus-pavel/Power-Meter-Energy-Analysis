export function LastSeenIndicator({ value }: { value: string | null }) {
  if (!value) {
    return <span className="text-muted-foreground">Never</span>;
  }
  const date = new Date(value);
  const ageSeconds = Math.max(0, Math.round((Date.now() - date.getTime()) / 1000));
  const ageLabel = ageSeconds < 60 ? `${ageSeconds}s ago` : ageSeconds < 3600 ? `${Math.round(ageSeconds / 60)}m ago` : `${Math.round(ageSeconds / 3600)}h ago`;
  return (
    <span className="tabular-nums" title={date.toLocaleString()}>
      {ageLabel}
    </span>
  );
}
