import { useQuery } from "@tanstack/react-query";
import { FileText, Plus } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "../components/ui/PageHeader";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { DataTable, type Column } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { api } from "../lib/api";

interface Report {
  id: string;
  name: string;
  type?: string;
  status?: string;
  created_at?: string;
  [k: string]: unknown;
}

export default function Reports() {
  const { data = [], isLoading } = useQuery<Report[]>({
    queryKey: ["reports"],
    queryFn: async () => {
      try {
        const res = await api.get<Report[] | { items: Report[] }>("/reports");
        return Array.isArray(res.data) ? res.data : (res.data?.items ?? []);
      } catch {
        return [];
      }
    },
  });

  const columns: Column<Report>[] = [
    {
      key: "name",
      header: "Report",
      render: (r) => <span className="font-medium">{r.name}</span>,
    },
    {
      key: "type",
      header: "Type",
      render: (r) => <Badge variant="outline">{r.type ?? "Custom"}</Badge>,
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
        title="Reports"
        description="Scheduled and ad-hoc reports across your portfolio."
        actions={
          <Button onClick={() => toast("Report builder coming soon")}>
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
            icon={<FileText className="h-5 w-5" />}
            title="No reports yet"
            description="Build a recurring or one-off report to share insights with your team."
            action={
              <Button onClick={() => toast("Report builder coming soon")}>
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
