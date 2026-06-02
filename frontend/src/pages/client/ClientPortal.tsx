import { useQuery } from "@tanstack/react-query";
import { FileBarChart, Sparkles, Users } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { StatCard } from "../../components/widgets/StatCard";
import { Card } from "../../components/ui/Card";
import { api } from "../../lib/api";

interface PortalBrand {
  tagline?: string;
  brand_voice?: string;
  recommended_tone?: string;
  industry?: string;
  agency_name?: string;
}

interface PortalDashboardSummary {
  brand: PortalBrand;
  persona_count: number;
  creative_count: number;
  report_count: number;
}

interface PortalReport {
  id: string;
  title: string;
  report_type: string;
  status: string;
  created_at: string;
}

// Client-tier landing surface (client_viewer role). White-label header
// pulls from the parent Agency's brand config; stat cards and the recent
// reports list are read-only.
export default function ClientPortal() {
  const dashQ = useQuery({
    queryKey: ["client", "dashboard"],
    queryFn: async () => {
      const res = await api.get<PortalDashboardSummary>("/portal/dashboard");
      return res.data;
    },
  });

  const reportsQ = useQuery({
    queryKey: ["client", "reports"],
    queryFn: async () => {
      const res = await api.get<PortalReport[]>("/portal/reports");
      return res.data;
    },
  });

  const brand = dashQ.data?.brand;
  const tagline = brand?.tagline ?? "Your campaign workspace.";

  return (
    <div>
      <Card className="mb-6 overflow-hidden border-accent/30 bg-gradient-to-br from-accent/15 via-accent/5 to-transparent p-6">
        <div className="text-xs uppercase tracking-wider text-muted-foreground">
          {brand?.agency_name ?? "Your Agency"}
        </div>
        <div className="mt-1 text-2xl font-semibold tracking-tight">
          {tagline}
        </div>
        {brand?.industry && (
          <div className="mt-1 text-sm text-muted-foreground">
            {brand.industry}
          </div>
        )}
      </Card>

      <PageHeader
        title="My Workspace"
        description="Personas, creatives and reports prepared for you."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="My Personas"
          value={String(dashQ.data?.persona_count ?? 0)}
          icon={Users}
          loading={dashQ.isLoading}
        />
        <StatCard
          label="My Creatives"
          value={String(dashQ.data?.creative_count ?? 0)}
          icon={Sparkles}
          loading={dashQ.isLoading}
        />
        <StatCard
          label="Reports this quarter"
          value={String(dashQ.data?.report_count ?? 0)}
          icon={FileBarChart}
          loading={dashQ.isLoading}
        />
      </div>

      <Card className="mt-6 p-5">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Recent reports</h3>
          <span className="text-xs text-muted-foreground">
            {(reportsQ.data ?? []).length}
          </span>
        </div>
        {reportsQ.isLoading ? (
          <div className="py-6 text-center text-sm text-muted-foreground">
            Loading…
          </div>
        ) : (reportsQ.data ?? []).length === 0 ? (
          <div className="py-6 text-center text-sm text-muted-foreground">
            No reports yet.
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {(reportsQ.data ?? []).slice(0, 8).map((r) => (
              <li
                key={r.id}
                className="flex items-center justify-between py-2 text-sm"
              >
                <div>
                  <div className="font-medium">{r.title}</div>
                  <div className="text-xs text-muted-foreground">
                    {r.report_type} · {r.status}
                  </div>
                </div>
                <span className="text-xs text-muted-foreground">
                  {new Date(r.created_at).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
