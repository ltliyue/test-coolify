import { useQuery } from "@tanstack/react-query";
import { Building2, PauseCircle, ShieldCheck, Sparkles } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { StatCard } from "../../components/widgets/StatCard";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { api } from "../../lib/api";

interface PlatformAgency {
  id: string;
  name: string;
  slug: string;
  plan: string;
  is_suspended: boolean;
  monthly_token_budget: number;
  member_count: number;
  client_count: number;
  created_at: string;
}

interface PlatformInvitation {
  id: string;
  email: string;
  role: string;
  created_at: string;
  accepted_at: string | null;
}

interface MonthlyUsage {
  tokens?: number;
}

// Platform-tier landing page: cross-Agency KPIs + recent activity.
// Endpoints that 4xx are tolerated and the relevant tile renders "—".
export default function PlatformDashboard() {
  const agenciesQ = useQuery({
    queryKey: ["platform", "agencies"],
    queryFn: async () => {
      const res = await api.get<PlatformAgency[]>("/platform/agencies");
      return res.data;
    },
  });

  const invitesQ = useQuery({
    queryKey: ["platform", "invitations"],
    queryFn: async () => {
      try {
        const res = await api.get<PlatformInvitation[]>(
          "/platform/invitations",
        );
        return res.data;
      } catch {
        return [] as PlatformInvitation[];
      }
    },
  });

  const usageQ = useQuery({
    queryKey: ["platform", "monthly-usage"],
    queryFn: async () => {
      try {
        const res = await api.get<MonthlyUsage>("/ai/usage/monthly");
        return res.data;
      } catch {
        return null;
      }
    },
  });

  const agencies = agenciesQ.data ?? [];
  const totalAgencies = agencies.length;
  const suspended = agencies.filter((a) => a.is_suspended).length;
  const totalMembers = agencies.reduce(
    (acc, a) => acc + (a.member_count ?? 0),
    0,
  );
  const tokens = usageQ.data?.tokens;

  const recentAgencies = agencies.slice(0, 10);
  const recentInvites = (invitesQ.data ?? []).slice(0, 8);

  return (
    <div>
      <PageHeader
        title="Platform Overview"
        description="Cross-Agency KPIs for the ReceptivIQ ops team."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Agencies"
          value={String(totalAgencies)}
          icon={Building2}
          loading={agenciesQ.isLoading}
        />
        <StatCard
          label="Active members"
          value={String(totalMembers)}
          icon={ShieldCheck}
          loading={agenciesQ.isLoading}
        />
        <StatCard
          label="Tokens this month"
          value={tokens != null ? tokens.toLocaleString() : "—"}
          icon={Sparkles}
          loading={usageQ.isLoading}
        />
        <StatCard
          label="Suspended"
          value={String(suspended)}
          icon={PauseCircle}
          loading={agenciesQ.isLoading}
        />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold">Recent agencies</h3>
            <span className="text-xs text-muted-foreground">
              Top {recentAgencies.length}
            </span>
          </div>
          {recentAgencies.length === 0 ? (
            <div className="py-6 text-center text-sm text-muted-foreground">
              No agencies yet.
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {recentAgencies.map((a) => (
                <li
                  key={a.id}
                  className="flex items-center justify-between py-2 text-sm"
                >
                  <div>
                    <div className="font-medium">{a.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {a.slug} · {a.plan}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {a.is_suspended ? (
                      <Badge variant="warn">Suspended</Badge>
                    ) : (
                      <Badge variant="success">Active</Badge>
                    )}
                    <span className="text-xs text-muted-foreground">
                      {a.member_count} members
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold">
              Recent platform invitations
            </h3>
            <span className="text-xs text-muted-foreground">
              {recentInvites.length}
            </span>
          </div>
          {recentInvites.length === 0 ? (
            <div className="py-6 text-center text-sm text-muted-foreground">
              No recent invitations.
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {recentInvites.map((inv) => (
                <li
                  key={inv.id}
                  className="flex items-center justify-between py-2 text-sm"
                >
                  <div>
                    <div className="font-medium">{inv.email}</div>
                    <div className="text-xs text-muted-foreground">
                      {inv.role}
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {inv.accepted_at ? "Accepted" : "Pending"}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
