import { ReactNode } from "react";
import { useAuthStore } from "../lib/auth-store";

interface PermissionCase {
  code: string;
  element: ReactNode;
}

interface PermissionSwitchProps {
  cases: PermissionCase[];
  default?: ReactNode;
}

/**
 * Renders the first case whose permission code the user holds.
 * Falls back to `default` when no case matches.
 */
export function PermissionSwitch({
  cases,
  default: fallback,
}: PermissionSwitchProps) {
  const perms = useAuthStore((s) => s.user?.permissions ?? []);
  for (const c of cases) {
    if (perms.includes(c.code)) return <>{c.element}</>;
  }
  return <>{fallback ?? null}</>;
}
