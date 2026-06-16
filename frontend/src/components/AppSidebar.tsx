import { Activity, BarChart3, ClipboardList, Compass, Gauge, LayoutDashboard, LineChart, MonitorCog, Settings, Sigma, Wrench } from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "./utils";
import type { UserRole } from "../types/auth";

interface NavItem {
  label: string;
  path: string;
  icon: typeof LayoutDashboard;
  roles: UserRole[];
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard, roles: ["guest", "analyst", "chief_engineer", "admin"] },
  { label: "Operations", path: "/operations", icon: MonitorCog, roles: ["analyst", "chief_engineer", "admin"] },
  { label: "Devices", path: "/devices", icon: Gauge, roles: ["analyst", "chief_engineer", "admin"] },
  { label: "Discovery", path: "/discovery", icon: Compass, roles: ["analyst", "chief_engineer", "admin"] },
  { label: "Candidates", path: "/candidates", icon: ClipboardList, roles: ["analyst", "chief_engineer", "admin"] },
  { label: "Analytics", path: "/analytics", icon: BarChart3, roles: ["analyst", "chief_engineer", "admin"] },
  { label: "History", path: "/history", icon: LineChart, roles: ["analyst", "chief_engineer", "admin"] },
  { label: "DRPI", path: "/drpi", icon: Activity, roles: ["analyst", "chief_engineer", "admin"] },
  { label: "SSA", path: "/ssa", icon: Sigma, roles: ["analyst", "chief_engineer", "admin"] },
  { label: "Administration", path: "/admin", icon: Settings, roles: ["admin"] }
];

export function allowedNavigation(role: UserRole) {
  return NAV_ITEMS.filter((item) => item.roles.includes(role));
}

export function AppSidebar({ role }: { role: UserRole }) {
  const items = allowedNavigation(role);
  return (
    <aside className="hidden w-60 shrink-0 border-r border-border bg-card md:block">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
          <Wrench className="h-4 w-4 text-primary" />
          Operations
        </div>
      </div>
      <nav className="space-y-1 p-3">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground",
                  isActive && "bg-muted text-foreground"
                )
              }
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
