import { Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

export interface ActivityItem {
  id: string;
  actor: string;
  action: string;
  target?: string;
  timestamp: string;
}

interface ActivityFeedProps {
  items: ActivityItem[];
}

export function ActivityFeed({ items }: ActivityFeedProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-accent" />
          Recent activity
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {items.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No activity yet
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {items.map((it) => (
              <li
                key={it.id}
                className="flex items-start gap-3 py-3 text-sm first:pt-0 last:pb-0"
              >
                <div className="mt-1 h-2 w-2 rounded-full bg-accent/60" />
                <div className="min-w-0 flex-1">
                  <div className="leading-snug">
                    <span className="font-medium">{it.actor}</span>{" "}
                    <span className="text-muted-foreground">{it.action}</span>{" "}
                    {it.target && (
                      <span className="font-medium">{it.target}</span>
                    )}
                  </div>
                  <div className="mt-0.5 text-xs text-muted-foreground">
                    {it.timestamp}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
