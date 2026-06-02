import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Copy, Mail, Trash2, UserPlus, X } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input, Label, FieldError } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { api, extractErrorMessage } from "../../lib/api";
import { useAuthStore } from "../../lib/auth-store";

type Role = "agency_admin" | "agency_ops" | "client_viewer";

interface Member {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  client_id: string | null;
  is_active: boolean;
  last_login_at: string | null;
}

interface Invitation {
  id: string;
  email: string;
  role: Role;
  client_id: string | null;
  invited_by: string;
  expires_at: string;
  accepted_at: string | null;
  revoked_at: string | null;
  created_at: string;
}

interface InvitationCreated extends Invitation {
  invite_url: string;
  raw_token: string;
}

const ROLE_LABEL: Record<Role, string> = {
  agency_admin: "Admin",
  agency_ops: "Ops",
  client_viewer: "Client viewer",
};

function roleBadge(role: Role) {
  const variant =
    role === "agency_admin"
      ? "accent"
      : role === "agency_ops"
        ? "default"
        : "outline";
  return <Badge variant={variant}>{ROLE_LABEL[role]}</Badge>;
}

export default function TeamPage() {
  const qc = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "agency_admin";
  const [inviteOpen, setInviteOpen] = useState(false);
  const [createdInvite, setCreatedInvite] = useState<InvitationCreated | null>(
    null,
  );

  // Fetch ALL members (shared cache key so Clients.tsx reuses the same
  // payload). The Agency-tier filter is applied at render time below so
  // it doesn't poison the cache for other pages.
  const membersQ = useQuery({
    queryKey: ["team", "members"],
    queryFn: async () => (await api.get<Member[]>("/team/members")).data,
  });
  const agencyMembers = (membersQ.data ?? []).filter(
    (m) => m.role !== "client_viewer",
  );

  const invitationsQ = useQuery({
    queryKey: ["team", "invitations"],
    queryFn: async () =>
      (await api.get<Invitation[]>("/team/invitations")).data,
    enabled: isAdmin,
  });

  const revoke = useMutation({
    mutationFn: async (id: string) => api.delete(`/team/invitations/${id}`),
    onSuccess: () => {
      toast.success("Invitation revoked");
      qc.invalidateQueries({ queryKey: ["team", "invitations"] });
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  const updateMember = useMutation({
    mutationFn: async (vars: { id: string; is_active?: boolean }) =>
      api.patch(`/team/members/${vars.id}`, { is_active: vars.is_active }),
    onSuccess: () => {
      toast.success("Member updated");
      qc.invalidateQueries({ queryKey: ["team", "members"] });
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  return (
    <>
      <PageHeader
        title="Team members"
        description="Invite teammates, manage roles, and revoke pending invitations."
        actions={
          isAdmin && (
            <Button variant="accent" onClick={() => setInviteOpen(true)}>
              <UserPlus className="h-4 w-4" />
              Invite member
            </Button>
          )
        }
      />

      <Card className="overflow-hidden">
        <div className="border-b border-border px-6 py-4">
          <h3 className="text-sm font-semibold">Members</h3>
        </div>
        {membersQ.isLoading ? (
          <div className="px-6 py-8 text-sm text-muted-foreground">
            Loading…
          </div>
        ) : agencyMembers.length === 0 ? (
          <EmptyState
            title="No members yet"
            description="Invite teammates to collaborate in this workspace."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/30 text-left text-xs uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-6 py-3">Name</th>
                  <th className="px-6 py-3">Email</th>
                  <th className="px-6 py-3">Role</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Last login</th>
                  <th className="px-6 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {agencyMembers.map((m) => (
                  <tr key={m.id} className="border-t border-border">
                    <td className="px-6 py-3">{m.full_name || "—"}</td>
                    <td className="px-6 py-3 text-muted-foreground">
                      {m.email}
                    </td>
                    <td className="px-6 py-3">{roleBadge(m.role)}</td>
                    <td className="px-6 py-3">
                      <Badge variant={m.is_active ? "success" : "warn"}>
                        {m.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </td>
                    <td className="px-6 py-3 text-muted-foreground">
                      {m.last_login_at
                        ? new Date(m.last_login_at).toLocaleString()
                        : "Never"}
                    </td>
                    <td className="px-6 py-3 text-right">
                      {isAdmin && m.id !== user?.id && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            updateMember.mutate({
                              id: m.id,
                              is_active: !m.is_active,
                            })
                          }
                        >
                          {m.is_active ? "Deactivate" : "Activate"}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {isAdmin && (
        <Card className="mt-6 overflow-hidden">
          <div className="border-b border-border px-6 py-4">
            <h3 className="text-sm font-semibold">Pending invitations</h3>
          </div>
          {invitationsQ.isLoading ? (
            <div className="px-6 py-8 text-sm text-muted-foreground">
              Loading…
            </div>
          ) : !invitationsQ.data ||
            invitationsQ.data.filter(
              (i) =>
                !i.accepted_at && !i.revoked_at && i.role !== "client_viewer",
            ).length === 0 ? (
            <EmptyState
              icon={<Mail className="h-5 w-5" />}
              title="No pending invitations"
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/30 text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th className="px-6 py-3">Email</th>
                    <th className="px-6 py-3">Role</th>
                    <th className="px-6 py-3">Expires</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {invitationsQ.data
                    .filter((inv) => inv.role !== "client_viewer")
                    .map((inv) => {
                      const expired = new Date(inv.expires_at) < new Date();
                      const status = inv.accepted_at
                        ? "Accepted"
                        : inv.revoked_at
                          ? "Revoked"
                          : expired
                            ? "Expired"
                            : "Pending";
                      return (
                        <tr key={inv.id} className="border-t border-border">
                          <td className="px-6 py-3">{inv.email}</td>
                          <td className="px-6 py-3">{roleBadge(inv.role)}</td>
                          <td className="px-6 py-3 text-muted-foreground">
                            {new Date(inv.expires_at).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-3">
                            <Badge
                              variant={
                                status === "Pending"
                                  ? "accent"
                                  : status === "Accepted"
                                    ? "success"
                                    : "warn"
                              }
                            >
                              {status}
                            </Badge>
                          </td>
                          <td className="px-6 py-3 text-right">
                            {status === "Pending" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => revoke.mutate(inv.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                                Revoke
                              </Button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {inviteOpen && (
        <InviteModal
          onClose={() => setInviteOpen(false)}
          onCreated={(inv) => {
            setCreatedInvite(inv);
            setInviteOpen(false);
            qc.invalidateQueries({ queryKey: ["team", "invitations"] });
          }}
        />
      )}

      {createdInvite && (
        <InviteLinkModal
          invite={createdInvite}
          onClose={() => setCreatedInvite(null)}
        />
      )}
    </>
  );
}

interface InviteForm {
  email: string;
  role: string;
}

interface RoleEntry {
  code: string;
  label: string;
  tier: string;
  is_system: boolean;
}

function InviteModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (inv: InvitationCreated) => void;
}) {
  const agencyId = useAuthStore((s) => s.user?.agency_id);
  const rolesQ = useQuery({
    enabled: !!agencyId,
    queryKey: ["agency-roles", agencyId],
    queryFn: async () =>
      (await api.get<RoleEntry[]>(`/agencies/${agencyId}/roles`)).data,
  });
  // Invite modal handles Agency-tier members only. Client viewers are
  // invited from Settings > Clients via per-Client modal.
  const agencyTierRoles = (rolesQ.data ?? []).filter(
    (r) => r.tier === "agency",
  );
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<InviteForm>({
    defaultValues: { email: "", role: "agency_ops" },
  });

  const onSubmit = async (values: InviteForm) => {
    try {
      const body: Record<string, unknown> = {
        email: values.email,
        role: values.role,
      };
      const res = await api.post<InvitationCreated>("/team/invitations", body);
      toast.success("Invitation created");
      onCreated(res.data);
    } catch (err) {
      toast.error(extractErrorMessage(err));
    }
  };

  return (
    <ModalShell title="Invite member" onClose={onClose}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="invite-email">Email</Label>
          <Input
            id="invite-email"
            type="email"
            invalid={!!errors.email}
            {...register("email", { required: "Email is required" })}
          />
          <FieldError message={errors.email?.message} />
        </div>

        <div>
          <Label>Role</Label>
          <div className="space-y-2">
            {/* Agency-tier roles only — client_viewer invitations live on each Client page. */}
            {rolesQ.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading roles…</p>
            ) : (
              agencyTierRoles.map((r) => (
                <label
                  key={r.code}
                  className="flex items-center gap-2 text-sm text-foreground"
                >
                  <input type="radio" value={r.code} {...register("role")} />
                  <span>{r.label}</span>
                </label>
              ))
            )}
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            To invite a client viewer, go to Settings → Clients and choose the
            target Client.
          </p>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="accent" loading={isSubmitting}>
            Send invite
          </Button>
        </div>
      </form>
    </ModalShell>
  );
}

function InviteLinkModal({
  invite,
  onClose,
}: {
  invite: InvitationCreated;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(invite.invite_url);
      setCopied(true);
      toast.success("Link copied");
    } catch {
      toast.error("Copy failed");
    }
  };

  useEffect(() => {
    if (!copied) return;
    const t = setTimeout(() => setCopied(false), 2000);
    return () => clearTimeout(t);
  }, [copied]);

  return (
    <ModalShell title="Invitation created" onClose={onClose}>
      <p className="text-sm text-muted-foreground">
        Email delivery is not configured in this environment. Share the
        following link with <strong>{invite.email}</strong>. It expires on{" "}
        {new Date(invite.expires_at).toLocaleDateString()}.
      </p>
      <div className="mt-4 flex items-center gap-2">
        <Input
          value={invite.invite_url}
          readOnly
          className="font-mono text-xs"
        />
        <Button variant="outline" onClick={copy}>
          <Copy className="h-4 w-4" />
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
      <div className="flex justify-end pt-4">
        <Button onClick={onClose}>Done</Button>
      </div>
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
