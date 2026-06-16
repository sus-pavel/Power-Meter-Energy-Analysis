import { useAuth } from "../auth/AuthContext";

export function usePermissions() {
  const { user } = useAuth();
  const role = user?.role;
  return {
    canReadLifecycle: role === "admin" || role === "chief_engineer" || role === "analyst",
    canManageLifecycle: role === "admin" || role === "chief_engineer",
    isReadOnly: role === "analyst"
  };
}
