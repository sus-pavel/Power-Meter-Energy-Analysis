import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "../auth/AuthContext";
import { isDesktopRuntime } from "../api/baseUrl";
import { DesktopStartupPage } from "../pages/DesktopStartupPage";
import { AppRoutes } from "../routes/AppRoutes";
import type { DesktopDiagnostics } from "../types/desktop";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false
    }
  }
});

export function App() {
  const [desktopDiagnostics, setDesktopDiagnostics] = useState<DesktopDiagnostics | null>(null);
  const [desktopReady, setDesktopReady] = useState(!isDesktopRuntime());
  const handleDesktopReady = useCallback((diagnostics: DesktopDiagnostics | null) => {
    setDesktopDiagnostics(diagnostics);
    setDesktopReady(true);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {desktopReady ? (
          <AuthProvider>
            <AppRoutes desktopDiagnostics={desktopDiagnostics} />
          </AuthProvider>
        ) : (
          <DesktopStartupPage onReady={handleDesktopReady} />
        )}
      </BrowserRouter>
    </QueryClientProvider>
  );
}
