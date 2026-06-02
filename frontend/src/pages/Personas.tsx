import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, Search, Users } from "lucide-react";

import { PageHeader } from "../components/ui/PageHeader";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { DataTable, type Column } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { Badge } from "../components/ui/Badge";
import { api } from "../lib/api";
import { toast } from "sonner";

interface Persona {
  id: string;
  name: string;
  description?: string | null;
  status?: string;
  created_at?: string;
  [k: string]: unknown;
}

export default function Personas() {
  const [q, setQ] = useState("");

  const { data = [], isLoading } = useQuery<Persona[]>({
    queryKey: ["personas"],
    queryFn: async () => {
      try {
        const res = await api.get<Persona[] | { items: Persona[] }>(
          "/personas",
        );
        return Array.isArray(res.data) ? res.data : (res.data?.items ?? []);
      } catch {
        return [];
      }
    },
  });

  const filtered = q
    ? data.filter((p) => p.name?.toLowerCase().includes(q.toLowerCase()))
    : data;

  const columns: Column<Persona>[] = [
    {
      key: "name",
      header: "Name",
      render: (p) => (
        <div>
          <div className="font-medium">{p.name}</div>
          {p.description && (
            <div className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">
              {p.description}
            </div>
          )}
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (p) => <Badge variant="accent">{p.status ?? "draft"}</Badge>,
    },
    {
      key: "created_at",
      header: "Created",
      render: (p) =>
        p.created_at ? new Date(p.created_at).toLocaleDateString() : "—",
      className: "text-muted-foreground",
    },
  ];

  return (
    <>
      <PageHeader
        title="Personas"
        description="AI-generated audience archetypes derived from your campaigns and CRM data."
        actions={
          <Button
            onClick={() =>
              toast("Wizard coming soon", {
                description: "Persona builder flow is in development",
              })
            }
          >
            <Plus className="h-4 w-4" />
            New persona
          </Button>
        }
      />

      <div className="mb-4 flex items-center gap-2">
        <div className="relative max-w-sm flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search personas..."
            className="pl-9"
          />
        </div>
      </div>

      <DataTable
        columns={columns}
        data={filtered}
        rowKey={(p) => p.id}
        loading={isLoading}
        empty={
          <EmptyState
            icon={<Users className="h-5 w-5" />}
            title="No personas yet"
            description="Personas help you target the right audience by clustering behavioral and demographic signals."
            action={
              <Button onClick={() => toast("Wizard coming soon")}>
                <Plus className="h-4 w-4" />
                Create your first persona
              </Button>
            }
          />
        }
      />
    </>
  );
}
