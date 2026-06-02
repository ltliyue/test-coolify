import type { LucideIcon } from "lucide-react";
import { TrendingDown, TrendingUp } from "lucide-react";
import { Card } from "../ui/Card";
import { cn } from "../../lib/cn";

interface StatCardProps {
  label: string;
  value: string;
  delta?: number;
  icon: LucideIcon;
  loading?: boolean;
}

export function StatCard({
  label,
  value,
  delta,
  icon: Icon,
  loading,
}: StatCardProps) {
  const positive = (delta ?? 0) >= 0;
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">{label}</div>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 text-accent">
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <div className="mt-3 text-3xl font-semibold tracking-tight">
        {loading ? "—" : value}
      </div>
      {typeof delta === "number" && (
        <div
          className={cn(
            "mt-2 inline-flex items-center gap-1 text-xs font-medium",
            positive
              ? "text-emerald-600 dark:text-emerald-400"
              : "text-destructive",
          )}
        >
          {positive ? (
            <TrendingUp className="h-3 w-3" />
          ) : (
            <TrendingDown className="h-3 w-3" />
          )}
          {positive ? "+" : ""}
          {delta.toFixed(1)}% vs last month
        </div>
      )}
    </Card>
  );
}
