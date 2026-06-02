import { Link, Navigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { ArrowRight } from "lucide-react";

import { Button } from "../../components/ui/Button";
import { FieldError, Input, Label } from "../../components/ui/Input";
import { useLogin } from "../../hooks/useAuth";
import { useAuthStore } from "../../lib/auth-store";

const schema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type FormValues = z.infer<typeof schema>;

export default function Login() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const login = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  if (accessToken) return <Navigate to="/" replace />;

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to continue to ReceptivIQ"
      footer={
        <>
          New here?{" "}
          <Link
            to="/register"
            className="font-medium text-accent hover:underline"
          >
            Create an account
          </Link>
        </>
      }
    >
      <form
        onSubmit={handleSubmit((v) => login.mutate(v))}
        className="space-y-4"
        noValidate
      >
        <div>
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            invalid={!!errors.email}
            {...register("email")}
          />
          <FieldError message={errors.email?.message} />
        </div>

        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <Label htmlFor="password" className="mb-0">
              Password
            </Label>
            <Link
              to="/forgot-password"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Forgot password?
            </Link>
          </div>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            invalid={!!errors.password}
            {...register("password")}
          />
          <FieldError message={errors.password?.message} />
        </div>

        <Button type="submit" className="w-full" loading={login.isPending}>
          Sign in
          <ArrowRight className="h-4 w-4" />
        </Button>

        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="bg-card px-2 text-muted-foreground">
              or continue with
            </span>
          </div>
        </div>

        <Button
          type="button"
          variant="outline"
          className="w-full"
          onClick={() =>
            toast("Coming soon", {
              description: "Google SSO is on the roadmap",
            })
          }
        >
          <GoogleMark />
          Sign in with Google
        </Button>
      </form>
    </AuthLayout>
  );
}

export function AuthLayout({
  title,
  subtitle,
  footer,
  children,
}: {
  title: string;
  subtitle?: string;
  footer?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="grid min-h-full grid-cols-1 lg:grid-cols-2">
      <div className="relative hidden overflow-hidden bg-gradient-to-br from-accent/15 via-background to-background lg:block">
        <div className="absolute left-10 top-10 flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-accent-foreground">
            <span className="text-sm font-bold">R</span>
          </div>
          <div className="text-sm font-semibold tracking-tight">ReceptivIQ</div>
        </div>
        <div className="flex h-full items-center px-12">
          <div className="max-w-md">
            <h2 className="text-3xl font-semibold tracking-tight">
              The agency-grade marketing intelligence platform.
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              Personas, creatives, attribution, and audience activation — built
              for compliance-first US agencies. GDPR, CCPA and HIPAA-aware by
              design.
            </p>
            <div className="mt-10 grid grid-cols-2 gap-4 text-xs text-muted-foreground">
              <div>
                <div className="text-lg font-semibold text-foreground">12+</div>
                Connected platforms
              </div>
              <div>
                <div className="text-lg font-semibold text-foreground">
                  SOC 2
                </div>
                Compliance-ready
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col">
        <div className="flex items-center justify-between px-6 py-5 lg:hidden">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent text-accent-foreground">
              <span className="text-xs font-bold">R</span>
            </div>
            <span className="text-sm font-semibold">ReceptivIQ</span>
          </div>
        </div>
        <div className="flex flex-1 items-center justify-center px-6 py-12">
          <div className="w-full max-w-sm">
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            {subtitle && (
              <p className="mt-1.5 text-sm text-muted-foreground">{subtitle}</p>
            )}
            <div className="mt-8">{children}</div>
            {footer && (
              <div className="mt-6 text-center text-sm text-muted-foreground">
                {footer}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function GoogleMark() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#EA4335"
        d="M12 10.2v3.9h5.5c-.2 1.3-1.6 3.8-5.5 3.8-3.3 0-6-2.7-6-6s2.7-6 6-6c1.9 0 3.1.8 3.8 1.5l2.6-2.5C16.8 3.5 14.6 2.5 12 2.5 6.8 2.5 2.5 6.8 2.5 12s4.3 9.5 9.5 9.5c5.5 0 9.1-3.8 9.1-9.2 0-.6-.1-1.1-.2-1.6L12 10.2z"
      />
    </svg>
  );
}
