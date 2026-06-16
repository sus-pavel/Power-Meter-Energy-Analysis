import type { UserRole } from "../types/auth";

const ROUTE_ROLES: Record<string, UserRole[]> = {
  "/dashboard": ["guest", "analyst", "chief_engineer", "admin"],
  "/devices": ["chief_engineer", "admin"],
  "/discovery": ["chief_engineer", "admin"],
  "/analytics": ["analyst", "chief_engineer", "admin"],
  "/admin": ["admin"]
};

export function canAccessPath(role: UserRole, path: string): boolean {
  return ROUTE_ROLES[path]?.includes(role) ?? true;
}
