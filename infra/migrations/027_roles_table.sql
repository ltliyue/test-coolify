-- PR 4 of multi-tenant hardening: custom role management.
-- Migrates the hardcoded `user_role` enum into a first-class `roles`
-- table so platform_super_admin and agency_admin can define their own
-- role codes alongside the 5 built-ins.

CREATE TABLE IF NOT EXISTS public.roles (
  code TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  tier TEXT NOT NULL CHECK (tier IN ('platform', 'agency', 'client')),
  agency_id UUID NULL REFERENCES public.agencies(id) ON DELETE CASCADE,
  is_system BOOLEAN NOT NULL DEFAULT FALSE,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID NULL REFERENCES public.users(id) ON DELETE SET NULL,
  UNIQUE (code, agency_id)
);
CREATE INDEX IF NOT EXISTS idx_roles_agency ON public.roles(agency_id);

-- Seed the 5 built-in roles. is_system=TRUE blocks rename/delete.
INSERT INTO public.roles (code, label, tier, is_system, description) VALUES
  ('platform_super_admin', 'Platform Super Admin', 'platform', TRUE, 'Built-in: full platform control'),
  ('platform_admin',       'Platform Admin',       'platform', TRUE, 'Built-in: platform ops without permission management'),
  ('agency_admin',         'Agency Admin',         'agency',   TRUE, 'Built-in: full Agency control'),
  ('agency_ops',           'Agency Ops',           'agency',   TRUE, 'Built-in: day-to-day Agency operations'),
  ('client_viewer',        'Client Viewer',        'client',   TRUE, 'Built-in: read-only client portal')
ON CONFLICT DO NOTHING;

-- Cast every existing role column from the user_role enum to plain TEXT
-- so foreign keys to roles.code work and custom role codes can be stored.
ALTER TABLE public.users               ALTER COLUMN role DROP DEFAULT;
ALTER TABLE public.users               ALTER COLUMN role TYPE TEXT USING role::TEXT;
ALTER TABLE public.users               ALTER COLUMN role SET DEFAULT 'agency_ops';
ALTER TABLE public.user_invitations    ALTER COLUMN role TYPE TEXT USING role::TEXT;
ALTER TABLE public.role_permissions    ALTER COLUMN role TYPE TEXT USING role::TEXT;
ALTER TABLE public.agency_role_permissions ALTER COLUMN role TYPE TEXT USING role::TEXT;

-- FKs into the new catalogue (idempotent).
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'users_role_fkey') THEN
    ALTER TABLE public.users ADD CONSTRAINT users_role_fkey FOREIGN KEY (role)
      REFERENCES public.roles(code) ON DELETE RESTRICT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'user_invitations_role_fkey') THEN
    ALTER TABLE public.user_invitations ADD CONSTRAINT user_invitations_role_fkey FOREIGN KEY (role)
      REFERENCES public.roles(code) ON DELETE RESTRICT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'role_permissions_role_fkey') THEN
    ALTER TABLE public.role_permissions ADD CONSTRAINT role_permissions_role_fkey FOREIGN KEY (role)
      REFERENCES public.roles(code) ON DELETE CASCADE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'agency_role_permissions_role_fkey') THEN
    ALTER TABLE public.agency_role_permissions ADD CONSTRAINT agency_role_permissions_role_fkey FOREIGN KEY (role)
      REFERENCES public.roles(code) ON DELETE CASCADE;
  END IF;
END $$;

-- The enum type is now unreferenced; drop it so no code path can
-- accidentally fall back to the closed set.
DROP TYPE IF EXISTS public.user_role;
