import { Plug } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "../components/ui/PageHeader";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";

interface Platform {
  id: string;
  name: string;
  category: string;
  color: string;
}

const PLATFORMS: Platform[] = [
  { id: "meta", name: "Meta", category: "Social Ads", color: "bg-blue-500" },
  { id: "ga4", name: "GA4", category: "Analytics", color: "bg-orange-500" },
  { id: "hubspot", name: "HubSpot", category: "CRM", color: "bg-orange-600" },
  { id: "dv360", name: "DV360", category: "Programmatic", color: "bg-sky-500" },
  {
    id: "tiktok",
    name: "TikTok",
    category: "Social Ads",
    color: "bg-zinc-900",
  },
  {
    id: "ttd",
    name: "The Trade Desk",
    category: "Programmatic",
    color: "bg-red-500",
  },
  {
    id: "stackadapt",
    name: "StackAdapt",
    category: "Programmatic",
    color: "bg-violet-500",
  },
  {
    id: "experian",
    name: "Experian",
    category: "Data",
    color: "bg-indigo-500",
  },
  {
    id: "liveramp",
    name: "LiveRamp",
    category: "Identity",
    color: "bg-cyan-500",
  },
  {
    id: "nielsen",
    name: "Nielsen",
    category: "Measurement",
    color: "bg-amber-600",
  },
  {
    id: "placeriq",
    name: "Placer IQ",
    category: "Location",
    color: "bg-emerald-500",
  },
  {
    id: "quorum",
    name: "Quorum",
    category: "Public Affairs",
    color: "bg-rose-500",
  },
  {
    id: "tresorit",
    name: "Tresorit",
    category: "Secure Storage",
    color: "bg-slate-600",
  },
];

export default function Integrations() {
  const handleConnect = (p: Platform) => {
    toast(`Redirecting to ${p.name} OAuth...`);
  };

  return (
    <>
      <PageHeader
        title="Integrations"
        description="Connect external platforms to power data ingestion, activation, and measurement."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {PLATFORMS.map((p) => (
          <Card
            key={p.id}
            className="flex flex-col gap-4 p-5 transition-shadow hover:shadow-md"
          >
            <div className="flex items-center gap-3">
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-lg text-sm font-semibold text-white ${p.color}`}
              >
                {p.name.charAt(0)}
              </div>
              <div className="min-w-0">
                <div className="truncate font-medium">{p.name}</div>
                <div className="text-xs text-muted-foreground">
                  {p.category}
                </div>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => handleConnect(p)}
            >
              <Plug className="h-3.5 w-3.5" />
              Connect
            </Button>
          </Card>
        ))}
      </div>
    </>
  );
}
