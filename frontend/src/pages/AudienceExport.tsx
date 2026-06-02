import { useQuery } from "@tanstack/react-query";
import { Download, Plus } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "../components/ui/PageHeader";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { DataTable, type Column } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { api } from "../lib/api";

interface AudienceExportItem {
  id: string;
  name: string;
  destination?: string;
  size?: number;
  status?: string;
  created_at?: string;
  [k: string]: unknown;
}

export default function AudienceExport() {
  const { data = [], isLoading } = useQuery<AudienceExportItem[]>({
    queryKey: ["audience-exports"],
    queryFn: async () => {
      try {
        const res = await api.get<
          AudienceExportItem[] | { items: AudienceExportItem[] }
        >("/audience-exports");
        return Array.isArray(res.data) ? res.data : (res.data?.items ?? []);
      } catch {
        return [];
      }
    },
  });

  const columns: Column<AudienceExportItem>[] = [
    {
      key: "name",
      header: "Export",
      render: (e) => <span className="font-medium">{e.name}</span>,
    },
    {
      key: "destination",
      header: "Destination",
      render: (e) => (
        <Badge variant="outline">{e.destination ?? "Unspecified"}</Badge>
      ),
    },
    {
      key: "size",
      header: "Audience size",
      render: (e) =>
        typeof e.size === "number" ? e.size.toLocaleString() : "—",
    },
    {
      key: "status",
      header: "Status",
      render: (e) => {
        const status = e.status ?? "pending";
        const variant: "success" | "warn" | "default" =
          status === "completed"
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
      render: (e) =>
        e.created_at ? new Date(e.created_at).toLocaleDateString() : "—",
      className: "text-muted-foreground",
    },
  ];

  return (
    <>
      <PageHeader
        title="Audience Export"
        description="Push activated audiences to your downstream platforms."
        actions={
          <Button onClick={() => toast("Export wizard coming soon")}>
            <Plus className="h-4 w-4" />
            New export
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data}
        rowKey={(e) => e.id}
        loading={isLoading}
        empty={
          <EmptyState
            icon={<Download className="h-5 w-5" />}
            title="No audience exports yet"
            description="Activate a persona by exporting it to ad platforms, DSPs, or CDPs."
            action={
              <Button onClick={() => toast("Export wizard coming soon")}>
                <Plus className="h-4 w-4" />
                Create your first export
              </Button>
            }
          />
        }
      />
    </>
  );
}
