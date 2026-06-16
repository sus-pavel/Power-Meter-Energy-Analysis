export function WcorrHeatmap({ matrix }: { matrix: number[][] }) {
  if (matrix.length === 0) {
    return <div className="rounded-md border border-dashed border-border p-6 text-sm text-muted-foreground">No W-correlation matrix available.</div>;
  }
  return (
    <div className="overflow-auto rounded-md border border-border bg-card p-3">
      <div className="grid w-max gap-0.5" style={{ gridTemplateColumns: `repeat(${matrix.length}, 2.25rem)` }}>
        {matrix.flatMap((row, rowIndex) =>
          row.map((value, colIndex) => (
            <div
              key={`${rowIndex}-${colIndex}`}
              className="flex h-9 w-9 items-center justify-center text-[10px] tabular-nums"
              style={{ backgroundColor: `rgba(37, 99, 235, ${Math.max(0.08, value)})`, color: value > 0.55 ? "white" : "black" }}
              title={`C${rowIndex} x C${colIndex}: ${value}`}
            >
              {value.toFixed(2)}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
