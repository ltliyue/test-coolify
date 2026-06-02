import { useMemo } from "react";
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

interface PlatformPermissionsResponse {
  role_defaults: Record<string, string[]>;
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

export default function PermissionsMatrix() {
  const qc = useQueryClient();
  const callerRank = useAuthStore((s) => s.user?.role_rank ?? 0);
  const { data, isLoading } = useQuery({
    queryKey: ["platform-permissions"],
    queryFn: async () =>
      (await api.get<PlatformPermissionsResponse>("/platform/permissions"))
        .data,
  });
  const rolesQ = useQuery({
    queryKey: ["platform-roles"],
    queryFn: async () => (await api.get<RoleEntry[]>("/platform/roles")).data,
  });
  const ROLES = useMemo(
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

  const mutation = useMutation({
    mutationFn: async (payload: {
      role: string;
      code: string;
      granted: boolean;
    }) => {
      await api.put("/platform/permissions", payload);
    },
    onSuccess: () => {
      toast.success("Permission updated");
      qc.invalidateQueries({ queryKey: ["platform-permissions"] });
    },
    onError: (err) => {
      toast.error(extractErrorMessage(err, "Failed to update permission"));
    },
  });

  const grouped = useMemo(() => {
    const groups: Record<string, PermissionEntry[]> = {};
    for (const p of data?.all_permissions ?? []) {
      (groups[p.category] ??= []).push(p);
    }
    return groups;
  }, [data]);

  const grantedSets = useMemo(() => {
    const sets: Record<string, Set<string>> = {};
    for (const role of ROLES) {
      sets[role] = new Set(data?.role_defaults?.[role] ?? []);
    }
    return sets;
  }, [data, ROLES]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Permission Defaults"
        description="System-wide role defaults. Agencies may override these per role."
      />
      {isLoading || rolesQ.isLoading ? (
        <Card className="p-6 text-sm text-muted-foreground">Loading…</Card>
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="min-w-full text-sm">
            <thead className="border-b border-border bg-muted/30 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="w-72 px-4 py-3">Permission</th>
                {ROLES.map((r) => (
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
                  roles={ROLES}
                  grantedSets={grantedSets}
                  isLocked={isLocked}
                  onToggle={(role, code, granted) =>
                    mutation.mutate({ role, code, granted })
                  }
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
  grantedSets,
  isLocked,
  onToggle,
}: {
  category: string;
  perms: PermissionEntry[];
  roles: string[];
  grantedSets: Record<string, Set<string>>;
  isLocked: (role: string) => boolean;
  onToggle: (role: string, code: string, granted: boolean) => void;
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
            const granted = grantedSets[r]?.has(p.code) ?? false;
            const locked = isLocked(r);
            return (
              <td key={r} className="px-3 py-2 text-center">
                <input
                  type="checkbox"
                  checked={granted}
                  disabled={locked}
                  onChange={(e) => onToggle(r, p.code, e.target.checked)}
                  className="h-4 w-4 cursor-pointer accent-accent disabled:cursor-not-allowed disabled:opacity-40"
                  title={
                    locked
                      ? "Cannot edit a role at or above your own level."
                      : undefined
                  }
                />
              </td>
            );
          })}
        </tr>
      ))}
    </>
  );
}
