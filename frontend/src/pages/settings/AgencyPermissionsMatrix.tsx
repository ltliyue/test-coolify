import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { PageHeader } from "../../components/ui/PageHeader";
import { Card } from "../../components/ui/Card";
import { api, extractErrorMessage } from "../../lib/api";
import { useAuthStore } from "../../lib/auth-store";

interface PermissionEntry {
  code: string;
  label: string;
  category: string;
  description: string | null;
}

interface OverrideRow {
  role: string;
  code: string;
  granted: boolean;
}

interface AgencyPermissionsResponse {
  role_defaults: Record<string, string[]>;
  overrides: OverrideRow[];
  effective: Record<string, string[]>;
  all_permissions: PermissionEntry[];
}

interface RoleEntry {
  code: string;
  label: string;
  tier: string;
  agency_id: string | null;
  is_system: boolean;
  rank: number;
}

export default function AgencyPermissionsMatrix() {
  const agencyId = useAuthStore((s) => s.user?.agency_id);
  const callerRank = useAuthStore((s) => s.user?.role_rank ?? 0);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    enabled: !!agencyId,
    queryKey: ["agency-permissions", agencyId],
    queryFn: async () =>
      (
        await api.get<AgencyPermissionsResponse>(
          `/agencies/${agencyId}/permissions`,
        )
      ).data,
  });

  const rolesQ = useQuery({
    enabled: !!agencyId,
    queryKey: ["agency-roles", agencyId],
    queryFn: async () =>
      (await api.get<RoleEntry[]>(`/agencies/${agencyId}/roles`)).data,
  });

  const AGENCY_ROLES = useMemo(
    () => (rolesQ.data ?? []).map((r) => r.code),
    [rolesQ.data],
  );
  const ROLE_LABELS = useMemo(() => {
    const out: Record<string, string> = {};
    for (const r of rolesQ.data ?? []) out[r.code] = r.label;
    return out;
  }, [rolesQ.data]);
  const ROLE_RANKS = useMemo(() => {
    const out: Record<string, number> = {};
    for (const r of rolesQ.data ?? []) out[r.code] = r.rank ?? 0;
    return out;
  }, [rolesQ.data]);
  const isLocked = (role: string) => (ROLE_RANKS[role] ?? 0) >= callerRank;

  const upsert = useMutation({
    mutationFn: async (payload: {
      role: string;
      code: string;
      granted: boolean;
    }) => {
      await api.put(`/agencies/${agencyId}/permissions`, payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["agency-permissions", agencyId] });
    },
    onError: (err) => {
      toast.error(extractErrorMessage(err, "Failed to save permission"));
    },
  });

  // (role|code) -> granted bool (override exists in DB)
  const overrideMap = useMemo(() => {
    const m = new Map<string, boolean>();
    for (const o of data?.overrides ?? []) {
      m.set(`${o.role}|${o.code}`, o.granted);
    }
    return m;
  }, [data]);

  // Per-role set of permission codes granted by the system default.
  const defaultSets = useMemo(() => {
    const sets: Record<string, Set<string>> = {};
    for (const r of AGENCY_ROLES) {
      sets[r] = new Set(data?.role_defaults?.[r] ?? []);
    }
    return sets;
  }, [data, AGENCY_ROLES]);

  const grouped = useMemo(() => {
    const groups: Record<string, PermissionEntry[]> = {};
    for (const p of data?.all_permissions ?? []) {
      (groups[p.category] ??= []).push(p);
    }
    return groups;
  }, [data]);

  /**
   * Effective state = override if present, else system default.
   * Clicking the checkbox writes an override row with the new boolean.
   */
  function isEffectivelyGranted(role: string, code: string): boolean {
    const ov = overrideMap.get(`${role}|${code}`);
    if (ov !== undefined) return ov;
    return defaultSets[role]?.has(code) ?? false;
  }

  function hasOverride(role: string, code: string): boolean {
    return overrideMap.has(`${role}|${code}`);
  }

  function onToggle(role: string, code: string, next: boolean) {
    upsert.mutate({ role, code, granted: next });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Agency Permissions"
        description="Tick to grant, untick to revoke. A small dot under the checkbox marks an Agency-level override against the platform default."
      />
      {!agencyId ? (
        <Card className="p-6 text-sm text-muted-foreground">
          <p className="mb-2 font-medium text-foreground">
            This page is for Agency-level overrides.
          </p>
          <p>
            Your account is not bound to an Agency (platform tier). Manage
            system-wide defaults at{" "}
            <Link
              to="/platform/permissions"
              className="font-medium text-accent underline-offset-4 hover:underline"
            >
              /platform/permissions
            </Link>
            .
          </p>
        </Card>
      ) : isLoading || rolesQ.isLoading ? (
        <Card className="p-6 text-sm text-muted-foreground">Loading…</Card>
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="min-w-full text-sm">
            <thead className="border-b border-border bg-muted/30 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="w-72 px-4 py-3">Permission</th>
                {AGENCY_ROLES.map((r) => (
                  <th
                    key={r}
                    className={
                      "px-3 py-3 text-center" +
                      (isLocked(r) ? " opacity-50" : "")
                    }
                    title={
                      isLocked(r)
                        ? "Cannot edit a role at or above your own level."
                        : undefined
                    }
                  >
                    {ROLE_LABELS[r] ?? r}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(grouped).map(([category, perms]) => (
                <CategoryRows
                  key={category}
                  category={category}
                  perms={perms}
                  roles={AGENCY_ROLES}
                  isGranted={isEffectivelyGranted}
                  hasOverride={hasOverride}
                  isLocked={isLocked}
                  onToggle={onToggle}
                />
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

function CategoryRows({
  category,
  perms,
  roles,
  isGranted,
  hasOverride,
  isLocked,
  onToggle,
}: {
  category: string;
  perms: PermissionEntry[];
  roles: string[];
  isGranted: (role: string, code: string) => boolean;
  hasOverride: (role: string, code: string) => boolean;
  isLocked: (role: string) => boolean;
  onToggle: (role: string, code: string, next: boolean) => void;
}) {
  return (
    <>
      <tr className="bg-muted/10">
        <td
          colSpan={roles.length + 1}
          className="px-4 py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
        >
          {category}
        </td>
      </tr>
      {perms.map((p) => (
        <tr key={p.code} className="border-b border-border/40">
          <td className="px-4 py-2">
            <div className="font-medium">{p.label}</div>
            <div className="font-mono text-[11px] text-muted-foreground">
              {p.code}
            </div>
          </td>
          {roles.map((r) => {
            const granted = isGranted(r, p.code);
            const override = hasOverride(r, p.code);
            const locked = isLocked(r);
            return (
              <td key={r} className="px-3 py-2 text-center">
                <div className="flex flex-col items-center gap-0.5">
                  <input
                    type="checkbox"
                    checked={granted}
                    disabled={locked}
                    onChange={(e) => onToggle(r, p.code, e.target.checked)}
                    className="h-4 w-4 cursor-pointer accent-accent disabled:cursor-not-allowed disabled:opacity-40"
                    title={
                      locked
                        ? "Cannot edit a role at or above your own level."
                        : override
                          ? "Agency override (click to flip)"
                          : "Inheriting platform default (click to override)"
                    }
                  />
                  <span
                    className={
                      "h-1 w-1 rounded-full " +
                      (override ? "bg-accent" : "bg-transparent")
                    }
                    aria-hidden="true"
                  />
                </div>
              </td>
            );
          })}
        </tr>
      ))}
    </>
  );
}
