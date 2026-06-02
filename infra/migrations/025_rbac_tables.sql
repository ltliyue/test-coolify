-- PR 3 of multi-tenant hardening: RBAC permission tables.
-- Permissions are stored at the platform level. Role defaults apply
-- across all agencies; per-agency overrides win.
CREATE TABLE IF NOT EXISTS public.permissions (
  code TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  category TEXT NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS public.role_permissions (
  role user_role NOT NULL,
  permission_code TEXT NOT NULL REFERENCES public.permissions(code) ON DELETE CASCADE,
  granted BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (role, permission_code)
);

CREATE TABLE IF NOT EXISTS public.agency_role_permissions (
  agency_id UUID NOT NULL REFERENCES public.agencies(id) ON DELETE CASCADE,
  role user_role NOT NULL,
  permission_code TEXT NOT NULL REFERENCES public.permissions(code) ON DELETE CASCADE,
  granted BOOLEAN NOT NULL,
  PRIMARY KEY (agency_id, role, permission_code)
);

CREATE INDEX IF NOT EXISTS idx_arp_agency ON public.agency_role_permissions(agency_id);
