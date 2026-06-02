import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { Lock, ShieldCheck } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "../components/ui/PageHeader";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input, Label, FieldError } from "../components/ui/Input";
import { useAuthStore } from "../lib/auth-store";
import { api, extractErrorMessage } from "../lib/api";
import { cn } from "../lib/cn";

type Tab = "profile" | "brand" | "compliance";

// /settings/agency is retained as an alias of the merged Profile tab
// so old URLs and saved sidebar entries keep working.
const SUBROUTE_TO_TAB: Record<string, Tab> = {
  "/settings/profile": "profile",
  "/settings/agency": "profile",
  "/settings/brand": "brand",
  "/settings/compliance": "compliance",
};

interface BrandForm {
  brand_voice: string;
  recommended_tone: string;
  tagline: string;
  industry: string;
}

const TABS: { id: Tab; label: string }[] = [
  { id: "profile", label: "Profile" },
  { id: "brand", label: "Brand" },
  { id: "compliance", label: "Compliance" },
];

export default function Settings() {
  const location = useLocation();
  const navigate = useNavigate();
  const initialTab = SUBROUTE_TO_TAB[location.pathname] ?? "profile";
  const [tab, setTab] = useState<Tab>(initialTab);
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    const next = SUBROUTE_TO_TAB[location.pathname];
    if (next && next !== tab) setTab(next);
  }, [location.pathname, tab]);

  const selectTab = (t: Tab) => {
    setTab(t);
    navigate(`/settings/${t}`);
  };

  return (
    <>
      <PageHeader
        title="Settings"
        description="Manage your profile, brand voice, and compliance posture."
      />

      <div className="mb-6 flex gap-1 border-b border-border">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => selectTab(t.id)}
            className={cn(
              "border-b-2 px-4 py-2 text-sm font-medium transition-colors",
              tab === t.id
                ? "border-accent text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "profile" && (
        <div className="space-y-6">
          <Card className="p-6">
            <SectionHeader
              title="Your profile"
              hint="These fields come from your account and your Agency assignment."
            />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <ReadOnlyField label="Full name" value={user?.full_name} />
              <ReadOnlyField label="Email" value={user?.email} />
              <ReadOnlyField
                label="Role"
                value={user?.role_label || user?.role}
              />
              <ReadOnlyField
                label="Status"
                value={user?.is_active ? "Active" : "Inactive"}
              />
            </div>
          </Card>

          <Card className="p-6">
            <SectionHeader
              title="Agency assignment"
              hint="Agency-level configuration is managed by your administrator."
            />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <ReadOnlyField label="Agency ID" value={user?.agency_id} />
              <ReadOnlyField label="User ID" value={user?.id} />
            </div>
          </Card>
        </div>
      )}

      {tab === "brand" && <BrandTab />}

      {tab === "compliance" && (
        <Card className="p-6">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold">
                GDPR + CCPA + HIPAA aligned
              </h3>
              <p className="mt-1 text-sm text-muted-foreground">
                This workspace enforces privacy-by-design: PII/PHI is hashed or
                encrypted before warehouse ingestion, 15-minute HIPAA session
                timeout is active, and audit logs are retained for 6 years.
                Contact your administrator to manage BAA status or DSAR
                requests.
              </p>
            </div>
          </div>
        </Card>
      )}
    </>
  );
}

function SectionHeader({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="mb-4">
      <h3 className="text-sm font-semibold">{title}</h3>
      {hint && <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

function ReadOnlyField({
  label,
  value,
}: {
  label: string;
  value?: string | null;
}) {
  return (
    <div>
      <div className="mb-1 flex items-center gap-1.5">
        <Label className="mb-0">{label}</Label>
        <Lock
          className="h-3 w-3 text-muted-foreground"
          aria-label="Read-only"
        />
      </div>
      <div
        className="flex h-9 cursor-not-allowed items-center rounded-lg border border-border bg-muted/50 px-3 text-sm text-muted-foreground"
        title="Read-only"
      >
        {value ?? "—"}
      </div>
    </div>
  );
}

function BrandTab() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<BrandForm>({
    defaultValues: {
      brand_voice: "",
      recommended_tone: "",
      tagline: "",
      industry: "",
    },
  });

  const onSubmit = async (values: BrandForm) => {
    try {
      await api.put("/brands/config", values);
      toast.success("Brand settings saved");
    } catch (err) {
      toast.error("Save failed", { description: extractErrorMessage(err) });
    }
  };

  return (
    <Card className="p-6">
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="grid grid-cols-1 gap-4 sm:grid-cols-2"
      >
        <div>
          <Label htmlFor="brand_voice">Brand voice</Label>
          <Input
            id="brand_voice"
            placeholder="e.g. confident, warm, expert"
            {...register("brand_voice", {
              required: "Brand voice is required",
            })}
            invalid={!!errors.brand_voice}
          />
          <FieldError message={errors.brand_voice?.message} />
        </div>
        <div>
          <Label htmlFor="recommended_tone">Recommended tone</Label>
          <Input
            id="recommended_tone"
            placeholder="e.g. friendly, professional"
            {...register("recommended_tone")}
          />
        </div>
        <div>
          <Label htmlFor="tagline">Tagline</Label>
          <Input
            id="tagline"
            placeholder="Your brand promise in one line"
            {...register("tagline")}
          />
        </div>
        <div>
          <Label htmlFor="industry">Industry</Label>
          <Input
            id="industry"
            placeholder="e.g. healthcare, retail"
            {...register("industry")}
          />
        </div>
        <div className="sm:col-span-2 flex justify-end">
          <Button type="submit" loading={isSubmitting}>
            Save changes
          </Button>
        </div>
      </form>
    </Card>
  );
}
