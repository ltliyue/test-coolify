import { useState } from "react";
import { useForm } from "react-hook-form";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Copy, ShieldCheck, UserPlus, X } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input, Label, FieldError } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { api, extractErrorMessage } from "../../lib/api";
import { useAuthStore } from "../../lib/auth-store";

type PlatformRole = "platform_super_admin" | "platform_admin";

interface PlatformUser {
  id: string;
  email: string;
  full_name: string;
  role: PlatformRole;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

interface InviteResult {
  invite_url: string;
  raw_token: string;
  expires_at: string;
  role: string;
}

export default function PlatformUsersPage() {
  const role = useAuthStore((s) => s.user?.role);
  const isSuper = role === "platform_super_admin";
  const [inviteOpen, setInviteOpen] = useState(false);
  const [created, setCreated] = useState<{
    email: string;
    invite: InviteResult;
  } | null>(null);

  const usersQ = useQuery({
    queryKey: ["platform", "users"],
    queryFn: async () =>
      (await api.get<PlatformUser[]>("/platform/users")).data,
  });

  return (
    <>
      <PageHeader
        title="Platform users"
        description="ReceptivIQ ops team members with cross-agency privileges."
        actions={
          isSuper && (
            <Button variant="accent" onClick={() => setInviteOpen(true)}>
              <UserPlus className="h-4 w-4" />
              Invite platform user
            </Button>
          )
        }
      />

      <Card className="overflow-hidden">
        {usersQ.isLoading ? (
          <div className="px-6 py-8 text-sm text-muted-foreground">
            Loading…
          </div>
        ) : !usersQ.data || usersQ.data.length === 0 ? (
          <EmptyState
            icon={<ShieldCheck className="h-5 w-5" />}
            title="No platform users yet"
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
                </tr>
              </thead>
              <tbody>
                {usersQ.data.map((u) => (
                  <tr key={u.id} className="border-t border-border">
                    <td className="px-6 py-3">{u.full_name || "—"}</td>
                    <td className="px-6 py-3 text-muted-foreground">
                      {u.email}
                    </td>
                    <td className="px-6 py-3">
                      <Badge
                        variant={
                          u.role === "platform_super_admin"
                            ? "accent"
                            : "default"
                        }
                      >
                        {u.role === "platform_super_admin"
                          ? "Super admin"
                          : "Admin"}
                      </Badge>
                    </td>
                    <td className="px-6 py-3">
                      <Badge variant={u.is_active ? "success" : "warn"}>
                        {u.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </td>
                    <td className="px-6 py-3 text-muted-foreground">
                      {u.last_login_at
                        ? new Date(u.last_login_at).toLocaleString()
                        : "Never"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {inviteOpen && (
        <InviteModal
          allowSuper={isSuper}
          onClose={() => setInviteOpen(false)}
          onCreated={(email, invite) => {
            setInviteOpen(false);
            setCreated({ email, invite });
          }}
        />
      )}

      {created && (
        <InviteLinkModal
          email={created.email}
          invite={created.invite}
          onClose={() => setCreated(null)}
        />
      )}
    </>
  );
}

interface InviteForm {
  email: string;
  role: PlatformRole;
}

function InviteModal({
  allowSuper,
  onClose,
  onCreated,
}: {
  allowSuper: boolean;
  onClose: () => void;
  onCreated: (email: string, invite: InviteResult) => void;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<InviteForm>({
    defaultValues: { email: "", role: "platform_admin" },
  });

  const onSubmit = async (values: InviteForm) => {
    try {
      const res = await api.post<InviteResult>("/platform/users/invitations", {
        email: values.email,
        role: values.role,
      });
      toast.success("Invitation created");
      onCreated(values.email, res.data);
    } catch (err) {
      toast.error(extractErrorMessage(err));
    }
  };

  return (
    <ModalShell title="Invite platform user" onClose={onClose}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="pu-email">Email</Label>
          <Input
            id="pu-email"
            type="email"
            invalid={!!errors.email}
            {...register("email", { required: "Email is required" })}
          />
          <FieldError message={errors.email?.message} />
        </div>
        <div>
          <Label>Role</Label>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-foreground">
              <input
                type="radio"
                value="platform_admin"
                {...register("role")}
              />
              <span>Platform admin</span>
            </label>
            {allowSuper && (
              <label className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="radio"
                  value="platform_super_admin"
                  {...register("role")}
                />
                <span>Platform super admin</span>
              </label>
            )}
          </div>
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
  email,
  invite,
  onClose,
}: {
  email: string;
  invite: InviteResult;
  onClose: () => void;
}) {
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(invite.invite_url);
      toast.success("Link copied");
    } catch {
      toast.error("Copy failed");
    }
  };
  return (
    <ModalShell title="Invitation created" onClose={onClose}>
      <p className="text-sm text-muted-foreground">
        Share the link below with <strong>{email}</strong>. It expires on{" "}
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
          Copy
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
