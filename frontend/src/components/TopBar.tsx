import { Activity } from "lucide-react";
import { DesktopStatusStrip } from "./DesktopStatusStrip";
import { UserMenu } from "./UserMenu";
import type { CurrentUser } from "../types/auth";
import type { DesktopDiagnostics } from "../types/desktop";

interface TopBarProps {
  user: CurrentUser;
  onLogout: () => void;
  desktopDiagnostics: DesktopDiagnostics | null;
}

export function TopBar({ user, onLogout, desktopDiagnostics }: TopBarProps) {
  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-5">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Activity className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold leading-4 text-foreground">PowerMeter</p>
          <p className="text-xs text-muted-foreground">Local energy monitoring</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <DesktopStatusStrip diagnostics={desktopDiagnostics} />
        <UserMenu user={user} onLogout={onLogout} />
      </div>
    </header>
  );
}
