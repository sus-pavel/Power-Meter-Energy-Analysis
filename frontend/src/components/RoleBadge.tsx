import type { UserRole } from "../types/auth";

const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Admin",
  chief_engineer: "Chief Engineer",
  analyst: "Analyst",
  guest: "Guest"
};

export function roleLabel(role: UserRole): string {
  return ROLE_LABELS[role];
}

export function RoleBadge({ role }: { role: UserRole }) {
  return (
    <span className="inline-flex items-center rounded-sm border border-border bg-muted px-2 py-1 text-xs font-medium text-foreground">
      {roleLabel(role)}
    </span>
  );
}
