import { BarChart3 } from "lucide-react";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";
import { StatusCard } from "../components/StatusCard";

export function AnalyticsPage() {
  return (
    <>
      <PageHeader title="Analytics" description="Historical trends, DRPI, and SSA will be added later." />
      <div className="space-y-4 p-6">
        <StatusCard label="Analytics module" value="Planned" icon={<BarChart3 className="h-5 w-5" />} detail="No analytics workflows in Stage 3.1" />
        <EmptyState title="Analytics placeholder" description="DRPI, SSA, exports, and historical views are reserved for future UI stages." />
      </div>
    </>
  );
}
