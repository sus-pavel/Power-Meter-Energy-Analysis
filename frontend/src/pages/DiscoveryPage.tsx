import { Compass } from "lucide-react";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";
import { StatusCard } from "../components/StatusCard";

export function DiscoveryPage() {
  return (
    <>
      <PageHeader title="Discovery" description="Safe Modbus TCP endpoint discovery." />
      <div className="space-y-4 p-6">
        <StatusCard label="Workflow" value="Ready" icon={<Compass className="h-5 w-5" />} detail="Scan execution UI arrives in Stage 3.2" />
        <EmptyState title="Discovery workflow will be implemented in Stage 3.2" description="The backend endpoints are available for scans, candidates, probes, and promotion." />
      </div>
    </>
  );
}
