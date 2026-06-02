import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "../../components/ui/PageHeader";
import { Card } from "../../components/ui/Card";
import { api } from "../../lib/api";

interface PortalPersona {
  id: string;
  name: string;
  description?: string | null;
  recommended_tone?: string | null;
  created_at: string;
}

// Client-tier read-only persona list.
export default function MyPersonas() {
  const { data, isLoading } = useQuery({
    queryKey: ["client", "personas", "list"],
    queryFn: async () => {
      const res = await api.get<PortalPersona[]>("/portal/personas");
      return res.data;
    },
  });

  return (
    <div>
      <PageHeader
        title="My Personas"
        description="Audience personas your agency has prepared for your brand."
      />

      {isLoading ? (
        <Card className="p-5 text-center text-sm text-muted-foreground">
          Loading…
        </Card>
      ) : (data ?? []).length === 0 ? (
        <Card className="p-5 text-center text-sm text-muted-foreground">
          No personas yet.
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data!.map((p) => (
            <Card key={p.id} className="p-5">
              <div className="text-sm font-semibold">{p.name}</div>
              {p.recommended_tone && (
                <div className="mt-1 text-xs text-muted-foreground">
                  Tone: {p.recommended_tone}
                </div>
              )}
              {p.description && (
                <p className="mt-3 line-clamp-4 text-sm text-muted-foreground">
                  {p.description}
                </p>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
