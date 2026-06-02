import { Link } from "react-router-dom";
import { useAuthStore } from "../lib/auth-store";

export default function Forbidden() {
  const clear = useAuthStore((s) => s.clear);
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <div className="text-6xl">:(</div>
      <h1 className="text-2xl font-semibold">403 — Forbidden</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        You do not have permission to view this page. If you believe this is a
        mistake, contact your administrator.
      </p>
      <div className="flex gap-3 text-sm">
        <Link className="text-accent underline" to="/">
          Go to dashboard
        </Link>
        <button
          type="button"
          className="text-accent underline"
          onClick={() => {
            clear();
            window.location.href = "/login";
          }}
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
