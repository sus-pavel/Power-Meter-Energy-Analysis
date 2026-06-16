import type { UserRole } from "../types/auth";

const ROUTE_ROLES: Record<string, UserRole[]> = {
  "/dashboard": ["guest", "analyst", "chief_engineer", "admin"],
  "/operations": ["analyst", "chief_engineer", "admin"],
  "/devices": ["analyst", "chief_engineer", "admin"],
  "/discovery": ["analyst", "chief_engineer", "admin"],
  "/candidates": ["analyst", "chief_engineer", "admin"],
  "/analytics": ["analyst", "chief_engineer", "admin"],
  "/admin": ["admin"]
};

export function canAccessPath(role: UserRole, path: string): boolean {
  const route = Object.keys(ROUTE_ROLES).find((candidate) => path === candidate || path.startsWith(`${candidate}/`));
  return route ? ROUTE_ROLES[route].includes(role) : true;
}
