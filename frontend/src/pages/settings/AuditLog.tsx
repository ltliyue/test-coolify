import { useMemo, useState } from "react";
import { useQuery, useInfiniteQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input, Label } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { api } from "../../lib/api";
import { useAuthStore } from "../../lib/auth-store";

interface AuditItem {
  id: number;
  agency_id: string | null;
  agency_name: string | null;
  client_id: string | null;
  client_name: string | null;
  user_id: string | null;
  member_name: string | null;
  member_email: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  request_path: string | null;
  request_method: string | null;
  status_code: number | null;
  success: boolean;
  ip_address: string | null;
  created_at: string;
  extra_data: Record<string, unknown> | null;
}

interface AuditPage {
  items: AuditItem[];
  next_cursor: number | null;
}

interface Member {
  id: string;
  email: string;
  full_name: string;
  agency_id: string | null;
  agency_name: string | null;
}

interface ClientLite {
  id: string;
  name: string;
  agency_id: string;
  agency_name: string | null;
}

interface Props {
  /** If null, this is the platform-wide view (no agency_id query param). */
  scopeAgencyId: string | null;
}

function isoNow(offsetDays: number): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  // strip seconds for datetime-local rendering
  d.setSeconds(0, 0);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
}

export default function AuditLog({ scopeAgencyId }: Props) {
  const [filters, setFilters] = useState({
    user_id: "",
    client_id: "",
    event: "",
    since: isoNow(-7),
    until: isoNow(0),
    status: "all" as "all" | "success" | "failed",
  });

  // /audit-logs/members and /audit-logs/clients are scope-aware on the
  // backend: Agency callers see only their tenant, platform callers see
  // everyone. Works for both Settings → Audit and Platform → Audit.
  const membersQ = useQuery({
    queryKey: ["audit-members", scopeAgencyId],
    queryFn: async () => (await api.get<Member[]>("/audit-logs/members")).data,
  });

  const clientsQ = useQuery({
    queryKey: ["audit-clients", scopeAgencyId],
    queryFn: async () =>
      (await api.get<ClientLite[]>("/audit-logs/clients")).data,
  });

  const queryParams = useMemo(() => {
    const p: Record<string, string> = {};
    if (scopeAgencyId) p.agency_id = scopeAgencyId;
    if (filters.user_id) p.user_id = filters.user_id;
    if (filters.client_id) p.client_id = filters.client_id;
    if (filters.event.trim()) p.event = filters.event.trim();
    if (filters.since) p.since = new Date(filters.since).toISOString();
    if (filters.until) p.until = new Date(filters.until).toISOString();
    if (filters.status === "success") p.success = "true";
    if (filters.status === "failed") p.success = "false";
    p.limit = "100";
    return p;
  }, [filters, scopeAgencyId]);

  const logsQ = useInfiniteQuery({
    queryKey: ["audit-logs", queryParams],
    initialPageParam: undefined as number | undefined,
    queryFn: async ({ pageParam }) => {
      const search = new URLSearchParams(queryParams);
      if (pageParam) search.set("cursor", String(pageParam));
      const { data } = await api.get<AuditPage>(
        `/audit-logs?${search.toString()}`,
      );
      return data;
    },
    getNextPageParam: (last) => last.next_cursor ?? undefined,
  });

  const memberMap = useMemo(() => {
    const m = new Map<string, Member>();
    for (const x of membersQ.data ?? []) m.set(x.id, x);
    return m;
  }, [membersQ.data]);
  const clientMap = useMemo(() => {
    const m = new Map<string, ClientLite>();
    for (const x of clientsQ.data ?? []) m.set(x.id, x);
    return m;
  }, [clientsQ.data]);

  const pages = logsQ.data?.pages ?? [];
  const items = pages.flatMap((p) => p.items);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit log"
        description={
          scopeAgencyId
            ? "Immutable record of actions in your agency."
            : "Cross-tenant audit log (platform admins)."
        }
      />

      <Card className="p-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <div>
            <Label>Member</Label>
            <select
              className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
              value={filters.user_id}
              onChange={(e) =>
                setFilters((f) => ({ ...f, user_id: e.target.value }))
              }
            >
              <option value="">All members</option>
              {(membersQ.data ?? []).map((m) => (
                <option key={m.id} value={m.id}>
                  {m.full_name} ({m.email})
                  {scopeAgencyId === null && m.agency_name
                    ? ` · ${m.agency_name}`
                    : ""}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Client</Label>
            <select
              className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
              value={filters.client_id}
              onChange={(e) =>
                setFilters((f) => ({ ...f, client_id: e.target.value }))
              }
            >
              <option value="">All clients</option>
              {(clientsQ.data ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                  {scopeAgencyId === null && c.agency_name
                    ? ` · ${c.agency_name}`
                    : ""}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Event</Label>
            <Input
              placeholder="e.g. rbac.permission"
              value={filters.event}
              onChange={(e) =>
                setFilters((f) => ({ ...f, event: e.target.value }))
              }
            />
          </div>
          <div>
            <Label>Since</Label>
            <Input
              type="datetime-local"
              value={filters.since}
              onChange={(e) =>
                setFilters((f) => ({ ...f, since: e.target.value }))
              }
            />
          </div>
          <div>
            <Label>Until</Label>
            <Input
              type="datetime-local"
              value={filters.until}
              onChange={(e) =>
                setFilters((f) => ({ ...f, until: e.target.value }))
              }
            />
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <span className="text-xs uppercase tracking-wide text-muted-foreground">
            Status
          </span>
          {(["all", "success", "failed"] as const).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setFilters((f) => ({ ...f, status: s }))}
              className={
                "rounded-full px-3 py-1 text-xs font-medium transition-colors " +
                (filters.status === s
                  ? "bg-accent text-accent-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/70")
              }
            >
              {s[0].toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </Card>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/30 text-left text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="w-8 px-3 py-3"></th>
                <th className="px-3 py-3">When</th>
                <th className="px-3 py-3">Member</th>
                <th className="px-3 py-3">Action</th>
                <th className="px-3 py-3">Resource</th>
                <th className="px-3 py-3">Client</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3">IP</th>
              </tr>
            </thead>
            <tbody>
              {logsQ.isLoading ? (
                <tr>
                  <td colSpan={8} className="px-3 py-6 text-muted-foreground">
                    Loading…
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-3 py-6 text-muted-foreground">
                    No audit events match the current filters.
                  </td>
                </tr>
              ) : (
                items.map((it) => (
                  <Row
                    key={it.id}
                    item={it}
                    memberMap={memberMap}
                    clientMap={clientMap}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
        {logsQ.hasNextPage ? (
          <div className="border-t border-border p-3 text-center">
            <Button
              variant="outline"
              size="sm"
              onClick={() => logsQ.fetchNextPage()}
              loading={logsQ.isFetchingNextPage}
            >
              Load more
            </Button>
          </div>
        ) : null}
      </Card>
    </div>
  );
}

function Row({
  item,
  memberMap,
  clientMap,
}: {
  item: AuditItem;
  memberMap: Map<string, { full_name: string; email: string }>;
  clientMap: Map<string, { name: string }>;
}) {
  const [open, setOpen] = useState(false);
  // Prefer the server-resolved names embedded on the audit item (works
  // cross-tenant for platform admins); fall back to the dropdown's
  // local map; fall back to the raw UUID as a last resort.
  const memberName =
    item.member_name ??
    (item.user_id ? (memberMap.get(item.user_id)?.full_name ?? null) : null);
  const memberEmail =
    item.member_email ??
    (item.user_id ? (memberMap.get(item.user_id)?.email ?? null) : null);
  const clientName =
    item.client_name ??
    (item.client_id ? (clientMap.get(item.client_id)?.name ?? null) : null);
  return (
    <>
      <tr className="border-t border-border align-top">
        <td className="px-3 py-2">
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            className="text-muted-foreground hover:text-foreground"
          >
            {open ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
        </td>
        <td className="px-3 py-2 text-xs text-muted-foreground">
          {new Date(item.created_at).toLocaleString()}
        </td>
        <td className="px-3 py-2">
          {memberName ? (
            <div>
              <div className="font-medium">{memberName}</div>
              {memberEmail && (
                <div className="text-[11px] text-muted-foreground">
                  {memberEmail}
                </div>
              )}
            </div>
          ) : (
            <span className="text-muted-foreground">
              {item.user_id ? item.user_id.slice(0, 8) + "…" : "—"}
            </span>
          )}
        </td>
        <td className="px-3 py-2 font-mono text-xs">{item.action}</td>
        <td className="px-3 py-2 text-xs">
          <span className="font-medium">{item.resource_type}</span>
          {item.resource_id ? (
            <span className="ml-1 text-muted-foreground">
              · {item.resource_id}
            </span>
          ) : null}
        </td>
        <td className="px-3 py-2 text-xs">
          {clientName ??
            (item.client_id ? item.client_id.slice(0, 8) + "…" : "—")}
        </td>
        <td className="px-3 py-2">
          {item.success ? (
            <Badge variant="default">Success</Badge>
          ) : (
            <Badge variant="accent">Failed</Badge>
          )}
        </td>
        <td className="px-3 py-2 font-mono text-[11px] text-muted-foreground">
          {item.ip_address ?? "—"}
        </td>
      </tr>
      {open ? (
        <tr className="border-t border-border/40 bg-muted/10">
          <td></td>
          <td colSpan={7} className="px-3 py-3 text-xs">
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              <KV label="Path" value={item.request_path} />
              <KV label="Method" value={item.request_method} />
              <KV
                label="Status code"
                value={
                  item.status_code != null ? String(item.status_code) : null
                }
              />
            </div>
            <div className="mt-3">
              <div className="mb-1 text-[10px] uppercase tracking-wider text-muted-foreground">
                Extra data
              </div>
              <pre className="overflow-x-auto rounded bg-card p-2 font-mono text-[11px]">
                {item.extra_data
                  ? JSON.stringify(item.extra_data, null, 2)
                  : "—"}
              </pre>
            </div>
          </td>
        </tr>
      ) : null}
    </>
  );
}

function KV({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="font-mono text-xs">{value ?? "—"}</div>
    </div>
  );
}

// Convenience wrapper: pull agency_id from auth-store for the agency view.
export function AuditLogForCurrentAgency() {
  const agencyId = useAuthStore((s) => s.user?.agency_id ?? null);
  return <AuditLog scopeAgencyId={agencyId || null} />;
}

// Platform-wide variant: no agency_id pinning, see all tenants.
export function AuditLogPlatform() {
  return <AuditLog scopeAgencyId={null} />;
}
