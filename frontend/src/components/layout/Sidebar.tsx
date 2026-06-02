import { useEffect, useMemo, useState } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  Sparkles,
  Network,
  Megaphone,
  Share2,
  Plug,
  Upload,
  Bell,
  FileBarChart,
  Settings as SettingsIcon,
  ChevronDown,
  UserPlus,
  Briefcase,
  Building2,
  ShieldCheck,
  KeyRound,
  UserCog,
  ScrollText,
  type LucideIcon,
} from "lucide-react";
import { cn } from "../../lib/cn";
import { useAuthStore } from "../../lib/auth-store";

type Tier = "platform" | "agency" | "client";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  /** Permission code required to see this item. null = always visible. */
  code?: string | null;
}

interface NavGroup {
  key: string;
  label: string;
  defaultOpen?: boolean;
  items: NavItem[];
  /**
   * Tiers that should see this group at all. Even when a user technically
   * holds every permission (e.g. platform_super_admin inherits all 45),
   * we don't show them Agency-scoped operations — they don't have an
   * agency_id, so the tool would have nothing to act on.
   */
  tiers: Tier[];
}

function userTier(role: string | undefined): Tier | null {
  if (role === "platform_super_admin" || role === "platform_admin")
    return "platform";
  if (role === "agency_admin" || role === "agency_ops") return "agency";
  if (role === "client_viewer") return "client";
  return null;
}

// PR 3: every nav item declares the permission code needed to see it.
// Items the user lacks are filtered out; empty groups disappear entirely.
const ALL_GROUPS: NavGroup[] = [
  // Overview first for every tier: the Dashboard is always the landing
  // page, so it should anchor the top of the sidebar.
  {
    key: "overview",
    label: "Overview",
    defaultOpen: true,
    tiers: ["platform", "agency"],
    items: [{ to: "/", label: "Dashboard", icon: LayoutDashboard, code: null }],
  },
  {
    key: "platform",
    label: "Platform",
    defaultOpen: true,
    tiers: ["platform"],
    items: [
      {
        to: "/platform/agencies",
        label: "Agencies",
        icon: Building2,
        code: "platform.agency.view",
      },
      {
        to: "/platform/users",
        label: "Platform Users",
        icon: ShieldCheck,
        code: "platform.users.view",
      },
      {
        to: "/platform/permissions",
        label: "Permissions",
        icon: KeyRound,
        code: "platform.permissions.manage",
      },
      {
        to: "/platform/roles",
        label: "Roles",
        icon: UserCog,
        code: "platform.permissions.manage",
      },
      {
        to: "/platform/audit",
        label: "Audit log",
        icon: ScrollText,
        code: "platform.audit.read",
      },
    ],
  },
  {
    key: "ai-studio",
    label: "AI Studio",
    defaultOpen: true,
    tiers: ["agency"],
    items: [
      {
        to: "/personas",
        label: "Personas",
        icon: Users,
        code: "personas.read",
      },
      {
        to: "/creatives",
        label: "Creatives",
        icon: Sparkles,
        code: "creatives.read",
      },
      {
        to: "/attribution",
        label: "Attribution",
        icon: Network,
        code: "attribution.read",
      },
    ],
  },
  {
    key: "operations",
    label: "Operations",
    defaultOpen: true,
    tiers: ["agency"],
    items: [
      {
        to: "/campaigns",
        label: "Campaigns",
        icon: Megaphone,
        code: "campaigns.read",
      },
      {
        to: "/audience-export",
        label: "Audience Export",
        icon: Share2,
        code: "audience_export.view",
      },
      {
        to: "/imports",
        label: "Imports",
        icon: Upload,
        code: "imports.upload",
      },
      {
        to: "/integrations",
        label: "Integrations",
        icon: Plug,
        code: "integrations.view",
      },
    ],
  },
  {
    key: "insights",
    label: "Insights",
    defaultOpen: true,
    tiers: ["agency"],
    items: [
      {
        to: "/reports",
        label: "Reports",
        icon: FileBarChart,
        code: "reports.read",
      },
      {
        to: "/notifications",
        label: "Notifications",
        icon: Bell,
        code: "notifications.read",
      },
    ],
  },
  {
    key: "client",
    label: "My Workspace",
    defaultOpen: true,
    tiers: ["client"],
    items: [
      {
        to: "/client/personas",
        label: "My Personas",
        icon: Users,
        code: "portal.access",
      },
      {
        to: "/client/reports",
        label: "My Reports",
        icon: FileBarChart,
        code: "portal.access",
      },
    ],
  },
  {
    key: "settings",
    label: "Settings",
    defaultOpen: true,
    tiers: ["agency"],
    items: [
      {
        to: "/settings",
        label: "General",
        icon: SettingsIcon,
        code: "settings.view",
      },
      {
        to: "/settings/team",
        label: "Team",
        icon: UserPlus,
        code: "team.view",
      },
      {
        to: "/settings/clients",
        label: "Clients",
        icon: Briefcase,
        code: "clients.view",
      },
      {
        to: "/settings/permissions",
        label: "Permissions",
        icon: KeyRound,
        code: "settings.permissions.manage",
      },
      {
        to: "/settings/roles",
        label: "Roles",
        icon: UserCog,
        code: "settings.permissions.manage",
      },
      {
        to: "/settings/audit",
        label: "Audit log",
        icon: ScrollText,
        code: "audit.read",
      },
    ],
  },
];

function groupsForUser(perms: Set<string>, tier: Tier | null): NavGroup[] {
  if (tier === null) return [];
  const out: NavGroup[] = [];
  for (const g of ALL_GROUPS) {
    if (!g.tiers.includes(tier)) continue;
    const items = g.items.filter(
      (i) => i.code === null || i.code === undefined || perms.has(i.code),
    );
    if (items.length > 0) out.push({ ...g, items });
  }
  return out;
}

const STORAGE_PREFIX = "riq-nav-open:";

interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const perms = useAuthStore((s) => s.user?.permissions ?? []);
  const role = useAuthStore((s) => s.user?.role);
  const permSet = useMemo(() => new Set(perms), [perms]);
  const tier = useMemo(() => userTier(role), [role]);
  const groups = useMemo(() => groupsForUser(permSet, tier), [permSet, tier]);

  const [openState, setOpenState] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    for (const g of groups) {
      try {
        const stored =
          typeof window !== "undefined"
            ? window.localStorage.getItem(STORAGE_PREFIX + g.key)
            : null;
        initial[g.key] =
          stored === null ? g.defaultOpen !== false : stored === "1";
      } catch {
        initial[g.key] = g.defaultOpen !== false;
      }
    }
    return initial;
  });

  useEffect(() => {
    for (const [key, open] of Object.entries(openState)) {
      try {
        window.localStorage.setItem(STORAGE_PREFIX + key, open ? "1" : "0");
      } catch {
        // ignore quota / privacy mode failures
      }
    }
  }, [openState]);

  const toggle = (key: string) =>
    setOpenState((prev) => ({ ...prev, [key]: !prev[key] }));

  return (
    <aside className="flex h-full w-64 flex-col border-r border-border bg-card/30">
      <div className="flex h-14 items-center gap-2 border-b border-border px-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <span className="text-sm font-bold">R</span>
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold tracking-tight">ReceptivIQ</div>
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
            Platform
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-3 overflow-y-auto scrollbar-thin px-3 py-5">
        {groups.map((group) => {
          const isOpen = openState[group.key] ?? group.defaultOpen !== false;
          return (
            <div key={group.key}>
              <button
                type="button"
                onClick={() => toggle(group.key)}
                className="mb-1 flex w-full items-center justify-between rounded px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground transition-colors hover:text-foreground"
              >
                <span>{group.label}</span>
                <ChevronDown
                  className={cn(
                    "h-3 w-3 transition-transform",
                    isOpen ? "rotate-0" : "-rotate-90",
                  )}
                />
              </button>
              {isOpen && (
                <ul className="space-y-0.5 pl-1">
                  {group.items.map((item) => {
                    const Icon = item.icon;
                    return (
                      <li key={item.to}>
                        <NavLink
                          to={item.to}
                          end
                          onClick={onNavigate}
                          className={({ isActive }) =>
                            cn(
                              "group relative flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-sm transition-colors",
                              isActive
                                ? "bg-accent/10 text-accent font-medium"
                                : "text-muted-foreground hover:bg-muted hover:text-foreground",
                            )
                          }
                        >
                          {({ isActive }) => (
                            <>
                              {isActive && (
                                <span className="absolute -left-3 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-r-full bg-accent" />
                              )}
                              <Icon className="h-4 w-4" />
                              <span>{item.label}</span>
                            </>
                          )}
                        </NavLink>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          );
        })}
      </nav>

      <div className="border-t border-border p-3 text-[10px] text-muted-foreground">
        v0.1.0 · MVP
      </div>
    </aside>
  );
}
