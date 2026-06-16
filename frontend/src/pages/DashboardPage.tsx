import { Compass, Gauge, Server, ShieldCheck, Users } from "lucide-react";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { StatusCard } from "../components/StatusCard";
import { useDashboardSummary } from "../hooks/useDashboardSummary";

export function DashboardPage() {
  const { data, isLoading, isError } = useDashboardSummary();

  return (
    <>
      <PageHeader title="Dashboard" description="Application status and operational inventory." />
      <div className="p-6">
        {isLoading ? <LoadingState label="Loading dashboard" /> : null}
        {isError ? <ErrorState /> : null}
        {data ? (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <StatusCard label="Devices" value={data.devices} icon={<Gauge className="h-5 w-5" />} detail={`${data.enabled_devices} enabled`} />
            <StatusCard label="Promoted" value={data.promoted_devices} icon={<ShieldCheck className="h-5 w-5" />} detail="From candidates" />
            <StatusCard label="Candidates" value={data.discovered_candidates} icon={<Compass className="h-5 w-5" />} detail={`${data.pending_review} pending review`} />
            <StatusCard label="Users" value={data.users} icon={<Users className="h-5 w-5" />} detail="Local accounts" />
            <StatusCard label="Database" value={data.database} icon={<Server className="h-5 w-5" />} detail={`Mode: ${data.mode}`} />
          </div>
        ) : null}
      </div>
    </>
  );
}
