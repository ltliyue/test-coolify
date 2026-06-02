import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useHasPermission } from "../hooks/usePermission";

interface PermissionGateProps {
  code: string;
  children: ReactNode;
  /** Optional fallback element shown when permission is missing. */
  fallback?: ReactNode;
  /** When set, missing permission triggers a redirect instead of fallback. */
  redirect?: string;
}

/**
 * Client-side soft guard. Renders children only when the user holds
 * the given permission code; otherwise renders the fallback or
 * redirects. Backend remains the source of truth for authorization.
 */
export function PermissionGate({
  code,
  children,
  fallback,
  redirect,
}: PermissionGateProps) {
  const ok = useHasPermission(code);
  if (ok) return <>{children}</>;
  if (redirect) return <Navigate to={redirect} replace />;
  return <>{fallback ?? null}</>;
}
