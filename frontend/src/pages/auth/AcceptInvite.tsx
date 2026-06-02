import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Button } from "../../components/ui/Button";
import { Input, Label, FieldError } from "../../components/ui/Input";
import { api, extractErrorMessage } from "../../lib/api";
import { useAuthStore, type AuthUser } from "../../lib/auth-store";

interface FormValues {
  full_name: string;
  password: string;
  confirm: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token?: string | null;
}

export default function AcceptInvite() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { accessToken, setTokens, setUser } = useAuthStore();
  const [invalid, setInvalid] = useState(false);

  useEffect(() => {
    if (!token) setInvalid(true);
  }, [token]);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    defaultValues: { full_name: "", password: "", confirm: "" },
  });

  const accept = useMutation({
    mutationFn: async (vars: { full_name: string; password: string }) => {
      const res = await api.post<TokenResponse>("/auth/accept-invite", {
        token,
        full_name: vars.full_name,
        password: vars.password,
      });
      setTokens(res.data.access_token, res.data.refresh_token ?? null);
      const me = (await api.get<AuthUser>("/auth/me")).data;
      setUser(me);
      return me;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["auth", "me"] });
      toast.success("Welcome to ReceptivIQ");
      navigate("/", { replace: true });
    },
    onError: (err) => {
      const msg = extractErrorMessage(err, "Could not accept invitation");
      if (msg.toLowerCase().includes("invalid")) setInvalid(true);
      else toast.error(msg);
    },
  });

  if (accessToken) return <Navigate to="/" replace />;

  if (invalid) {
    return (
      <Shell title="Invalid or expired invitation">
        <p className="text-sm text-muted-foreground">
          This invitation link is no longer valid. Ask your administrator for a
          new one.
        </p>
        <div className="pt-4">
          <Link
            to="/login"
            className="text-sm font-medium text-accent hover:underline"
          >
            Back to sign in
          </Link>
        </div>
      </Shell>
    );
  }

  return (
    <Shell
      title="Accept invitation"
      subtitle="Set up your account to join the workspace."
    >
      <form
        onSubmit={handleSubmit((v) =>
          accept.mutate({ full_name: v.full_name, password: v.password }),
        )}
        className="space-y-4"
        noValidate
      >
        <div>
          <Label htmlFor="full_name">Full name</Label>
          <Input
            id="full_name"
            invalid={!!errors.full_name}
            {...register("full_name", { required: "Name is required" })}
          />
          <FieldError message={errors.full_name?.message} />
        </div>
        <div>
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            invalid={!!errors.password}
            {...register("password", {
              required: "Password is required",
              minLength: { value: 8, message: "Must be at least 8 characters" },
            })}
          />
          <FieldError message={errors.password?.message} />
        </div>
        <div>
          <Label htmlFor="confirm">Confirm password</Label>
          <Input
            id="confirm"
            type="password"
            invalid={!!errors.confirm}
            {...register("confirm", {
              validate: (v) =>
                v === watch("password") || "Passwords do not match",
            })}
          />
          <FieldError message={errors.confirm?.message} />
        </div>
        <Button
          type="submit"
          variant="accent"
          className="w-full"
          loading={accept.isPending}
        >
          Create account
        </Button>
      </form>
    </Shell>
  );
}

function Shell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-8 shadow-lg">
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle && (
          <p className="mt-1.5 text-sm text-muted-foreground">{subtitle}</p>
        )}
        <div className="mt-6">{children}</div>
      </div>
    </div>
  );
}
