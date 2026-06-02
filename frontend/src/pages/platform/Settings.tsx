import { useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { useAuthStore } from "../../lib/auth-store";

// Platform-tier Settings: intentionally minimal. The Brand / Agency /
// Compliance tabs from the Agency Settings shell are Agency-scoped and
// have no meaningful target when the calling user has agency_id=NULL.
export default function PlatformSettings() {
  const user = useAuthStore((s) => s.user);
  const clear = useAuthStore((s) => s.clear);
  const navigate = useNavigate();

  const signOut = () => {
    clear();
    navigate("/login", { replace: true });
  };

  return (
    <div>
      <PageHeader title="Settings" description="Your platform-tier account." />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <h3 className="mb-3 text-sm font-semibold">Profile</h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Name</dt>
              <dd>{user?.full_name ?? "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Email</dt>
              <dd>{user?.email ?? "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Role</dt>
              <dd>{user?.role_label || user?.role || "—"}</dd>
            </div>
          </dl>
        </Card>

        <Card className="p-5">
          <h3 className="mb-3 text-sm font-semibold">Session</h3>
          <p className="mb-4 text-sm text-muted-foreground">
            Sign out of the platform console. Agency-scoped configuration
            (Brand, Compliance, Team) is managed by each Agency admin.
          </p>
          <Button variant="outline" onClick={signOut}>
            <LogOut className="mr-2 h-4 w-4" />
            Sign out
          </Button>
        </Card>
      </div>
    </div>
  );
}
