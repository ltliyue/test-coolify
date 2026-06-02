import { Link, Navigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowRight } from "lucide-react";

import { Button } from "../../components/ui/Button";
import { FieldError, Input, Label } from "../../components/ui/Input";
import { useRegister } from "../../hooks/useAuth";
import { useAuthStore } from "../../lib/auth-store";
import { AuthLayout } from "./Login";

const schema = z
  .object({
    agency_name: z.string().min(2, "Agency name must be at least 2 characters"),
    full_name: z.string().min(2, "Your name must be at least 2 characters"),
    email: z.string().email("Enter a valid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string(),
  })
  .refine((d) => d.password === d.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type FormValues = z.infer<typeof schema>;

export default function Register() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const reg = useRegister();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      agency_name: "",
      full_name: "",
      email: "",
      password: "",
      confirm_password: "",
    },
  });

  if (accessToken) return <Navigate to="/" replace />;

  return (
    <AuthLayout
      title="Create your workspace"
      subtitle="Spin up a new ReceptivIQ agency in a minute."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-accent hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form
        onSubmit={handleSubmit((v) =>
          reg.mutate({
            agency_name: v.agency_name,
            full_name: v.full_name,
            email: v.email,
            password: v.password,
          }),
        )}
        className="space-y-4"
        noValidate
      >
        <div>
          <Label htmlFor="agency_name">Agency name</Label>
          <Input
            id="agency_name"
            placeholder="Acme Marketing"
            invalid={!!errors.agency_name}
            {...register("agency_name")}
          />
          <FieldError message={errors.agency_name?.message} />
        </div>

        <div>
          <Label htmlFor="full_name">Your name</Label>
          <Input
            id="full_name"
            autoComplete="name"
            invalid={!!errors.full_name}
            {...register("full_name")}
          />
          <FieldError message={errors.full_name?.message} />
        </div>

        <div>
          <Label htmlFor="email">Work email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            invalid={!!errors.email}
            {...register("email")}
          />
          <FieldError message={errors.email?.message} />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              invalid={!!errors.password}
              {...register("password")}
            />
            <FieldError message={errors.password?.message} />
          </div>
          <div>
            <Label htmlFor="confirm_password">Confirm</Label>
            <Input
              id="confirm_password"
              type="password"
              autoComplete="new-password"
              invalid={!!errors.confirm_password}
              {...register("confirm_password")}
            />
            <FieldError message={errors.confirm_password?.message} />
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          By creating an account you agree to the Terms of Service and
          acknowledge our Privacy Policy. Your data is encrypted at rest and in
          transit.
        </p>

        <Button type="submit" className="w-full" loading={reg.isPending}>
          Create account
          <ArrowRight className="h-4 w-4" />
        </Button>
      </form>
    </AuthLayout>
  );
}
