import { useQuery } from "@tanstack/react-query";
import { BarChart3, Plus } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "../components/ui/PageHeader";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { DataTable, type Column } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { api } from "../lib/api";

interface AttributionReport {
  id: string;
  name: string;
  model?: string;
  status?: string;
  created_at?: string;
  [k: string]: unknown;
}

export default function Attribution() {
  const { data = [], isLoading } = useQuery<AttributionReport[]>({
    queryKey: ["attribution-reports"],
    queryFn: async () => {
      try {
        const res = await api.get<
          AttributionReport[] | { items: AttributionReport[] }
        >("/attribution/reports");
        return Array.isArray(res.data) ? res.data : (res.data?.items ?? []);
      } catch {
        return [];
      }
    },
  });

  const columns: Column<AttributionReport>[] = [
    {
      key: "name",
      header: "Report",
      render: (r) => <span className="font-medium">{r.name}</span>,
    },
    {
      key: "model",
      header: "Model",
      render: (r) => <Badge variant="outline">{r.model ?? "Last-touch"}</Badge>,
    },
    {
      key: "status",
      header: "Status",
      render: (r) => {
        const status = r.status ?? "draft";
        const variant: "success" | "warn" | "default" =
          status === "ready"
            ? "success"
            : status === "running"
              ? "warn"
              : "default";
        return <Badge variant={variant}>{status}</Badge>;
      },
    },
    {
      key: "created_at",
      header: "Created",
      render: (r) =>
        r.created_at ? new Date(r.created_at).toLocaleDateString() : "—",
      className: "text-muted-foreground",
    },
  ];

  return (
    <>
      <PageHeader
        title="Attribution"
        description="Multi-touch attribution reports across your connected channels."
        actions={
          <Button onClick={() => toast("Attribution builder coming soon")}>
            <Plus className="h-4 w-4" />
            New report
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data}
        rowKey={(r) => r.id}
        loading={isLoading}
        empty={
          <EmptyState
            icon={<BarChart3 className="h-5 w-5" />}
            title="No attribution reports yet"
            description="Build a report to understand which touchpoints drive conversions across your funnel."
            action={
              <Button onClick={() => toast("Attribution builder coming soon")}>
                <Plus className="h-4 w-4" />
                Create your first report
              </Button>
            }
          />
        }
      />
    </>
  );
}
