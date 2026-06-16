import { Activity } from "lucide-react";
import { UserMenu } from "./UserMenu";
import type { CurrentUser } from "../types/auth";

interface TopBarProps {
  user: CurrentUser;
  onLogout: () => void;
}

export function TopBar({ user, onLogout }: TopBarProps) {
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
      <UserMenu user={user} onLogout={onLogout} />
    </header>
  );
}
