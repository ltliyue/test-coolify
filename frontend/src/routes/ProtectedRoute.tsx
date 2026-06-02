import { useEffect, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";
import { useAuthStore, type AuthUser } from "../lib/auth-store";

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { accessToken, user, setUser, clear } = useAuthStore();
  const location = useLocation();

  // Always re-fetch /auth/me on protected-route mount so changes to
  // role_rank, permissions, agency suspension, etc. propagate without
  // forcing a manual logout. The stored user is only used as an
  // optimistic placeholder while the request is in flight.
  const { data, error, isLoading } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => (await api.get<AuthUser>("/auth/me")).data,
    enabled: Boolean(accessToken),
    staleTime: 30_000,
  });

  useEffect(() => {
    if (data) setUser(data);
  }, [data, setUser]);

  useEffect(() => {
    if (error) clear();
  }, [error, clear]);

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!user && isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
