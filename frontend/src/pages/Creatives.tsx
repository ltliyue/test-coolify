import { useQuery } from "@tanstack/react-query";
import { Plus, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "../components/ui/PageHeader";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { api } from "../lib/api";

interface Creative {
  id: string;
  name?: string;
  headline?: string;
  format?: string;
  status?: string;
  thumbnail_url?: string;
  created_at?: string;
}

export default function Creatives() {
  const { data = [], isLoading } = useQuery<Creative[]>({
    queryKey: ["creatives"],
    queryFn: async () => {
      try {
        const res = await api.get<Creative[] | { items: Creative[] }>(
          "/creatives",
        );
        return Array.isArray(res.data) ? res.data : (res.data?.items ?? []);
      } catch {
        return [];
      }
    },
  });

  return (
    <>
      <PageHeader
        title="Creatives"
        description="AI-assisted ad creatives — copy, visuals, and variations."
        actions={
          <Button onClick={() => toast("Creative studio coming soon")}>
            <Plus className="h-4 w-4" />
            New creative
          </Button>
        }
      />

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-56" />
          ))}
        </div>
      ) : data.length === 0 ? (
        <EmptyState
          icon={<Sparkles className="h-5 w-5" />}
          title="No creatives yet"
          description="Generate ad copy, images, and variations tuned to your personas and brand voice."
          action={
            <Button onClick={() => toast("Creative studio coming soon")}>
              <Plus className="h-4 w-4" />
              Generate first creative
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((c) => (
            <Card
              key={c.id}
              className="overflow-hidden transition-shadow hover:shadow-md"
            >
              <div className="aspect-video bg-gradient-to-br from-accent/30 to-accent/5">
                {c.thumbnail_url && (
                  <img
                    src={c.thumbnail_url}
                    alt={c.name ?? "creative"}
                    className="h-full w-full object-cover"
                  />
                )}
              </div>
              <div className="p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="truncate font-medium">
                      {c.name ?? c.headline ?? "Untitled"}
                    </div>
                    <div className="mt-0.5 text-xs text-muted-foreground">
                      {c.format ?? "Image"}
                    </div>
                  </div>
                  <Badge variant="accent">{c.status ?? "draft"}</Badge>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </>
  );
}
