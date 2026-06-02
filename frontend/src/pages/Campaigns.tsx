import { useQuery } from "@tanstack/react-query";
import { Megaphone, Plus } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "../components/ui/PageHeader";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { DataTable, type Column } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { api } from "../lib/api";

interface Campaign {
  id: string;
  name: string;
  platform?: string;
  status?: string;
  budget?: number;
  start_date?: string;
  end_date?: string;
  [k: string]: unknown;
}

export default function Campaigns() {
  const { data = [], isLoading } = useQuery<Campaign[]>({
    queryKey: ["campaigns"],
    queryFn: async () => {
      try {
        const res = await api.get<Campaign[] | { items: Campaign[] }>(
          "/campaigns",
        );
        return Array.isArray(res.data) ? res.data : (res.data?.items ?? []);
      } catch {
        return [];
      }
    },
  });

  const columns: Column<Campaign>[] = [
    {
      key: "name",
      header: "Campaign",
      render: (c) => <span className="font-medium">{c.name}</span>,
    },
    {
      key: "platform",
      header: "Platform",
      render: (c) => (
        <Badge variant="outline">{c.platform ?? "Unspecified"}</Badge>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (c) => {
        const status = c.status ?? "draft";
        const variant: "success" | "warn" | "default" =
          status === "active"
            ? "success"
            : status === "paused"
              ? "warn"
              : "default";
        return <Badge variant={variant}>{status}</Badge>;
      },
    },
    {
      key: "budget",
      header: "Budget",
      render: (c) =>
        typeof c.budget === "number" ? `$${c.budget.toLocaleString()}` : "—",
    },
    {
      key: "start_date",
      header: "Starts",
      render: (c) =>
        c.start_date ? new Date(c.start_date).toLocaleDateString() : "—",
      className: "text-muted-foreground",
    },
  ];

  return (
    <>
      <PageHeader
        title="Campaigns"
        description="All paid media campaigns across connected platforms."
        actions={
          <Button onClick={() => toast("Campaign builder coming soon")}>
            <Plus className="h-4 w-4" />
            New campaign
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data}
        rowKey={(c) => c.id}
        loading={isLoading}
        empty={
          <EmptyState
            icon={<Megaphone className="h-5 w-5" />}
            title="No campaigns yet"
            description="Connect a platform and start a campaign to see performance here."
            action={
              <Button onClick={() => toast("Campaign builder coming soon")}>
                <Plus className="h-4 w-4" />
                Create campaign
              </Button>
            }
          />
        }
      />
    </>
  );
}
