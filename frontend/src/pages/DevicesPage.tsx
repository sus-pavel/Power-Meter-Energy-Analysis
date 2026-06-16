import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { deleteDevice } from "../api/devices";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { DeviceTable } from "../components/DeviceTable";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { useDevices } from "../hooks/useDevices";
import { useOperationalDevices } from "../hooks/useOperations";
import { usePermissions } from "../hooks/usePermissions";
import type { Device } from "../types/device";

export function DevicesPage() {
  const { data, isLoading, isError } = useDevices();
  const operations = useOperationalDevices(5000);
  const { canManageLifecycle } = usePermissions();
  const queryClient = useQueryClient();
  const [deleteTarget, setDeleteTarget] = useState<Device | null>(null);
  const [error, setError] = useState<string | null>(null);

  const deleteMutation = useMutation({
    mutationFn: deleteDevice,
    onSuccess: () => {
      setDeleteTarget(null);
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
    onError: (err: AxiosError<{ detail?: string }>) => setError(err.response?.data?.detail ?? "Device delete failed.")
  });

  return (
    <>
      <PageHeader title="Devices" description="Managed Modbus TCP devices and promoted assets." />
      <div className="space-y-4 p-6">
        {error ? <ErrorState title="Action failed" message={error} /> : null}
        {isLoading ? <LoadingState label="Loading devices" /> : null}
        {isError ? <ErrorState message="Devices could not be loaded." /> : null}
        {data && data.length === 0 ? <EmptyState title="No managed devices" description="Promote a candidate from discovery to create a device." /> : null}
        {data && data.length > 0 ? (
          <DeviceTable
            devices={data}
            operationsByDeviceId={new Map((operations.data ?? []).map((device) => [device.id, device]))}
            canManage={canManageLifecycle}
            onDelete={setDeleteTarget}
          />
        ) : null}
      </div>
      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete device"
        message={`Delete ${deleteTarget?.name}? This also removes the register map.`}
        confirmLabel="Delete"
        danger
        onCancel={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
      />
    </>
  );
}
