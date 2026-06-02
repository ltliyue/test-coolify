import { useLocation, useNavigate, Link } from "react-router-dom";
import {
  Bell,
  ChevronRight,
  LogOut,
  Menu,
  Search,
  User as UserIcon,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { ThemeToggle } from "../ui/ThemeToggle";
import { Avatar } from "../ui/Avatar";
import { Dropdown, DropdownItem, DropdownSeparator } from "../ui/Dropdown";
import { Badge } from "../ui/Badge";
import { useAuthStore } from "../../lib/auth-store";
import { api } from "../../lib/api";
import { useLogout } from "../../hooks/useAuth";

interface NotificationsResponse {
  items?: Array<{ id: string }>;
  total?: number;
}

const ROUTE_TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/personas": "Personas",
  "/creatives": "Creatives",
  "/campaigns": "Campaigns",
  "/attribution": "Attribution",
  "/audience-export": "Audience Export",
  "/integrations": "Integrations",
  "/imports": "Imports",
  "/notifications": "Notifications",
  "/reports": "Reports",
  "/settings": "Settings",
};

interface TopbarProps {
  onToggleSidebar: () => void;
}

export function Topbar({ onToggleSidebar }: TopbarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const title = ROUTE_TITLES[location.pathname] ?? "ReceptivIQ";

  const { data: unread } = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: async () => {
      const res = await api.get<NotificationsResponse | unknown[]>(
        "/notifications",
        { params: { unread_only: true, limit: 1 } },
      );
      // Endpoint shape may be list or paginated. Be defensive.
      if (Array.isArray(res.data)) return res.data.length;
      return res.data?.total ?? res.data?.items?.length ?? 0;
    },
    refetchInterval: 60_000,
    retry: false,
  });

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur md:px-6">
      <Button
        variant="ghost"
        size="icon"
        onClick={onToggleSidebar}
        className="md:hidden"
        aria-label="Toggle sidebar"
      >
        <Menu className="h-4 w-4" />
      </Button>

      <div className="hidden items-center gap-1.5 text-sm md:flex">
        <Link
          to="/"
          className="text-muted-foreground transition-colors hover:text-foreground"
        >
          ReceptivIQ
        </Link>
        <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="font-medium">{title}</span>
      </div>

      <div className="relative ml-auto hidden w-72 md:block">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search..."
          className="h-9 pl-9 pr-12"
          aria-label="Search"
        />
        <kbd className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
          /
        </kbd>
      </div>

      <div className="ml-auto flex items-center gap-1 md:ml-2">
        <ThemeToggle />

        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate("/notifications")}
          aria-label="Notifications"
          className="relative"
        >
          <Bell className="h-4 w-4" />
          {!!unread && unread > 0 && (
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-accent ring-2 ring-background" />
          )}
        </Button>

        <Dropdown
          trigger={
            <div className="ml-1 flex items-center gap-2 rounded-full p-1 transition-colors hover:bg-muted">
              <Avatar name={user?.full_name ?? "User"} size={28} />
            </div>
          }
        >
          {(close) => (
            <>
              <div className="px-2.5 py-2">
                <div className="text-sm font-medium">
                  {user?.full_name ?? "—"}
                </div>
                <div className="truncate text-xs text-muted-foreground">
                  {user?.email}
                </div>
                <div className="mt-1.5">
                  <Badge variant="accent">
                    {user?.role_label || user?.role}
                  </Badge>
                </div>
              </div>
              <DropdownSeparator />
              <DropdownItem
                onClick={() => {
                  close();
                  navigate("/settings");
                }}
              >
                <UserIcon className="h-3.5 w-3.5" />
                Profile & Settings
              </DropdownItem>
              <DropdownSeparator />
              <DropdownItem
                destructive
                onClick={() => {
                  close();
                  logout.mutate();
                }}
              >
                <LogOut className="h-3.5 w-3.5" />
                Sign out
              </DropdownItem>
            </>
          )}
        </Dropdown>
      </div>
    </header>
  );
}
