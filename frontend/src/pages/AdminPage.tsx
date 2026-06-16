import { Settings } from "lucide-react";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";
import { StatusCard } from "../components/StatusCard";

export function AdminPage() {
  return (
    <>
      <PageHeader title="Administration" description="Users, roles, settings, and audit tools." />
      <div className="space-y-4 p-6">
        <StatusCard label="Administration" value="Admin only" icon={<Settings className="h-5 w-5" />} detail="Management screens arrive after shell validation" />
        <EmptyState title="Administration placeholder" description="User management and audit views will build on the existing backend APIs." />
      </div>
    </>
  );
}
