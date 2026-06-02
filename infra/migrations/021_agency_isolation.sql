-- 021_agency_isolation.sql
-- Adds per-Agency database isolation metadata to the agencies table.
--
-- MVP step: schema-per-Agency on the shared Postgres. Each Agency owns a
-- dedicated schema (db_schema, e.g. tenant_acme) that contains a copy of the
-- agency-owned tables (personas, generations, campaigns, ...). Platform-owned
-- tables (agencies, users, user_invitations, audit_logs) stay in public.
--
-- Forward-compat: db_dsn is reserved for the Phase-2 split where each
-- Agency runs in its own Neon project. A TenantSessionRouter will inspect
-- db_dsn first and fall back to db_schema on the shared cluster.
--
-- See docs/MULTI-TENANT-DB.md for the full design.

ALTER TABLE agencies ADD COLUMN IF NOT EXISTS db_schema TEXT;
ALTER TABLE agencies ADD COLUMN IF NOT EXISTS db_dsn TEXT;

-- Backfill: derive a safe Postgres schema identifier from each agency's slug.
UPDATE agencies
SET db_schema = 'tenant_' || regexp_replace(slug, '[^a-z0-9]', '_', 'g')
WHERE db_schema IS NULL;

ALTER TABLE agencies ALTER COLUMN db_schema SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ix_agencies_db_schema ON agencies (db_schema);
