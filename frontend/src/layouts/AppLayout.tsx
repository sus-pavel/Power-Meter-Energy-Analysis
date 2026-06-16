import { Outlet } from "react-router-dom";
import { AppSidebar } from "../components/AppSidebar";
import { TopBar } from "../components/TopBar";
import { useAuth } from "../auth/AuthContext";
import type { DesktopDiagnostics } from "../types/desktop";

interface AppLayoutProps {
  desktopDiagnostics: DesktopDiagnostics | null;
}

export function AppLayout({ desktopDiagnostics }: AppLayoutProps) {
  const { user, logout } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <TopBar user={user} onLogout={logout} desktopDiagnostics={desktopDiagnostics} />
      {user.must_change_password ? (
        <div className="border-b border-accent/40 bg-accent/15 px-5 py-2 text-sm text-foreground">
          Default admin credentials are still active. Change the admin password in User Administration before using this app operationally.
        </div>
      ) : null}
      <div className="flex min-h-[calc(100vh-3.5rem)]">
        <AppSidebar role={user.role} />
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
