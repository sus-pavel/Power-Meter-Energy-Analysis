import type { ChartPoint } from "../types/analytics";

function pathFor(points: ChartPoint[], width: number, height: number): string {
  if (points.length === 0) return "";
  const values = points.map((point) => point.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return points.map((point, index) => {
    const x = points.length === 1 ? width / 2 : (index / (points.length - 1)) * width;
    const y = height - ((point.value - min) / span) * height;
    return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
  }).join(" ");
}

export function LineChart({ points, label, height = 220 }: { points: ChartPoint[]; label?: string; height?: number }) {
  if (points.length === 0) {
    return <div className="rounded-md border border-dashed border-border p-6 text-sm text-muted-foreground">No chart data available.</div>;
  }
  const width = 900;
  const pad = 24;
  const values = points.map((point) => point.value);
  return (
    <div className="rounded-md border border-border bg-card p-3">
      {label ? <div className="mb-2 text-sm font-medium">{label}</div> : null}
      <svg viewBox={`0 0 ${width + pad * 2} ${height + pad * 2}`} className="h-64 w-full" role="img">
        <line x1={pad} y1={height + pad} x2={width + pad} y2={height + pad} className="stroke-border" />
        <line x1={pad} y1={pad} x2={pad} y2={height + pad} className="stroke-border" />
        <path d={pathFor(points, width, height)} transform={`translate(${pad} ${pad})`} fill="none" className="stroke-primary" strokeWidth="2" />
        <text x={pad} y={16} className="fill-muted-foreground text-xs">{Math.max(...values).toFixed(2)}</text>
        <text x={pad} y={height + pad + 18} className="fill-muted-foreground text-xs">{Math.min(...values).toFixed(2)}</text>
      </svg>
    </div>
  );
}
