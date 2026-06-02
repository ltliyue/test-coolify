import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "../components/ui/PageHeader";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { api, extractErrorMessage } from "../lib/api";

interface NotificationItem {
  id: string;
  title?: string;
  message?: string;
  read?: boolean;
  is_read?: boolean;
  created_at?: string;
  severity?: string;
  [k: string]: unknown;
}

export default function Notifications() {
  const qc = useQueryClient();

  const { data = [], isLoading } = useQuery<NotificationItem[]>({
    queryKey: ["notifications"],
    queryFn: async () => {
      try {
        const res = await api.get<
          NotificationItem[] | { items: NotificationItem[] }
        >("/notifications");
        return Array.isArray(res.data) ? res.data : (res.data?.items ?? []);
      } catch {
        return [];
      }
    },
  });

  const markAll = useMutation({
    mutationFn: async () => {
      await api.post("/notifications/mark-all-read");
    },
    onSuccess: () => {
      toast.success("All notifications marked as read");
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
    onError: (err) => {
      toast.error("Failed to mark as read", {
        description: extractErrorMessage(err),
      });
    },
  });

  const isUnread = (n: NotificationItem) => !(n.read ?? n.is_read ?? false);

  const unreadCount = data.filter(isUnread).length;

  return (
    <>
      <PageHeader
        title="Notifications"
        description="Recent activity, alerts, and system updates."
        actions={
          <div className="flex items-center gap-2">
            {unreadCount > 0 && (
              <Badge variant="accent">{unreadCount} unread</Badge>
            )}
            <Button
              variant="outline"
              onClick={() => markAll.mutate()}
              loading={markAll.isPending}
              disabled={unreadCount === 0}
            >
              <CheckCheck className="h-4 w-4" />
              Mark all read
            </Button>
          </div>
        }
      />

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : data.length === 0 ? (
        <EmptyState
          icon={<Bell className="h-5 w-5" />}
          title="No notifications"
          description="You're all caught up — new alerts will appear here."
        />
      ) : (
        <div className="space-y-2">
          {data.map((n) => {
            const unread = isUnread(n);
            return (
              <Card
                key={n.id}
                className={`flex items-start gap-3 p-4 ${
                  unread ? "border-accent/50 bg-accent/5" : ""
                }`}
              >
                <div
                  className={`mt-1 h-2 w-2 shrink-0 rounded-full ${
                    unread ? "bg-accent" : "bg-muted-foreground/40"
                  }`}
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-2">
                    <div className="font-medium">
                      {n.title ?? "Notification"}
                    </div>
                    {n.severity && (
                      <Badge variant="outline">{n.severity}</Badge>
                    )}
                  </div>
                  {n.message && (
                    <p className="mt-0.5 text-sm text-muted-foreground">
                      {n.message}
                    </p>
                  )}
                  {n.created_at && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      {new Date(n.created_at).toLocaleString()}
                    </p>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </>
  );
}
