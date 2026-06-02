import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Pencil, Trash2, UserCog } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { api, extractErrorMessage } from "../../lib/api";
import { useAuthStore } from "../../lib/auth-store";
import { CreateRoleModal, EditRoleModal } from "../platform/RolesAdmin";

interface Role {
  code: string;
  label: string;
  tier: "platform" | "agency" | "client";
  agency_id: string | null;
  is_system: boolean;
  rank: number;
  description: string | null;
  created_at: string;
  user_count: number;
}

export default function AgencyRolesAdmin() {
  const agencyId = useAuthStore((s) => s.user?.agency_id);
  const callerRank = useAuthStore((s) => s.user?.role_rank ?? 0);
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<Role | null>(null);

  const { data, isLoading } = useQuery({
    enabled: !!agencyId,
    queryKey: ["agency-roles", agencyId],
    queryFn: async () =>
      (await api.get<Role[]>(`/agencies/${agencyId}/roles`)).data,
  });

  const del = useMutation({
    mutationFn: async (code: string) =>
      api.delete(`/agencies/${agencyId}/roles/${code}`),
    onSuccess: () => {
      toast.success("Role deleted");
      qc.invalidateQueries({ queryKey: ["agency-roles", agencyId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  if (!agencyId) {
    return (
      <Card className="p-6 text-sm text-muted-foreground">
        <p className="mb-2 font-medium text-foreground">
          This page manages roles for your Agency.
        </p>
        <p>
          Your account is not bound to an Agency (platform tier). Manage
          system-wide roles at{" "}
          <Link
            to="/platform/roles"
            className="font-medium text-accent underline-offset-4 hover:underline"
          >
            /platform/roles
          </Link>
          .
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Roles"
        description="Custom roles for this Agency. Built-in and system-wide roles are shown read-only."
        actions={
          <Button variant="accent" onClick={() => setShowCreate(true)}>
            <UserCog className="h-4 w-4" />
            New role
          </Button>
        }
      />

      <Card className="overflow-hidden">
        {isLoading ? (
          <div className="px-6 py-8 text-sm text-muted-foreground">
            Loading…
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/30 text-left text-xs uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-6 py-3">Code</th>
                  <th className="px-6 py-3">Label</th>
                  <th className="px-6 py-3">Tier</th>
                  <th className="px-6 py-3">Type</th>
                  <th className="px-6 py-3">Users</th>
                  <th className="px-6 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {(data ?? []).map((r) => {
                  const ownedByAgency = r.agency_id === agencyId;
                  const rankLocked = (r.rank ?? 0) >= callerRank;
                  const canModify =
                    !r.is_system && ownedByAgency && !rankLocked;
                  const lockTip = rankLocked
                    ? "Cannot manage a role at or above your own level."
                    : undefined;
                  return (
                    <tr key={r.code} className="border-t border-border">
                      <td className="px-6 py-3 font-mono text-xs">{r.code}</td>
                      <td className="px-6 py-3">{r.label}</td>
                      <td className="px-6 py-3">
                        <Badge variant="outline">{r.tier}</Badge>
                      </td>
                      <td className="px-6 py-3">
                        {r.is_system ? (
                          <Badge variant="default">Built-in</Badge>
                        ) : ownedByAgency ? (
                          <Badge variant="accent">Custom</Badge>
                        ) : (
                          <Badge variant="outline">System custom</Badge>
                        )}
                      </td>
                      <td className="px-6 py-3 text-muted-foreground">
                        {r.user_count}
                      </td>
                      <td className="px-6 py-3 text-right">
                        <div
                          className="inline-flex items-center gap-2"
                          title={lockTip}
                        >
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={!canModify}
                            onClick={() => setEditing(r)}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                            Edit
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={!canModify || r.user_count > 0}
                            onClick={() => {
                              if (window.confirm(`Delete role '${r.code}'?`)) {
                                del.mutate(r.code);
                              }
                            }}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {showCreate && (
        <CreateRoleModal
          tiers={["agency", "client"]}
          scope="agency"
          agencyId={agencyId}
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            qc.invalidateQueries({ queryKey: ["agency-roles", agencyId] });
          }}
        />
      )}
      {editing && (
        <EditRoleModal
          role={editing}
          scope="agency"
          agencyId={agencyId}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            qc.invalidateQueries({ queryKey: ["agency-roles", agencyId] });
          }}
        />
      )}
    </div>
  );
}
