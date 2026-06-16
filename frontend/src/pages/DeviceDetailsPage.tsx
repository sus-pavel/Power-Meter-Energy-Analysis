import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { useParams } from "react-router-dom";
import {
  createDeviceRegister,
  deleteDeviceRegister,
  updateDevice,
  updateDeviceRegister
} from "../api/devices";
import { DeviceDetailsCard } from "../components/DeviceDetailsCard";
import { DeviceStatusCard } from "../components/DeviceStatusCard";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { RecentMeasurementsTable } from "../components/RecentMeasurementsTable";
import { RegisterMapTable } from "../components/RegisterMapTable";
import { useDevice, useDeviceMeasurements, useDeviceRegisters, useDeviceStatus } from "../hooks/useDeviceDetails";
import { usePermissions } from "../hooks/usePermissions";
import type { DeviceUpdatePayload, RegisterPayload } from "../types/device";

export function DeviceDetailsPage() {
  const deviceId = Number(useParams().deviceId);
  const deviceQuery = useDevice(deviceId);
  const registersQuery = useDeviceRegisters(deviceId);
  const statusQuery = useDeviceStatus(deviceId);
  const measurementsQuery = useDeviceMeasurements(deviceId);
  const { canManageLifecycle } = usePermissions();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["devices"] });
    queryClient.invalidateQueries({ queryKey: ["devices", deviceId] });
    queryClient.invalidateQueries({ queryKey: ["devices", deviceId, "registers"] });
    queryClient.invalidateQueries({ queryKey: ["devices", deviceId, "status"] });
    queryClient.invalidateQueries({ queryKey: ["devices", deviceId, "measurements"] });
    queryClient.invalidateQueries({ queryKey: ["operations"] });
  };

  const saveDevice = useMutation({
    mutationFn: (payload: DeviceUpdatePayload) => updateDevice(deviceId, payload),
    onSuccess: invalidate,
    onError: (err: AxiosError<{ detail?: string }>) => setError(err.response?.data?.detail ?? "Device update failed.")
  });

  const createRegister = useMutation({
    mutationFn: (payload: RegisterPayload) => createDeviceRegister(deviceId, payload),
    onSuccess: invalidate,
    onError: (err: AxiosError<{ detail?: string }>) => setError(err.response?.data?.detail ?? "Register create failed.")
  });

  const updateRegister = useMutation({
    mutationFn: ({ registerId, payload }: { registerId: number; payload: Partial<RegisterPayload> }) => updateDeviceRegister(deviceId, registerId, payload),
    onSuccess: invalidate,
    onError: (err: AxiosError<{ detail?: string }>) => setError(err.response?.data?.detail ?? "Register update failed.")
  });

  const deleteRegister = useMutation({
    mutationFn: (registerId: number) => deleteDeviceRegister(deviceId, registerId),
    onSuccess: invalidate,
    onError: (err: AxiosError<{ detail?: string }>) => setError(err.response?.data?.detail ?? "Register delete failed.")
  });

  return (
    <>
      <PageHeader title={`Device #${deviceId}`} description="Device configuration and register map." />
      <div className="space-y-4 p-6">
        {error ? <ErrorState title="Action failed" message={error} /> : null}
        {deviceQuery.isLoading ? <LoadingState label="Loading device" /> : null}
        {deviceQuery.isError ? <ErrorState message="Device could not be loaded." /> : null}
        {deviceQuery.data ? (
          <DeviceDetailsCard device={deviceQuery.data} canManage={canManageLifecycle} saving={saveDevice.isPending} onSave={(payload) => saveDevice.mutate(payload)} />
        ) : null}
        {statusQuery.data ? <DeviceStatusCard status={statusQuery.data} /> : null}
        <section className="space-y-2">
          <h2 className="text-sm font-semibold">Polling Configuration</h2>
          <div className="rounded-md border border-border bg-card p-4 text-sm">
            <dl className="grid gap-3 sm:grid-cols-3">
              <div><dt className="text-muted-foreground">Enabled</dt><dd className="font-medium">{deviceQuery.data?.enabled ? "Yes" : "No"}</dd></div>
              <div><dt className="text-muted-foreground">Interval</dt><dd className="font-medium">{deviceQuery.data?.poll_interval_sec ?? "-"} seconds</dd></div>
              <div><dt className="text-muted-foreground">Enabled registers</dt><dd className="font-medium">{registersQuery.data?.filter((register) => register.enabled).length ?? "-"}</dd></div>
            </dl>
          </div>
        </section>
        <section className="space-y-2">
          <h2 className="text-sm font-semibold">Register Map</h2>
          {registersQuery.isLoading ? <LoadingState label="Loading register map" /> : null}
          {registersQuery.isError ? <ErrorState message="Register map could not be loaded." /> : null}
          {registersQuery.data ? (
            <RegisterMapTable
              registers={registersQuery.data}
              canManage={canManageLifecycle}
              onCreate={(payload) => createRegister.mutate(payload)}
              onUpdate={(registerId, payload) => updateRegister.mutate({ registerId, payload })}
              onDelete={(registerId) => deleteRegister.mutate(registerId)}
            />
          ) : null}
        </section>
        <section className="space-y-2">
          <h2 className="text-sm font-semibold">Recent Measurements</h2>
          {measurementsQuery.isLoading ? <LoadingState label="Loading recent measurements" /> : null}
          {measurementsQuery.isError ? <ErrorState message="Recent measurements could not be loaded." /> : null}
          {measurementsQuery.data ? <RecentMeasurementsTable measurements={measurementsQuery.data} /> : null}
        </section>
      </div>
    </>
  );
}
