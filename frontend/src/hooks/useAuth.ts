import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { api, extractErrorMessage } from "../lib/api";
import { useAuthStore, type AuthUser } from "../lib/auth-store";

interface TokenResponse {
  access_token: string;
  refresh_token?: string | null;
  token_type: string;
}

export function useLogin() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { setTokens, setUser } = useAuthStore();

  return useMutation({
    mutationFn: async (payload: { email: string; password: string }) => {
      const tokens = (await api.post<TokenResponse>("/auth/login", payload))
        .data;
      setTokens(tokens.access_token, tokens.refresh_token ?? null);
      const me = (await api.get<AuthUser>("/auth/me")).data;
      setUser(me);
      return me;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["auth", "me"] });
      toast.success("Welcome back");
      navigate("/", { replace: true });
    },
    onError: (err) => {
      toast.error(extractErrorMessage(err, "Sign in failed"));
    },
  });
}

export function useRegister() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { setTokens, setUser } = useAuthStore();

  return useMutation({
    mutationFn: async (payload: {
      agency_name: string;
      full_name: string;
      email: string;
      password: string;
    }) => {
      const tokens = (await api.post<TokenResponse>("/auth/register", payload))
        .data;
      setTokens(tokens.access_token, tokens.refresh_token ?? null);
      const me = (await api.get<AuthUser>("/auth/me")).data;
      setUser(me);
      return me;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["auth", "me"] });
      toast.success("Account created");
      navigate("/", { replace: true });
    },
    onError: (err) => {
      toast.error(extractErrorMessage(err, "Sign up failed"));
    },
  });
}

export function useLogout() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { clear } = useAuthStore();

  return useMutation({
    mutationFn: async () => {
      try {
        await api.post("/auth/logout");
      } catch {
        // ignore — token may already be invalid
      }
    },
    onSettled: () => {
      clear();
      qc.clear();
      navigate("/login", { replace: true });
    },
  });
}
