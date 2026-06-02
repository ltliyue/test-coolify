import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "../../components/ui/PageHeader";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { api } from "../../lib/api";

interface PortalReport {
  id: string;
  title: string;
  report_type: string;
  status: string;
  created_at: string;
}

// Client-tier read-only report list. Backend portal endpoint already
// scopes by agency_id (and downstream by client_id where applicable).
export default function MyReports() {
  const { data, isLoading } = useQuery({
    queryKey: ["client", "reports", "list"],
    queryFn: async () => {
      const res = await api.get<PortalReport[]>("/portal/reports");
      return res.data;
    },
  });

  return (
    <div>
      <PageHeader
        title="My Reports"
        description="Attribution reports your agency has shared with you."
      />

      <Card className="p-5">
        {isLoading ? (
          <div className="py-6 text-center text-sm text-muted-foreground">
            Loading…
          </div>
        ) : (data ?? []).length === 0 ? (
          <div className="py-6 text-center text-sm text-muted-foreground">
            No reports yet.
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {data!.map((r) => (
              <li
                key={r.id}
                className="flex items-center justify-between py-3 text-sm"
              >
                <div>
                  <div className="font-medium">{r.title}</div>
                  <div className="text-xs text-muted-foreground">
                    {r.report_type} ·{" "}
                    {new Date(r.created_at).toLocaleDateString()}
                  </div>
                </div>
                <Badge
                  variant={r.status === "completed" ? "success" : "default"}
                >
                  {r.status}
                </Badge>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
