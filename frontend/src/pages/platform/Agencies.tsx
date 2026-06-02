import { useState } from "react";
import { useForm } from "react-hook-form";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Copy, Pause, Play, Plus, UserPlus, X } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input, Label, FieldError } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { api, extractErrorMessage } from "../../lib/api";

type Plan = "starter" | "growth" | "enterprise";

interface Agency {
  id: string;
  name: string;
  slug: string;
  plan: Plan;
  monthly_token_budget: number;
  is_suspended: boolean;
  suspended_at: string | null;
  suspended_reason: string | null;
  created_at: string;
  member_count: number;
  client_count: number;
}

interface InviteResult {
  invite_url: string;
  raw_token: string;
  expires_at: string;
}

export default function PlatformAgencies() {
  const qc = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [inviteTarget, setInviteTarget] = useState<Agency | null>(null);
  const [suspendTarget, setSuspendTarget] = useState<Agency | null>(null);
  const [createdInvite, setCreatedInvite] = useState<{
    email: string;
    invite: InviteResult;
  } | null>(null);

  const agenciesQ = useQuery({
    queryKey: ["platform", "agencies"],
    queryFn: async () => (await api.get<Agency[]>("/platform/agencies")).data,
  });

  const unsuspend = useMutation({
    mutationFn: async (id: string) =>
      api.post(`/platform/agencies/${id}/unsuspend`),
    onSuccess: () => {
      toast.success("Agency reactivated");
      qc.invalidateQueries({ queryKey: ["platform", "agencies"] });
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  });

  return (
    <>
      <PageHeader
        title="Agencies"
        description="Manage every tenant on the platform."
        actions={
          <Button variant="accent" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" />
            New agency
          </Button>
        }
      />

      <Card className="overflow-hidden">
        {agenciesQ.isLoading ? (
          <div className="px-6 py-8 text-sm text-muted-foreground">
            Loading…
          </div>
        ) : !agenciesQ.data || agenciesQ.data.length === 0 ? (
          <EmptyState
            title="No agencies yet"
            description="Create the first agency to onboard a customer."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/30 text-left text-xs uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-6 py-3">Name</th>
                  <th className="px-6 py-3">Slug</th>
                  <th className="px-6 py-3">Plan</th>
                  <th className="px-6 py-3">Members</th>
                  <th className="px-6 py-3">Clients</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Created</th>
                  <th className="px-6 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {agenciesQ.data.map((a) => (
                  <tr key={a.id} className="border-t border-border">
                    <td className="px-6 py-3 font-medium">{a.name}</td>
                    <td className="px-6 py-3 text-muted-foreground">
                      {a.slug}
                    </td>
                    <td className="px-6 py-3">
                      <Badge variant="outline">{a.plan}</Badge>
                    </td>
                    <td className="px-6 py-3">{a.member_count}</td>
                    <td className="px-6 py-3">{a.client_count}</td>
                    <td className="px-6 py-3">
                      <Badge variant={a.is_suspended ? "warn" : "success"}>
                        {a.is_suspended ? "Suspended" : "Active"}
                      </Badge>
                    </td>
                    <td className="px-6 py-3 text-muted-foreground">
                      {new Date(a.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setInviteTarget(a)}
                        >
                          <UserPlus className="h-4 w-4" />
                          Invite admin
                        </Button>
                        {a.is_suspended ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => unsuspend.mutate(a.id)}
                          >
                            <Play className="h-4 w-4" />
                            Unsuspend
                          </Button>
                        ) : (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSuspendTarget(a)}
                          >
                            <Pause className="h-4 w-4" />
                            Suspend
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {createOpen && (
        <CreateAgencyModal
          onClose={() => setCreateOpen(false)}
          onCreated={() => {
            setCreateOpen(false);
            qc.invalidateQueries({ queryKey: ["platform", "agencies"] });
          }}
        />
      )}

      {inviteTarget && (
        <InviteAdminModal
          agency={inviteTarget}
          onClose={() => setInviteTarget(null)}
          onCreated={(email, invite) => {
            setInviteTarget(null);
            setCreatedInvite({ email, invite });
          }}
        />
      )}

      {suspendTarget && (
        <SuspendModal
          agency={suspendTarget}
          onClose={() => setSuspendTarget(null)}
          onDone={() => {
            setSuspendTarget(null);
            qc.invalidateQueries({ queryKey: ["platform", "agencies"] });
          }}
        />
      )}

      {createdInvite && (
        <InviteLinkModal
          email={createdInvite.email}
          invite={createdInvite.invite}
          onClose={() => setCreatedInvite(null)}
        />
      )}
    </>
  );
}

interface CreateForm {
  name: string;
  plan: Plan;
}

function CreateAgencyModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateForm>({ defaultValues: { name: "", plan: "starter" } });

  const onSubmit = async (values: CreateForm) => {
    try {
      await api.post("/platform/agencies", values);
      toast.success("Agency created");
      onCreated();
    } catch (err) {
      toast.error(extractErrorMessage(err));
    }
  };

  return (
    <ModalShell title="New agency" onClose={onClose}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="agency-name">Name</Label>
          <Input
            id="agency-name"
            invalid={!!errors.name}
            {...register("name", { required: "Name is required" })}
          />
          <FieldError message={errors.name?.message} />
        </div>
        <div>
          <Label>Plan</Label>
          <div className="space-y-2">
            {(["starter", "growth", "enterprise"] as Plan[]).map((p) => (
              <label
                key={p}
                className="flex items-center gap-2 text-sm text-foreground"
              >
                <input type="radio" value={p} {...register("plan")} />
                <span className="capitalize">{p}</span>
              </label>
            ))}
          </div>
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

function InviteAdminModal({
  agency,
  onClose,
  onCreated,
}: {
  agency: Agency;
  onClose: () => void;
  onCreated: (email: string, invite: InviteResult) => void;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<{ email: string }>({ defaultValues: { email: "" } });

  const onSubmit = async (values: { email: string }) => {
    try {
      const res = await api.post<InviteResult>(
        `/platform/agencies/${agency.id}/invite-admin`,
        { email: values.email },
      );
      onCreated(values.email, res.data);
    } catch (err) {
      toast.error(extractErrorMessage(err));
    }
  };

  return (
    <ModalShell title={`Invite admin to ${agency.name}`} onClose={onClose}>
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

function SuspendModal({
  agency,
  onClose,
  onDone,
}: {
  agency: Agency;
  onClose: () => void;
  onDone: () => void;
}) {
  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<{ reason: string }>({ defaultValues: { reason: "" } });

  const onSubmit = async (values: { reason: string }) => {
    try {
      await api.post(`/platform/agencies/${agency.id}/suspend`, {
        reason: values.reason || null,
      });
      toast.success("Agency suspended");
      onDone();
    } catch (err) {
      toast.error(extractErrorMessage(err));
    }
  };

  return (
    <ModalShell title={`Suspend ${agency.name}`} onClose={onClose}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Users of this agency will be denied login until reactivated.
        </p>
        <div>
          <Label htmlFor="suspend-reason">Reason (optional)</Label>
          <Input id="suspend-reason" {...register("reason")} />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="accent" loading={isSubmitting}>
            Suspend
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
