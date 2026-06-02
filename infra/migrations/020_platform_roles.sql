-- Migration 020: introduce platform-tier roles for 3-tier tenant hierarchy.
-- Adds platform_super_admin / platform_admin to user_role, relaxes users.agency_id
-- and user_invitations.agency_id to NULL (platform users do not belong to an agency),
-- and tracks per-agency suspension state.

ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'platform_super_admin';
ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'platform_admin';

ALTER TABLE users ALTER COLUMN agency_id DROP NOT NULL;
ALTER TABLE user_invitations ALTER COLUMN agency_id DROP NOT NULL;

ALTER TABLE agencies ADD COLUMN IF NOT EXISTS is_suspended BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE agencies ADD COLUMN IF NOT EXISTS suspended_at TIMESTAMPTZ NULL;
ALTER TABLE agencies ADD COLUMN IF NOT EXISTS suspended_reason TEXT NULL;
