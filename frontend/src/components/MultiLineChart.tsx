import type { ChartPoint } from "../types/analytics";

const COLORS = ["#2563eb", "#16a34a", "#dc2626", "#9333ea", "#ca8a04", "#0891b2"];

export function MultiLineChart({ series }: { series: Array<{ name: string; points: ChartPoint[] }> }) {
  const nonEmpty = series.filter((item) => item.points.length > 0);
  if (nonEmpty.length === 0) {
    return <div className="rounded-md border border-dashed border-border p-6 text-sm text-muted-foreground">No chart data available.</div>;
  }
  const width = 900;
  const height = 220;
  const values = nonEmpty.flatMap((item) => item.points.map((point) => point.value));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const pathFor = (points: ChartPoint[]) => points.map((point, index) => {
    const x = points.length === 1 ? width / 2 : (index / (points.length - 1)) * width;
    const y = height - ((point.value - min) / span) * height;
    return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
  }).join(" ");
  return (
    <div className="rounded-md border border-border bg-card p-3">
      <div className="mb-2 flex flex-wrap gap-3 text-xs">
        {nonEmpty.map((item, index) => <span key={item.name} style={{ color: COLORS[index % COLORS.length] }}>{item.name}</span>)}
      </div>
      <svg viewBox={`0 0 ${width + 48} ${height + 48}`} className="h-64 w-full" role="img">
        <line x1="24" y1="244" x2="924" y2="244" className="stroke-border" />
        {nonEmpty.map((item, index) => (
          <path key={item.name} d={pathFor(item.points)} transform="translate(24 24)" fill="none" stroke={COLORS[index % COLORS.length]} strokeWidth="2" />
        ))}
      </svg>
    </div>
  );
}
