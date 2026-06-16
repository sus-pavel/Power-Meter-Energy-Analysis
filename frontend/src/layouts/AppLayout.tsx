import { Outlet } from "react-router-dom";
import { AppSidebar } from "../components/AppSidebar";
import { TopBar } from "../components/TopBar";
import { useAuth } from "../auth/AuthContext";

export function AppLayout() {
  const { user, logout } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <TopBar user={user} onLogout={logout} />
      <div className="flex min-h-[calc(100vh-3.5rem)]">
        <AppSidebar role={user.role} />
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
