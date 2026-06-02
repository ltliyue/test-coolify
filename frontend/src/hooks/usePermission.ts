import { useAuthStore } from "../lib/auth-store";

/**
 * Returns true when the current user has the given permission code.
 *
 * The backend is the source of truth — this is a client-side
 * visibility helper that mirrors what /auth/me already resolved.
 */
export function useHasPermission(code: string): boolean {
  const perms = useAuthStore((s) => s.user?.permissions ?? []);
  return perms.includes(code);
}

export function useHasAnyPermission(codes: string[]): boolean {
  const perms = useAuthStore((s) => s.user?.permissions ?? []);
  return codes.some((c) => perms.includes(c));
}
