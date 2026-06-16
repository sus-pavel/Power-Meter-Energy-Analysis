export function ScatterChart({ points }: { points: Array<{ component: number; cluster: number; frequency: number; amplitude: number }> }) {
  if (points.length === 0) {
    return <div className="rounded-md border border-dashed border-border p-6 text-sm text-muted-foreground">No scatter data available.</div>;
  }
  const width = 520;
  const height = 240;
  const maxFreq = Math.max(...points.map((point) => point.frequency), 1);
  const maxAmp = Math.max(...points.map((point) => point.amplitude), 1);
  return (
    <div className="rounded-md border border-border bg-card p-3">
      <svg viewBox={`0 0 ${width + 48} ${height + 48}`} className="h-72 w-full" role="img">
        <line x1="24" y1="264" x2="544" y2="264" className="stroke-border" />
        <line x1="24" y1="24" x2="24" y2="264" className="stroke-border" />
        {points.map((point) => (
          <circle
            key={point.component}
            cx={24 + (point.frequency / maxFreq) * width}
            cy={24 + height - (point.amplitude / maxAmp) * height}
            r="5"
            className="fill-primary"
          />
        ))}
      </svg>
    </div>
  );
}
