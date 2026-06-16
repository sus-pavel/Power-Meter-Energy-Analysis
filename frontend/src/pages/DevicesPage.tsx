import { Gauge } from "lucide-react";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { StatusCard } from "../components/StatusCard";
import { useDevices } from "../hooks/useDevices";

export function DevicesPage() {
  const { data, isLoading, isError } = useDevices();
  return (
    <>
      <PageHeader title="Devices" description="Managed Modbus TCP devices." />
      <div className="space-y-4 p-6">
        {isLoading ? <LoadingState label="Loading devices" /> : null}
        {isError ? <ErrorState /> : null}
        {data ? <StatusCard label="Managed devices" value={data.length} icon={<Gauge className="h-5 w-5" />} detail="Device editor arrives in Stage 3.2" /> : null}
        <EmptyState title="Devices page coming in Stage 3.2" description="This shell is ready for the device list and register map editor." />
      </div>
    </>
  );
}
