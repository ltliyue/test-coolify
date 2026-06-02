import { DollarSign, Megaphone, Sparkles, Users } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "../components/ui/PageHeader";
import { StatCard } from "../components/widgets/StatCard";
import {
  ActivityFeed,
  type ActivityItem,
} from "../components/widgets/ActivityFeed";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { api } from "../lib/api";
import { useAuthStore } from "../lib/auth-store";

interface DashboardSummary {
  personas?: number;
  creatives?: number;
  campaigns?: number;
  monthly_spend?: number;
}

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);

  // Try the (optional) portal dashboard endpoint; fall back gracefully on 404
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: async () => {
      try {
        const res = await api.get<DashboardSummary>("/portal/dashboard");
        return res.data;
      } catch {
        return null;
      }
    },
  });

  const stats = [
    {
      label: "Personas",
      value: data?.personas ?? 0,
      delta: 12.4,
      icon: Users,
    },
    {
      label: "Creatives",
      value: data?.creatives ?? 0,
      delta: 8.1,
      icon: Sparkles,
    },
    {
      label: "Active campaigns",
      value: data?.campaigns ?? 0,
      delta: -2.3,
      icon: Megaphone,
    },
    {
      label: "Spend this month",
      value:
        typeof data?.monthly_spend === "number"
          ? `$${data.monthly_spend.toLocaleString()}`
          : "$0",
      delta: 21.7,
      icon: DollarSign,
    },
  ];

  const activity: ActivityItem[] = [
    {
      id: "1",
      actor: user?.full_name ?? "You",
      action: "signed in to",
      target: "ReceptivIQ",
      timestamp: "Just now",
    },
    {
      id: "2",
      actor: "System",
      action: "created your workspace",
      timestamp: "Moments ago",
    },
  ];

  return (
    <>
      <PageHeader
        title={`Welcome${user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}`}
        description="Here's a quick snapshot of your agency's performance."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <StatCard
            key={s.label}
            label={s.label}
            value={
              typeof s.value === "number" ? s.value.toLocaleString() : s.value
            }
            delta={s.delta}
            icon={s.icon}
            loading={isLoading}
          />
        ))}
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Performance overview</CardTitle>
              <Badge variant="outline">Last 30 days</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <PlaceholderChart />
          </CardContent>
        </Card>

        <ActivityFeed items={activity} />
      </div>
    </>
  );
}

function PlaceholderChart() {
  // Deterministic decorative SVG area chart (no external charting dep for MVP).
  const points = [12, 18, 14, 22, 19, 26, 24, 32, 28, 36, 33, 41, 38, 45];
  const max = Math.max(...points);
  const w = 600;
  const h = 200;
  const step = w / (points.length - 1);
  const coords = points.map((p, i) => [
    i * step,
    h - (p / max) * (h - 20) - 10,
  ]);
  const line = coords
    .map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");
  const area = `${line} L${w},${h} L0,${h} Z`;
  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      className="h-56 w-full"
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id="riq-grad" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity="0.35" />
          <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill="url(#riq-grad)" />
      <path
        d={line}
        fill="none"
        stroke="hsl(var(--accent))"
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
