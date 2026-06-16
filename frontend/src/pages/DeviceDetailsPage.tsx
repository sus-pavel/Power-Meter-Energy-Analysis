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
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { RegisterMapTable } from "../components/RegisterMapTable";
import { useDevice, useDeviceRegisters } from "../hooks/useDeviceDetails";
import { usePermissions } from "../hooks/usePermissions";
import type { DeviceUpdatePayload, RegisterPayload } from "../types/device";

export function DeviceDetailsPage() {
  const deviceId = Number(useParams().deviceId);
  const deviceQuery = useDevice(deviceId);
  const registersQuery = useDeviceRegisters(deviceId);
  const { canManageLifecycle } = usePermissions();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["devices"] });
    queryClient.invalidateQueries({ queryKey: ["devices", deviceId] });
    queryClient.invalidateQueries({ queryKey: ["devices", deviceId, "registers"] });
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
      </div>
    </>
  );
}
