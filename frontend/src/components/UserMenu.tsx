import { LogOut, UserCircle } from "lucide-react";
import { RoleBadge } from "./RoleBadge";
import type { CurrentUser } from "../types/auth";

interface UserMenuProps {
  user: CurrentUser;
  onLogout: () => void;
}

export function UserMenu({ user, onLogout }: UserMenuProps) {
  return (
    <div className="flex items-center gap-3">
      <div className="hidden items-center gap-2 text-sm md:flex">
        <UserCircle className="h-5 w-5 text-muted-foreground" />
        <div className="text-right">
          <p className="font-medium leading-5 text-foreground">{user.full_name || user.username}</p>
          <RoleBadge role={user.role} />
        </div>
      </div>
      <button
        type="button"
        onClick={onLogout}
        className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-card text-muted-foreground hover:bg-muted hover:text-foreground"
        aria-label="Logout"
        title="Logout"
      >
        <LogOut className="h-4 w-4" />
      </button>
    </div>
  );
}
