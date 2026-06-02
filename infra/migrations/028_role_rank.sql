-- Role hierarchy support. Each role carries an integer rank; users may
-- only manage roles whose rank is STRICTLY LESS than their own. This
-- prevents privilege escalation by toggling permissions on your own
-- (or a superior) role.

ALTER TABLE public.roles ADD COLUMN IF NOT EXISTS rank INTEGER NOT NULL DEFAULT 0;

UPDATE public.roles SET rank = 100 WHERE code = 'platform_super_admin';
UPDATE public.roles SET rank = 90  WHERE code = 'platform_admin';
UPDATE public.roles SET rank = 50  WHERE code = 'agency_admin';
UPDATE public.roles SET rank = 40  WHERE code = 'agency_ops';
UPDATE public.roles SET rank = 10  WHERE code = 'client_viewer';

-- Existing custom roles default to a sensible tier-relative rank
-- (avoid 0 collisions with newly added rows).
UPDATE public.roles SET rank = 85 WHERE tier = 'platform' AND is_system = false AND rank = 0;
UPDATE public.roles SET rank = 35 WHERE tier = 'agency'   AND is_system = false AND rank = 0;
UPDATE public.roles SET rank = 5  WHERE tier = 'client'   AND is_system = false AND rank = 0;
