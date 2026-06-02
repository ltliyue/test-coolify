import { useState } from "react";
import { useForm } from "react-hook-form";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Pencil, Trash2, UserCog, X } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input, Label, FieldError } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { api, extractErrorMessage } from "../../lib/api";
import { useAuthStore } from "../../lib/auth-store";

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

interface CreateRoleForm {
  code: string;
  label: string;
  tier: "platform" | "agency" | "client";
  rank: number;
  description?: string;
}

export default function PlatformRolesAdmin() {
  const qc = useQueryClient();
  const callerRank = useAuthStore((s) => s.user?.role_rank ?? 0);
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<Role | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["platform-roles"],
    queryFn: async () => (await api.get<Role[]>("/platform/roles")).data,
  });

  const del = useMutation({
    mutationFn: async (code: string) => api.delete(`/platform/roles/${code}`),
    onSuccess: () => {
      toast.success("Role deleted");
      qc.invalidateQueries({ queryKey: ["platform-roles"] });
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Roles"
        description="System-wide role catalogue. Built-in roles are immutable."
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
                  const rankLocked = (r.rank ?? 0) >= callerRank;
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
                        ) : (
                          <Badge variant="accent">Custom</Badge>
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
                            disabled={r.is_system || rankLocked}
                            onClick={() => setEditing(r)}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                            Edit
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={
                              r.is_system || rankLocked || r.user_count > 0
                            }
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
          tiers={["platform", "agency", "client"]}
          scope="platform"
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            qc.invalidateQueries({ queryKey: ["platform-roles"] });
          }}
        />
      )}
      {editing && (
        <EditRoleModal
          role={editing}
          scope="platform"
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            qc.invalidateQueries({ queryKey: ["platform-roles"] });
          }}
        />
      )}
    </div>
  );
}

export function CreateRoleModal({
  tiers,
  scope,
  agencyId,
  onClose,
  onCreated,
}: {
  tiers: ("platform" | "agency" | "client")[];
  scope: "platform" | "agency";
  agencyId?: string;
  onClose: () => void;
  onCreated: () => void;
}) {
  const callerRank = useAuthStore((s) => s.user?.role_rank ?? 0);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateRoleForm>({
    defaultValues: {
      code: "",
      label: "",
      tier: tiers[0],
      rank: Math.max(0, callerRank - 1),
      description: "",
    },
  });

  const onSubmit = async (values: CreateRoleForm) => {
    try {
      const url =
        scope === "platform"
          ? "/platform/roles"
          : `/agencies/${agencyId}/roles`;
      await api.post(url, {
        ...values,
        rank: values.rank == null ? undefined : Number(values.rank),
      });
      toast.success("Role created");
      onCreated();
    } catch (err) {
      toast.error(extractErrorMessage(err));
    }
  };

  return (
    <ModalShell title="New role" onClose={onClose}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="role-code">Code (slug)</Label>
          <Input
            id="role-code"
            placeholder="e.g. agency_creative_lead"
            invalid={!!errors.code}
            {...register("code", {
              required: "Code is required",
              pattern: {
                value: /^[a-z][a-z0-9_]{2,63}$/,
                message:
                  "Lowercase letters, digits, underscores; 3-64 chars; start with a letter",
              },
            })}
          />
          <FieldError message={errors.code?.message} />
        </div>
        <div>
          <Label htmlFor="role-label">Label</Label>
          <Input
            id="role-label"
            invalid={!!errors.label}
            {...register("label", { required: "Label is required" })}
          />
          <FieldError message={errors.label?.message} />
        </div>
        <div>
          <Label>Tier</Label>
          <div className="space-y-2">
            {tiers.map((t) => (
              <label
                key={t}
                className="flex items-center gap-2 text-sm text-foreground"
              >
                <input type="radio" value={t} {...register("tier")} />
                <span className="capitalize">{t}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <Label htmlFor="role-rank">Rank</Label>
          <Input
            id="role-rank"
            type="number"
            min={0}
            max={callerRank - 1}
            invalid={!!errors.rank}
            {...register("rank", {
              valueAsNumber: true,
              required: "Rank is required",
              min: { value: 0, message: "Must be >= 0" },
              max: {
                value: callerRank - 1,
                message: `Must be less than your rank (${callerRank})`,
              },
            })}
          />
          <FieldError message={errors.rank?.message} />
          <p className="mt-1 text-[11px] text-muted-foreground">
            Your rank: {callerRank}. New role must rank below you.
          </p>
        </div>
        <div>
          <Label htmlFor="role-desc">Description (optional)</Label>
          <Input id="role-desc" {...register("description")} />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="accent" loading={isSubmitting}>
            Create role
          </Button>
        </div>
      </form>
    </ModalShell>
  );
}

export function EditRoleModal({
  role,
  scope,
  agencyId,
  onClose,
  onSaved,
}: {
  role: Role;
  scope: "platform" | "agency";
  agencyId?: string;
  onClose: () => void;
  onSaved: () => void;
}) {
  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<{ label: string; description: string }>({
    defaultValues: {
      label: role.label,
      description: role.description ?? "",
    },
  });

  const onSubmit = async (values: { label: string; description: string }) => {
    try {
      const url =
        scope === "platform"
          ? `/platform/roles/${role.code}`
          : `/agencies/${agencyId}/roles/${role.code}`;
      await api.patch(url, values);
      toast.success("Role updated");
      onSaved();
    } catch (err) {
      toast.error(extractErrorMessage(err));
    }
  };

  return (
    <ModalShell title={`Edit ${role.code}`} onClose={onClose}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="edit-label">Label</Label>
          <Input id="edit-label" {...register("label", { required: true })} />
        </div>
        <div>
          <Label htmlFor="edit-desc">Description</Label>
          <Input id="edit-desc" {...register("description")} />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="accent" loading={isSubmitting}>
            Save
          </Button>
        </div>
      </form>
    </ModalShell>
  );
}

function ModalShell({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
