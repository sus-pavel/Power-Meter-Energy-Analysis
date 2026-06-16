import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { clearToken, getStoredToken, storeToken } from "../api/client";
import { getCurrentUser, loginRequest, logoutRequest } from "../api/auth";
import type { CurrentUser } from "../types/auth";

interface AuthContextValue {
  user: CurrentUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [hasToken, setHasToken] = useState(Boolean(getStoredToken()));

  const userQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentUser,
    enabled: hasToken,
    retry: false
  });

  const logout = useCallback(async () => {
    try {
      if (getStoredToken()) {
        await logoutRequest();
      }
    } catch {
      // Stateless JWT logout is client-side in the backend.
    } finally {
      clearToken();
      setHasToken(false);
      queryClient.clear();
    }
  }, [queryClient]);

  const login = useCallback(
    async (username: string, password: string) => {
      const response = await loginRequest(username, password);
      storeToken(response.access_token);
      setHasToken(true);
      await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
    [queryClient]
  );

  useEffect(() => {
    const handler = () => {
      clearToken();
      setHasToken(false);
      queryClient.clear();
    };
    window.addEventListener("powermeter:unauthorized", handler);
    return () => window.removeEventListener("powermeter:unauthorized", handler);
  }, [queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: userQuery.data ?? null,
      isAuthenticated: hasToken && Boolean(userQuery.data),
      isLoading: hasToken && userQuery.isLoading,
      login,
      logout
    }),
    [hasToken, login, logout, userQuery.data, userQuery.isLoading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
