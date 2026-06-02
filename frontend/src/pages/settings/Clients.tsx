import { useState } from "react";
import { useForm } from "react-hook-form";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Briefcase, Plus, X, Users, Copy, Check } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input, Label, FieldError } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { api, extractErrorMessage } from "../../lib/api";
import { useAuthStore } from "../../lib/auth-store";

type Role = string;

interface Member {
  id: string;
  full_name: string;
  email: string;
  role: Role;
  client_id: string | null;
  is_active: boolean;
  last_login_at: string | null;
}

interface RoleEntry {
  code: string;
  label: string;
  tier: string;
  is_system: boolean;
}

interface ClientRow {
  id: string;
  agency_id: string;
  name: string;
  slug: string;
  status: string;
  created_at: string;
}

interface ClientForm {
  name: string;
}

interface InvitationCreated {
  id: string;
  email: string;
  role: Role;
  invite_url: string;
  raw_token: string;
  expires_at: string;
}

export default function ClientsPage() {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "agency_admin";
  const agencyId = user?.agency_id;
  const qc = useQueryClient();
  const [newClientOpen, setNewClientOpen] = useState(false);
  const [viewersFor, setViewersFor] = useState<ClientRow | null>(null);

  const clientsQ = useQuery({
    queryKey: ["tenants", "clients", agencyId],
    queryFn: async () =>
      (await api.get<ClientRow[]>(`/tenants/agencies/${agencyId}/clients`))
        .data,
    enabled: Boolean(agencyId),
  });

  const membersQ = useQuery({
    queryKey: ["team", "members"],
    queryFn: async () => (await api.get<Member[]>("/team/members")).data,
  });

  const viewersOf = (clientId: string) =>
    (membersQ.data ?? []).filter(
      (m) => m.role === "client_viewer" && m.client_id === clientId,
    );

  return (
    <>
      <PageHeader
        title="Clients"
        description="Sub-tenants within your agency. Each has its own viewers and brand config."
        actions={
          isAdmin && (
            <Button variant="accent" onClick={() => setNewClientOpen(true)}>
              <Plus className="h-4 w-4" />
              New client
            </Button>
          )
        }
      />

      <Card className="overflow-hidden">
        {clientsQ.isLoading ? (
          <div className="px-6 py-8 text-sm text-muted-foreground">
            Loading…
          </div>
        ) : !clientsQ.data || clientsQ.data.length === 0 ? (
          <EmptyState
            icon={<Briefcase className="h-5 w-5" />}
            title="No clients yet"
            description="Create your first client to start organizing campaigns by sub-tenant."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/30 text-left text-xs uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-6 py-3">Name</th>
                  <th className="px-6 py-3">Slug</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Created</th>
                  <th className="px-6 py-3">Viewers</th>
                  <th className="px-6 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {clientsQ.data.map((c) => (
                  <tr key={c.id} className="border-t border-border">
                    <td className="px-6 py-3 font-medium">{c.name}</td>
                    <td className="px-6 py-3 text-muted-foreground">
                      {c.slug}
                    </td>
                    <td className="px-6 py-3">
                      <Badge
                        variant={c.status === "active" ? "success" : "warn"}
                      >
                        {c.status}
                      </Badge>
                    </td>
                    <td className="px-6 py-3 text-muted-foreground">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-3 text-muted-foreground">
                      {viewersOf(c.id).length}
                    </td>
                    <td className="px-6 py-3 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setViewersFor(c)}
                      >
                        <Users className="h-4 w-4" />
                        Manage viewers
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {newClientOpen && (
        <NewClientModal
          agencyId={agencyId!}
          onClose={() => setNewClientOpen(false)}
          onCreated={() => {
            setNewClientOpen(false);
            qc.invalidateQueries({
              queryKey: ["tenants", "clients", agencyId],
            });
          }}
        />
      )}

      {viewersFor && (
        <ManageViewersModal
          client={viewersFor}
          viewers={viewersOf(viewersFor.id)}
          isAdmin={isAdmin}
          onClose={() => setViewersFor(null)}
        />
      )}
    </>
  );
}

function NewClientModal({
  agencyId,
  onClose,
  onCreated,
}: {
  agencyId: string;
  onClose: () => void;
  onCreated: () => void;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ClientForm>({ defaultValues: { name: "" } });

  const onSubmit = async (values: ClientForm) => {
    try {
      await api.post(`/tenants/agencies/${agencyId}/clients`, {
        name: values.name,
        agency_id: agencyId,
      });
      toast.success("Client created");
      onCreated();
    } catch (err) {
      toast.error(extractErrorMessage(err));
    }
  };

  return (
    <ModalShell title="New client" onClose={onClose}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="client-name">Name</Label>
          <Input
            id="client-name"
            invalid={!!errors.name}
            {...register("name", { required: "Name is required" })}
          />
          <FieldError message={errors.name?.message} />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="accent" loading={isSubmitting}>
            Create
          </Button>
        </div>
      </form>
    </ModalShell>
  );
}

function ManageViewersModal({
  client,
  viewers,
  isAdmin,
  onClose,
}: {
  client: ClientRow;
  viewers: Member[];
  isAdmin: boolean;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [created, setCreated] = useState<InvitationCreated | null>(null);
  const [showInvite, setShowInvite] = useState(false);

  const deactivate = useMutation({
    mutationFn: async (id: string) =>
      api.patch(`/team/members/${id}`, { is_active: false }),
    onSuccess: () => {
      toast.success("Viewer deactivated");
      qc.invalidateQueries({ queryKey: ["team", "members"] });
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  return (
    <ModalShell title={`Viewers · ${client.name}`} onClose={onClose} wide>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          People who can see the white-label portal for{" "}
          <span className="font-medium text-foreground">{client.name}</span>{" "}
          only.
        </p>
        {isAdmin && !showInvite && (
          <Button
            variant="accent"
            size="sm"
            onClick={() => setShowInvite(true)}
          >
            <Plus className="h-4 w-4" />
            Invite viewer
          </Button>
        )}
      </div>

      {showInvite && (
        <InviteViewerForm
          clientId={client.id}
          onCancel={() => setShowInvite(false)}
          onCreated={(inv) => {
            setCreated(inv);
            setShowInvite(false);
            qc.invalidateQueries({ queryKey: ["team", "members"] });
            qc.invalidateQueries({ queryKey: ["team", "invitations"] });
          }}
        />
      )}

      {created && (
        <InviteLinkBox invite={created} onDone={() => setCreated(null)} />
      )}

      {viewers.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border px-6 py-10 text-center">
          <Users className="mx-auto h-5 w-5 text-muted-foreground" />
          <p className="mt-2 text-sm font-medium">No viewers yet</p>
          <p className="text-xs text-muted-foreground">
            Invite a stakeholder to give them read-only access to this client's
            portal.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-muted/30 text-left text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Email</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Last login</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {viewers.map((v) => (
                <tr key={v.id} className="border-t border-border">
                  <td className="px-4 py-2">{v.full_name || "—"}</td>
                  <td className="px-4 py-2 text-muted-foreground">{v.email}</td>
                  <td className="px-4 py-2">
                    <Badge variant={v.is_active ? "success" : "warn"}>
                      {v.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">
                    {v.last_login_at
                      ? new Date(v.last_login_at).toLocaleString()
                      : "Never"}
                  </td>
                  <td className="px-4 py-2 text-right">
                    {isAdmin && v.is_active && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deactivate.mutate(v.id)}
                      >
                        Deactivate
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex justify-end pt-4">
        <Button variant="outline" onClick={onClose}>
          Close
        </Button>
      </div>
    </ModalShell>
  );
}

function InviteViewerForm({
  clientId,
  onCancel,
  onCreated,
}: {
  clientId: string;
  onCancel: () => void;
  onCreated: (inv: InvitationCreated) => void;
}) {
  const agencyId = useAuthStore((s) => s.user?.agency_id);
  const rolesQ = useQuery({
    enabled: !!agencyId,
    queryKey: ["agency-roles", agencyId],
    queryFn: async () =>
      (await api.get<RoleEntry[]>(`/agencies/${agencyId}/roles`)).data,
  });
  const clientTierRoles = (rolesQ.data ?? []).filter(
    (r) => r.tier === "client",
  );
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<{ email: string; role: string }>({
    defaultValues: { email: "", role: "client_viewer" },
  });

  const onSubmit = async (values: { email: string; role: string }) => {
    try {
      const res = await api.post<InvitationCreated>("/team/invitations", {
        email: values.email,
        role: values.role,
        client_id: clientId,
      });
      toast.success("Invitation created");
      onCreated(res.data);
    } catch (err) {
      toast.error(extractErrorMessage(err));
    }
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="mb-4 rounded-lg border border-border bg-muted/20 p-4"
    >
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <Label htmlFor="viewer-email">Viewer email</Label>
          <Input
            id="viewer-email"
            type="email"
            invalid={!!errors.email}
            {...register("email", { required: "Email is required" })}
          />
          <FieldError message={errors.email?.message} />
        </div>
        {clientTierRoles.length > 1 && (
          <div>
            <Label htmlFor="viewer-role">Role</Label>
            <select
              id="viewer-role"
              {...register("role")}
              className="h-9 rounded-md border border-border bg-background px-2 text-sm"
            >
              {clientTierRoles.map((r) => (
                <option key={r.code} value={r.code}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
        )}
        <Button type="submit" variant="accent" loading={isSubmitting}>
          Send invite
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

function InviteLinkBox({
  invite,
  onDone,
}: {
  invite: InvitationCreated;
  onDone: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(invite.invite_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div className="mb-4 rounded-lg border border-accent/40 bg-accent/5 p-4">
      <p className="text-xs font-medium uppercase tracking-wider text-accent">
        Invitation link · share with {invite.email}
      </p>
      <div className="mt-2 flex items-center gap-2">
        <code className="flex-1 overflow-x-auto rounded bg-background px-2 py-1.5 text-xs">
          {invite.invite_url}
        </code>
        <Button variant="outline" size="sm" onClick={copy}>
          {copied ? (
            <Check className="h-4 w-4" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
          {copied ? "Copied" : "Copy"}
        </Button>
        <Button variant="ghost" size="sm" onClick={onDone}>
          Dismiss
        </Button>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        Expires {new Date(invite.expires_at).toLocaleString()}. Single-use.
      </p>
    </div>
  );
}

function ModalShell({
  title,
  onClose,
  wide,
  children,
}: {
  title: string;
  onClose: () => void;
  wide?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div
        className={
          "w-full rounded-xl border border-border bg-card p-6 shadow-lg " +
          (wide ? "max-w-3xl" : "max-w-md")
        }
      >
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
